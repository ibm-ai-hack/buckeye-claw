"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

// ── Types ────────────────────────────────────────────────────────────────────

interface MemoryFact {
  id: string;
  key: string;
  value: string;
  updated_at: string;
  user_id: string;
}

interface MemoryTask {
  id: string;
  task: string;
  category: string;
  created_at: string;
  user_id: string;
}

interface MemoryJob {
  id: string;
  schedule: string;
  prompt: string;
  task_name: string;
  description: string | null;
  category: string;
  occurrence_count: number;
  created_at: string;
}

interface GraphNode {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
  label: string;
  type: "center" | "category" | "fact" | "task" | "job";
  meta: Record<string, string>;
  pinned?: boolean;
}

interface GraphEdge {
  sourceId: string;
  targetId: string;
  color: string;
}

// ── Constants ────────────────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<string, string> = {
  bus_transit:   "#7c8afe",
  dining_hall:   "#e0a643",
  food_ordering: "#4dcb8a",
  academics:     "#b48afe",
  campus:        "#e8729a",
};

const CENTER_COLOR = "#c24848";
const FACT_COLOR = "#8a8f98";
const JOB_COLOR = "#e8a84c";
const BG = "#181614";

function catColor(cat: string) {
  return CATEGORY_COLORS[cat] ?? "#6b7280";
}

function hexToRgba(hex: string, alpha: number) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── Force simulation ─────────────────────────────────────────────────────────

function simulate(nodes: GraphNode[], edges: GraphEdge[]) {
  const REPULSION = 3000;
  const ATTRACTION = 0.005;
  const DAMPING = 0.85;
  const CENTER_PULL = 0.001;

  const idMap = new Map<string, GraphNode>();
  for (const n of nodes) idMap.set(n.id, n);

  for (const n of nodes) {
    if (n.pinned) continue;
    n.vx *= DAMPING;
    n.vy *= DAMPING;

    for (const other of nodes) {
      if (n.id === other.id) continue;
      const dx = n.x - other.x;
      const dy = n.y - other.y;
      const distSq = dx * dx + dy * dy + 1;
      const force = REPULSION / distSq;
      const dist = Math.sqrt(distSq);
      n.vx += (dx / dist) * force;
      n.vy += (dy / dist) * force;
    }

    n.vx -= n.x * CENTER_PULL;
    n.vy -= n.y * CENTER_PULL;
  }

  for (const e of edges) {
    const s = idMap.get(e.sourceId);
    const t = idMap.get(e.targetId);
    if (!s || !t) continue;
    const dx = t.x - s.x;
    const dy = t.y - s.y;
    const dist = Math.sqrt(dx * dx + dy * dy) + 1;
    const ideal = 100;
    const force = (dist - ideal) * ATTRACTION;
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    if (!s.pinned) { s.vx += fx; s.vy += fy; }
    if (!t.pinned) { t.vx -= fx; t.vy -= fy; }
  }

  for (const n of nodes) {
    if (n.pinned) continue;
    n.x += n.vx;
    n.y += n.vy;
  }
}

// ── Build graph ──────────────────────────────────────────────────────────────

