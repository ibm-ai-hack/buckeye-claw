import asyncio
import base64
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.agent import BuckeyeLinkAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent: BuckeyeLinkAgent | None = None

STATUS_MESSAGES = {
    "idle": "Not started",
    "awaiting_auth": "Waiting for you to log in...",
    "authenticated": "Logged in! Starting extraction...",
    "extracting": "Reading your schedule...",
    "error": None,
}


def _status_message(a: BuckeyeLinkAgent) -> str:
    if a.status == "complete":
        count = len(a.schedule.get("courses", [])) if a.schedule else 0
        return f"Done! Found {count} courses."
    if a.status == "error":
        return a.error_message or "Unknown error"
    return STATUS_MESSAGES.get(a.status, a.status)


@app.post("/api/session/start")
async def session_start():
    global agent
    if agent is not None:
        logger.info("Closing existing session before starting new one")
        await agent.close()
    agent = BuckeyeLinkAgent()
    await agent.start()
    return {"status": agent.status}


@app.get("/api/session/status")
async def session_status():
    if agent is None:
        return {"status": "idle", "message": "Not started"}
    return {"status": agent.status, "message": _status_message(agent)}


@app.get("/api/session/screenshot")
async def session_screenshot():
    if agent is None or agent.browser is None:
        return Response(status_code=404)
    png = await agent.get_screenshot()
    return Response(content=png, media_type="image/png")


@app.websocket("/api/session/stream")
async def session_stream(ws: WebSocket):
    global agent
    await ws.accept()
    logger.info("WebSocket client connected")

    if agent is None:
        await ws.send_json({"type": "error", "message": "No session started"})
        await ws.close()
        return

    stop_event = asyncio.Event()
    extraction_task: asyncio.Task | None = None

    async def send_frames():
        """Send screenshot frames to the client at ~3 fps."""
        nonlocal extraction_task
        try:
            while not stop_event.is_set():
                # Take screenshot
                try:
                    png = await agent.get_screenshot()
                    image_b64 = base64.b64encode(png).decode("ascii")
                except Exception as e:
                    logger.warning("Screenshot failed: %s", e)
                    image_b64 = ""

                # Poll for auth if still waiting
                if agent.status == "awaiting_auth":
                    await agent.poll_for_auth()

                # If just authenticated, kick off extraction
                if agent.status == "authenticated" and extraction_task is None:
                    logger.info("Auth detected, starting extraction in background")
                    extraction_task = asyncio.create_task(agent.extract_schedule())

                # Send frame
                try:
                    await ws.send_json({
                        "type": "frame",
                        "image": image_b64,
                        "status": agent.status,
                        "message": _status_message(agent),
                    })
                except Exception:
                    stop_event.set()
                    return

                # Check terminal states
                if agent.status == "complete":
                    try:
                        await ws.send_json({
                            "type": "complete",
                            "status": "complete",
                            "schedule": agent.schedule,
                            "message": _status_message(agent),
                        })
                    except Exception:
                        pass
                    stop_event.set()
                    return

                if agent.status == "error":
                    try:
                        await ws.send_json({
                            "type": "error",
                            "message": _status_message(agent),
                        })
                    except Exception:
                        pass
                    stop_event.set()
                    return

                await asyncio.sleep(0.333)
        except Exception as e:
            logger.error("Frame sender error: %s", e)
            stop_event.set()

    async def receive_input():
        """Receive mouse/keyboard input from the client."""
        try:
            while not stop_event.is_set():
                try:
                    data = await asyncio.wait_for(ws.receive_json(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                except WebSocketDisconnect:
                    logger.info("WebSocket client disconnected (receiver)")
                    stop_event.set()
                    return
                except Exception:
                    stop_event.set()
                    return

                msg_type = data.get("type")

                if msg_type == "click":
                    x = float(data.get("x", 0))
                    y = float(data.get("y", 0))
                    await agent.handle_click(x, y)

                elif msg_type == "keypress":
                    key = data.get("key", "")
                    if key:
                        await agent.handle_keyboard(key=key)

                elif msg_type == "type":
                    text = data.get("text", "")
                    if text:
                        await agent.handle_keyboard(text=text)

        except Exception as e:
            logger.error("Input receiver error: %s", e)
            stop_event.set()

    try:
        await asyncio.gather(send_frames(), receive_input())
    except Exception as e:
        logger.error("WebSocket session error: %s", e)
    finally:
        if extraction_task is not None and not extraction_task.done():
            extraction_task.cancel()
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("WebSocket session ended")


@app.post("/api/session/close")
async def session_close():
    global agent
    if agent is not None:
        await agent.close()
        agent = None
    return {"status": "closed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
