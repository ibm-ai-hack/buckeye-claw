"""
Local Grubhub server — exposes Appium automation as HTTP endpoints.

Run this on a machine with Android emulator + Appium installed.
Tunnel to the internet via ngrok so the cloud-hosted BuckeyeClaw app
can call these endpoints.

    python grubhub_server.py          # starts on GRUBHUB_SERVER_PORT (default 8000)
    ngrok http 8000                   # tunnel to public URL
"""

import asyncio
import logging
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="BuckeyeClaw Grubhub Server")

# Serialize Appium operations — only one emulator session at a time
_appium_lock = asyncio.Lock()


# ── Auth ──────────────────────────────────────────────────────────────


async def verify_api_key(x_grubhub_server_key: str = Header(...)) -> None:
    expected = os.environ.get("GRUBHUB_SERVER_KEY", "")
    if not expected or x_grubhub_server_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── Request / response models ─────────────────────────────────────────


class SearchRequest(BaseModel):
    query: str


class MenuRequest(BaseModel):
    restaurant_name: str


class OrderRequest(BaseModel):
    restaurant_name: str
    items: str


class ScheduleRequest(BaseModel):
    restaurant_name: str
    items: str
    time_description: str
    from_number: str


def _ok(data: dict | list | None = None) -> dict:
    return {"success": True, "data": data, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "data": None, "error": msg}


# ── Endpoints ─────────────────────────────────────────────────────────


@app.get("/api/grubhub/health")
async def health():
    from backend.integrations.grubhub.emulator import (
        is_emulator_running,
        is_grubhub_installed,
    )

    emu = is_emulator_running()
    grubhub = is_grubhub_installed() if emu else False

    # Quick check if Appium is reachable
    import httpx

    appium_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get("http://localhost:4723/status")
            appium_ok = resp.status_code == 200
    except Exception:
        pass

    healthy = emu and grubhub and appium_ok
    return {
        "healthy": healthy,
        "emulator": emu,
        "grubhub_installed": grubhub,
        "appium": appium_ok,
    }


@app.post("/api/grubhub/search", dependencies=[Depends(verify_api_key)])
async def search(req: SearchRequest):
    from backend.integrations.grubhub.automation import get_driver, search_restaurants

    async with _appium_lock:
        try:
            driver = get_driver()
            results = search_restaurants(driver, req.query)
            driver.quit()
            return _ok({"restaurants": results})
        except Exception as e:
            logger.exception("Search failed")
            return _err(str(e))


@app.post("/api/grubhub/menu", dependencies=[Depends(verify_api_key)])
async def menu(req: MenuRequest):
    from backend.integrations.grubhub.automation import (
        get_driver,
        search_restaurants,
        select_restaurant,
    )

    async with _appium_lock:
        try:
            driver = get_driver()
            results = search_restaurants(driver, req.restaurant_name)
            if not results:
                driver.quit()
                return _ok({"menu": []})
            menu_items = select_restaurant(driver, req.restaurant_name, results)
            driver.quit()
            return _ok({"menu": menu_items})
        except Exception as e:
            logger.exception("Menu failed")
            return _err(str(e))


@app.post("/api/grubhub/order", dependencies=[Depends(verify_api_key)])
async def order(req: OrderRequest):
    from backend.integrations.grubhub.automation import get_driver, intelligent_order

    async with _appium_lock:
        try:
            driver = get_driver()
            result = intelligent_order(driver, req.restaurant_name, req.items)
            driver.quit()
            return _ok(result)
        except Exception as e:
            logger.exception("Order failed")
            return _err(str(e))


@app.post("/api/grubhub/schedule", dependencies=[Depends(verify_api_key)])
async def schedule(req: ScheduleRequest):
    from backend.integrations.grubhub.scheduler import parse_time, schedule_order

    try:
        run_at = parse_time(req.time_description)
        job_id = schedule_order(
            req.restaurant_name, req.items, run_at, req.from_number
        )
        return _ok({
            "job_id": job_id,
            "run_at": run_at.strftime("%I:%M %p on %b %d"),
        })
    except ValueError as e:
        return _err(f"Could not parse time: {e}")
    except Exception as e:
        logger.exception("Schedule failed")
        return _err(str(e))


@app.get("/api/grubhub/scheduled", dependencies=[Depends(verify_api_key)])
async def list_scheduled(from_number: str = Query(...)):
    from backend.integrations.grubhub.scheduler import get_scheduled_orders

    orders = get_scheduled_orders(from_number)
    return _ok({"orders": orders})


@app.delete("/api/grubhub/scheduled/{job_id}", dependencies=[Depends(verify_api_key)])
async def cancel_scheduled(job_id: str):
    from backend.integrations.grubhub.scheduler import cancel_order

    if cancel_order(job_id):
        return _ok({"cancelled": job_id})
    return _err(f"No scheduled order found with ID {job_id}")
