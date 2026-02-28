"use client";

import { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  r: number;
  brightness: number;
  vx: number;
  vy: number;
}

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return s / 2147483647;
  };
}

export default function GraphBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;

    let w = 0;
    let h = 0;
    let nodes: Node[] = [];

    const CONNECTION_DIST = 160;
    const NODE_COUNT = 120;
    const DRIFT_SPEED = 0.15;

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      w = window.innerWidth;
      h = window.innerHeight;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      canvas!.style.width = w + "px";
      canvas!.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function initNodes() {
      const rand = seededRandom(42);
      nodes = [];
      for (let i = 0; i < NODE_COUNT; i++) {
        const brightness = rand() < 0.08 ? 0.7 + rand() * 0.3 : 0.15 + rand() * 0.35;
        const r = brightness > 0.6 ? 2 + rand() * 1.5 : 1 + rand() * 1.2;
        nodes.push({
          x: rand() * w,
          y: rand() * h,
          r,
          brightness,
          vx: (rand() - 0.5) * DRIFT_SPEED,
          vy: (rand() - 0.5) * DRIFT_SPEED,
        });
      }
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);

      // edges
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DIST) {
            const alpha = (1 - dist / CONNECTION_DIST) * 0.12;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(180,180,190,${alpha})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      // nodes
      for (const node of nodes) {
        // glow
        if (node.brightness > 0.4) {
          const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.r * 8);
          const isAccent = node.brightness > 0.7;
          const glowColor = isAccent ? "168,50,50" : "180,180,190";
          gradient.addColorStop(0, `rgba(${glowColor},${node.brightness * 0.25})`);
          gradient.addColorStop(1, "rgba(0,0,0,0)");
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.r * 8, 0, Math.PI * 2);
          ctx.fillStyle = gradient;
          ctx.fill();
        }

        // dot
        const isAccent = node.brightness > 0.7;
        const dotColor = isAccent
          ? `rgba(198,60,60,${node.brightness})`
          : `rgba(200,200,210,${node.brightness})`;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
        ctx.fillStyle = dotColor;
        ctx.fill();
      }

      // drift
      for (const node of nodes) {
        node.x += node.vx;
        node.y += node.vy;
        if (node.x < -20) node.x = w + 20;
        if (node.x > w + 20) node.x = -20;
        if (node.y < -20) node.y = h + 20;
        if (node.y > h + 20) node.y = -20;
      }

      animRef.current = requestAnimationFrame(draw);
    }

    resize();
    initNodes();
    draw();

    const onResize = () => {
      resize();
      initNodes();
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(animRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
      }}
    />
  );
}