function buildGraph(
  facts: MemoryFact[],
  tasksByCategory: Record<string, MemoryTask[]>,
  jobs: MemoryJob[],
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  nodes.push({
    id: "__center__",
    x: 0, y: 0, vx: 0, vy: 0,
    radius: 20,
    color: CENTER_COLOR,
    label: "you",
    type: "center",
    meta: {},
    pinned: true,
  });

  facts.forEach((f, i) => {
    const angle = (i / Math.max(facts.length, 1)) * Math.PI * 2;
    const dist = 140 + Math.random() * 60;
    nodes.push({
      id: f.id,
      x: Math.cos(angle) * dist, y: Math.sin(angle) * dist,
      vx: 0, vy: 0,
      radius: 7,
      color: FACT_COLOR,
      label: f.key,
      type: "fact",
      meta: { key: f.key, value: f.value },
    });
    edges.push({ sourceId: "__center__", targetId: f.id, color: "#ffffff" });
  });

  const categories = Object.keys(tasksByCategory);
  categories.forEach((cat, ci) => {
    const catId = `cat_${cat}`;
    const angle = (ci / Math.max(categories.length, 1)) * Math.PI * 2;
    const dist = 220 + Math.random() * 40;
    const tasks = tasksByCategory[cat];
    nodes.push({
      id: catId,
      x: Math.cos(angle) * dist, y: Math.sin(angle) * dist,
      vx: 0, vy: 0,
      radius: 7 + Math.min(tasks.length, 8),
      color: catColor(cat),
      label: cat.replace(/_/g, " "),
      type: "category",
      meta: { category: cat, tasks: String(tasks.length) },
    });
    edges.push({ sourceId: "__center__", targetId: catId, color: catColor(cat) });

    tasks.forEach((t, ti) => {
      const tAngle = angle + ((ti - tasks.length / 2) * 0.3);
      const tDist = dist + 90 + Math.random() * 50;
      nodes.push({
        id: t.id,
        x: Math.cos(tAngle) * tDist, y: Math.sin(tAngle) * tDist,
        vx: 0, vy: 0,
        radius: 3.5,
        color: catColor(cat),
        label: t.task.length > 40 ? t.task.slice(0, 37) + "..." : t.task,
        type: "task",
        meta: { task: t.task, category: t.category },
      });
      edges.push({ sourceId: catId, targetId: t.id, color: catColor(cat) });
    });
  });

  jobs.forEach((j, ji) => {
    const catId = `cat_${j.category}`;
    const hasCat = nodes.some((n) => n.id === catId);
    const parentId = hasCat ? catId : "__center__";
    const parent = nodes.find((n) => n.id === parentId)!;
    const angle = (ji / Math.max(jobs.length, 1)) * Math.PI * 2;
    nodes.push({
      id: j.id,
      x: parent.x + Math.cos(angle) * 130, y: parent.y + Math.sin(angle) * 130,
      vx: 0, vy: 0,
      radius: 5.5,
      color: JOB_COLOR,
      label: j.task_name.replace(/_/g, " "),
      type: "job",
      meta: {
        "task name": j.task_name, schedule: j.schedule, prompt: j.prompt,
        description: j.description ?? "—", category: j.category,
        "run count": String(j.occurrence_count),
      },
    });
    edges.push({ sourceId: parentId, targetId: j.id, color: JOB_COLOR });
  });

  return { nodes, edges };
}

// ── Detail modal ─────────────────────────────────────────────────────────────

function DetailModal({ node, onClose }: { node: GraphNode; onClose: () => void }) {
  // Build display fields based on node type so the actual stored content is front and center
  const displayFields: { label: string; value: string; highlight?: boolean }[] = [];

  if (node.type === "fact") {
    displayFields.push(
      { label: "i know that your", value: node.meta.key.replace(/_/g, " "), highlight: true },
      { label: "is", value: node.meta.value, highlight: true },
    );
  } else if (node.type === "task") {
    displayFields.push(
      { label: "you asked", value: node.meta.task, highlight: true },
      { label: "topic", value: node.meta.category.replace(/_/g, " ") },
    );
  } else if (node.type === "job") {
    displayFields.push(
      { label: "routine", value: node.meta.description !== "—" ? node.meta.description : node.meta["task name"].replace(/_/g, " "), highlight: true },
      { label: "i will", value: node.meta.prompt, highlight: true },
      { label: "repeats", value: node.meta.schedule },
      { label: "triggered", value: `${node.meta["run count"]} time${node.meta["run count"] === "1" ? "" : "s"}` },
    );
  } else if (node.type === "category") {
    displayFields.push(
      { label: "topic", value: node.meta.category.replace(/_/g, " "), highlight: true },
      { label: "messages", value: node.meta.tasks },
    );
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 100,
        display: "flex", alignItems: "center", justifyContent: "center",
        background: "rgba(0,0,0,0.6)", backdropFilter: "blur(6px)",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#1c1c20", border: `1px solid ${hexToRgba(node.color, 0.15)}`,
          borderRadius: 14, padding: "28px 32px",
          maxWidth: 480, width: "90%", maxHeight: "80vh", overflowY: "auto",
          fontFamily: "monospace",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
          <div style={{
            width: 10, height: 10, borderRadius: "50%",
            background: node.color, boxShadow: `0 0 8px ${node.color}`, flexShrink: 0,
          }} />
          <span style={{ fontSize: 10, letterSpacing: 2, color: node.color, textTransform: "uppercase" }}>
            {{ fact: "something i remember", task: "something you asked", job: "recurring routine", category: "topic" }[node.type] ?? node.type}
          </span>
          <div style={{ flex: 1 }} />
          <button
            onClick={onClose}
            style={{
              background: "none", border: "none", color: "rgba(255,255,255,0.3)",
              fontSize: 18, cursor: "pointer", padding: "0 4px", lineHeight: 1,
            }}
          >
            &times;
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {displayFields.map(({ label, value, highlight }) => (
            <div key={label}>
              <div style={{
                fontSize: 9, letterSpacing: 1.5, color: "rgba(255,255,255,0.25)",
                textTransform: "uppercase", marginBottom: 4,
              }}>
                {label}
              </div>
              <div style={{
                fontSize: highlight ? 14 : 12,
                color: highlight ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.5)",
                lineHeight: 1.5, wordBreak: "break-word",
                ...(highlight ? { fontFamily: "var(--font-outfit, monospace)" } : {}),
              }}>
                {value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Canvas graph ─────────────────────────────────────────────────────────────

export default function MemoryPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [facts, setFacts] = useState<MemoryFact[]>([]);
  const [tasksByCategory, setTasksByCategory] = useState<Record<string, MemoryTask[]>>({});
  const [jobs, setJobs] = useState<MemoryJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const nodesRef = useRef<GraphNode[]>([]);
  const edgesRef = useRef<GraphEdge[]>([]);
  const animRef = useRef(0);
  const offsetRef = useRef({ x: 0, y: 0 });
  const zoomRef = useRef(1);
  const hoveredRef = useRef<GraphNode | null>(null);
  const sizeRef = useRef({ w: 0, h: 0 });
  const tickRef = useRef(0);
  const dragRef = useRef<{
    active: boolean;
    lastX: number;
    lastY: number;
    node: GraphNode | null;
    didMove: boolean;
  }>({ active: false, lastX: 0, lastY: 0, node: null, didMove: false });

  // ── Data fetch ──────────────────────────────────────────────────────────

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) { setLoading(false); return; }
      const uid = user.id;
      Promise.all([
        supabase.from("memory_facts").select("id, key, value, updated_at, user_id").eq("user_id", uid),
        supabase.from("memory_tasks").select("id, task, category, created_at, user_id")
          .eq("user_id", uid).order("created_at", { ascending: false }).limit(40),
        supabase.from("memory_jobs")
          .select("id, schedule, prompt, task_name, description, category, occurrence_count, created_at")
          .eq("user_id", uid).limit(20),
      ]).then(([factsRes, tasksRes, jobsRes]) => {
        const f = factsRes.data ?? [];
        const t = tasksRes.data ?? [];
        const j = jobsRes.data ?? [];
        setFacts(f);
        setJobs(j);

        const bycat: Record<string, MemoryTask[]> = {};
        for (const task of t) (bycat[task.category] ??= []).push(task);
        setTasksByCategory(bycat);

        const { nodes, edges } = buildGraph(f, bycat, j);
        for (let i = 0; i < 200; i++) simulate(nodes, edges);
        nodesRef.current = nodes;
        edgesRef.current = edges;
        setLoading(false);
      });
    });
  }, []);

  // ── Coordinate helpers ──────────────────────────────────────────────────

  const screenToWorld = useCallback((sx: number, sy: number) => {
    const { w, h } = sizeRef.current;
    return {
      x: (sx - w / 2) / zoomRef.current - offsetRef.current.x,
      y: (sy - h / 2) / zoomRef.current - offsetRef.current.y,
    };
  }, []);

  const findNodeAt = useCallback((wx: number, wy: number): GraphNode | null => {
    const nodes = nodesRef.current;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = wx - n.x;
      const dy = wy - n.y;
      const hit = Math.max(n.radius + 4, 10);
      if (dx * dx + dy * dy < hit * hit) return n;
    }
    return null;
  }, []);

  // ── Render loop ─────────────────────────────────────────────────────────

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || loading) return;
    const ctx = canvas.getContext("2d")!;

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      const w = canvas!.clientWidth;
      const h = canvas!.clientHeight;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      sizeRef.current = { w, h };
    }

    function draw() {
      const { w, h } = sizeRef.current;
      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const z = zoomRef.current;
      const off = offsetRef.current;
      const hovered = hoveredRef.current;

      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = BG;
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      ctx.translate(w / 2, h / 2);
      ctx.scale(z, z);
      ctx.translate(off.x, off.y);

      if (tickRef.current < 600) {
        simulate(nodes, edges);
        tickRef.current++;
      }

      // build id map
      const idMap = new Map<string, GraphNode>();
      for (const n of nodes) idMap.set(n.id, n);

      // hovered connections
      const connectedIds = new Set<string>();
      if (hovered) {
        connectedIds.add(hovered.id);
        for (const e of edges) {
          if (e.sourceId === hovered.id) connectedIds.add(e.targetId);
          if (e.targetId === hovered.id) connectedIds.add(e.sourceId);
        }
      }

      // edges
      for (const e of edges) {
        const s = idMap.get(e.sourceId);
        const t = idMap.get(e.targetId);
        if (!s || !t) continue;
        const highlighted = hovered && (connectedIds.has(s.id) && connectedIds.has(t.id));
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.strokeStyle = highlighted
          ? hexToRgba(e.color, 0.35)
          : hexToRgba(e.color, 0.07);
        ctx.lineWidth = highlighted ? 1.2 : 0.5;
        ctx.stroke();
      }

      // nodes
      for (const n of nodes) {
        const isHovered = hovered?.id === n.id;
        const isConnected = hovered && connectedIds.has(n.id);
        const dimmed = hovered && !isHovered && !isConnected;

        // glow
        if (isHovered || n.type === "center" || n.type === "category") {
          const gr = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.radius * (isHovered ? 5 : 3));
          gr.addColorStop(0, hexToRgba(n.color, isHovered ? 0.3 : 0.12));
          gr.addColorStop(1, hexToRgba(n.color, 0));
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius * (isHovered ? 5 : 3), 0, Math.PI * 2);
          ctx.fillStyle = gr;
          ctx.fill();
        }

        // dot
        ctx.beginPath();
        ctx.arc(n.x, n.y, isHovered ? n.radius * 1.3 : n.radius, 0, Math.PI * 2);
        ctx.fillStyle = dimmed ? hexToRgba(n.color, 0.25) : n.color;
        ctx.fill();

        // always-on labels
        if ((n.type === "category" || n.type === "center") && !isHovered) {
          ctx.font = n.type === "center" ? "bold 11px monospace" : "10px monospace";
          ctx.fillStyle = dimmed ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.4)";
          ctx.textAlign = "center";
          ctx.fillText(n.label, n.x, n.y + n.radius + 14);
        }

        // always-on fact labels: show key = value
        if (n.type === "fact" && !isHovered) {
          const key = n.meta.key?.replace(/_/g, " ") ?? "";
          const val = n.meta.value ?? "";
          const display = val.length > 30 ? val.slice(0, 27) + "..." : val;
          ctx.textAlign = "center";
          ctx.font = "bold 9px monospace";
          ctx.fillStyle = dimmed ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.5)";
          ctx.fillText(key, n.x, n.y + n.radius + 12);
          ctx.font = "9px monospace";
          ctx.fillStyle = dimmed ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.3)";
          ctx.fillText(display, n.x, n.y + n.radius + 23);
        }

        // hover tooltip
        if (isHovered) {
          const lx = n.x;
          let ly = n.y - n.radius - 12;

          ctx.font = "bold 11px monospace";
          ctx.fillStyle = "rgba(255,255,255,0.9)";
          ctx.textAlign = "center";
          ctx.fillText(n.label, lx, ly);
          ly -= 4;

          if (n.type === "fact" && n.meta.value) {
            ly -= 12;
            ctx.font = "10px monospace";
            ctx.fillStyle = "rgba(255,255,255,0.45)";
            const val = n.meta.value.length > 60 ? n.meta.value.slice(0, 57) + "..." : n.meta.value;
            ctx.fillText(val, lx, ly);
          }

          if (n.type === "task" && n.meta.task) {
            ly -= 12;
            ctx.font = "10px monospace";
            ctx.fillStyle = "rgba(255,255,255,0.45)";
            const val = n.meta.task.length > 60 ? n.meta.task.slice(0, 57) + "..." : n.meta.task;
            ctx.fillText(val, lx, ly);
          }

          if (n.type === "job") {
            ly -= 12;
            ctx.font = "10px monospace";
            ctx.fillStyle = "rgba(255,255,255,0.45)";
            ctx.fillText(`${n.meta.schedule} · ${n.meta["run count"]} runs`, lx, ly);
          }

          if (n.type !== "center") {
            ly -= 14;
            ctx.font = "9px monospace";
            ctx.fillStyle = "rgba(255,255,255,0.18)";
            ctx.fillText("click for details", lx, ly);
          }
        }
      }

      ctx.restore();
      animRef.current = requestAnimationFrame(draw);
    }

    resize();
    draw();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animRef.current);
    };
  }, [loading]);

  // ── Mouse interactions ──────────────────────────────────────────────────

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || loading) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const factor = e.deltaY > 0 ? 0.92 : 1.08;
      zoomRef.current = Math.max(0.15, Math.min(5, zoomRef.current * factor));
    };

    const onMouseDown = (e: MouseEvent) => {
      const { x, y } = screenToWorld(e.offsetX, e.offsetY);
      const node = findNodeAt(x, y);
      dragRef.current = {
        active: true,
        lastX: e.offsetX,
        lastY: e.offsetY,
        node: node ?? null,
        didMove: false,
      };
      if (node && node.type !== "center") {
        node.pinned = true;
      }
    };

    const onMouseMove = (e: MouseEvent) => {
      const { x, y } = screenToWorld(e.offsetX, e.offsetY);
      const drag = dragRef.current;

      if (drag.active && drag.node) {
        drag.node.x = x;
        drag.node.y = y;
        drag.node.vx = 0;
        drag.node.vy = 0;
        drag.didMove = true;
        tickRef.current = 0;
      } else if (drag.active) {
        const dx = (e.offsetX - drag.lastX) / zoomRef.current;
        const dy = (e.offsetY - drag.lastY) / zoomRef.current;
        offsetRef.current.x += dx;
        offsetRef.current.y += dy;
        drag.lastX = e.offsetX;
        drag.lastY = e.offsetY;
        drag.didMove = true;
      }

      hoveredRef.current = findNodeAt(x, y);
      canvas.style.cursor = hoveredRef.current
        ? "pointer"
        : drag.active ? "grabbing" : "grab";
    };

    const onMouseUp = () => {
      const drag = dragRef.current;
      if (drag.node && drag.node.type !== "center") {
        drag.node.pinned = false;
        tickRef.current = 0;
      }
      // click = mousedown + mouseup without significant movement
      if (!drag.didMove && drag.node && drag.node.type !== "center") {
        setSelectedNode({ ...drag.node });
      }
      dragRef.current = { active: false, lastX: 0, lastY: 0, node: null, didMove: false };
    };

    const onMouseLeave = () => {
      hoveredRef.current = null;
      const drag = dragRef.current;
      if (drag.node && drag.node.type !== "center") drag.node.pinned = false;
      dragRef.current = { active: false, lastX: 0, lastY: 0, node: null, didMove: false };
    };

    canvas.addEventListener("wheel", onWheel, { passive: false });
    canvas.addEventListener("mousedown", onMouseDown);
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseup", onMouseUp);
    canvas.addEventListener("mouseleave", onMouseLeave);
    return () => {
      canvas.removeEventListener("wheel", onWheel);
      canvas.removeEventListener("mousedown", onMouseDown);
      canvas.removeEventListener("mousemove", onMouseMove);
      canvas.removeEventListener("mouseup", onMouseUp);
      canvas.removeEventListener("mouseleave", onMouseLeave);
    };
  }, [loading, screenToWorld, findNodeAt]);

  const categories = Object.keys(tasksByCategory);
  const totalTasks = Object.values(tasksByCategory).flat().length;

  return (
    <div style={{ width: "100%", height: "100vh", background: BG, position: "relative", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ position: "absolute", top: 32, left: 32, zIndex: 10, pointerEvents: "none" }}>
        <h2 style={{
          fontFamily: "var(--font-jakarta)", fontWeight: 200, fontSize: 26,
          letterSpacing: "0.28em", color: "rgba(255,255,255,0.85)", margin: 0, textTransform: "lowercase",
        }}>
          memory
        </h2>
        {!loading && (
          <p style={{
            fontFamily: "var(--font-jakarta)", fontSize: 10, letterSpacing: "2px",
            color: "rgba(255,255,255,0.2)", margin: "6px 0 0",
          }}>
            {facts.length} facts · {totalTasks} tasks · {jobs.length} jobs
          </p>
        )}
      </div>

      {/* Legend */}
      {!loading && (
        <div style={{
          position: "absolute", bottom: 32, right: 32, zIndex: 10,
          display: "flex", flexDirection: "column", gap: 10, pointerEvents: "none",
        }}>
          {[
            { color: CENTER_COLOR, label: "you" },
            { color: FACT_COLOR, label: "facts" },
            { color: JOB_COLOR, label: "jobs" },
            ...categories.map((c) => ({ color: catColor(c), label: c.replace(/_/g, " ") })),
          ].map(({ color, label }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 6, height: 6, borderRadius: "50%", background: color,
                boxShadow: `0 0 6px ${color}`, flexShrink: 0,
              }} />
              <span style={{
                fontFamily: "var(--font-jakarta)", fontSize: 10,
                letterSpacing: "1.5px", color: "rgba(255,255,255,0.28)",
              }}>
                {label}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Hint */}
      <div style={{ position: "absolute", bottom: 32, left: 32, zIndex: 10, pointerEvents: "none" }}>
        <p style={{
          fontFamily: "var(--font-jakarta)", fontSize: 10, letterSpacing: "1.5px",
          color: "rgba(255,255,255,0.12)", margin: 0,
        }}>
          drag to pan · scroll to zoom · drag nodes · click for details
        </p>
      </div>

      {loading ? (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{
            fontFamily: "var(--font-jakarta)", fontSize: 11, letterSpacing: "3px", color: "rgba(255,255,255,0.18)",
          }}>
            loading memory...
          </span>
        </div>
      ) : (
        <canvas ref={canvasRef} style={{ width: "100%", height: "100%", cursor: "grab" }} />
      )}

      {selectedNode && selectedNode.type !== "center" && (
        <DetailModal node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
}
