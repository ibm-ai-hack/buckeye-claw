"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";
import { createClient } from "@/lib/supabase/client";

// ── Types ────────────────────────────────────────────────────────────────────

interface MemoryFact { key: string; value: string }
interface MemoryTask { task: string; category: string }

// ── Constants ────────────────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<string, string> = {
  bus_transit:   "#60a5fa",
  dining_hall:   "#fbbf24",
  food_ordering: "#34d399",
  academics:     "#a78bfa",
  campus:        "#f472b6",
};

const CATEGORY_POSITIONS: Record<string, [number, number, number]> = {
  bus_transit:   [-5.8,  1.2,  2.0],
  dining_hall:   [ 5.2, -0.8, -3.5],
  food_ordering: [ 2.0,  3.5, -5.5],
  academics:     [-3.0, -2.5, -5.0],
  campus:        [ 1.0, -4.0,  3.5],
};

function categoryColor(cat: string) {
  return CATEGORY_COLORS[cat] ?? "#94a3b8";
}

// ── Geometry helpers ─────────────────────────────────────────────────────────

function fibonacciSphere(n: number, r: number): [number, number, number][] {
  const phi = (1 + Math.sqrt(5)) / 2;
  return Array.from({ length: n }, (_, i) => {
    const t = Math.acos(1 - 2 * (i + 0.5) / n);
    const p = 2 * Math.PI * i / phi;
    return [r * Math.sin(t) * Math.cos(p), r * Math.sin(t) * Math.sin(p), r * Math.cos(t)];
  });
}

function clusterAround(
  center: [number, number, number],
  n: number,
  r: number,
): [number, number, number][] {
  if (n === 0) return [];
  if (n === 1) return [[center[0], center[1] + r * 0.5, center[2]]];
  return fibonacciSphere(n, r).map(([x, y, z]) => [center[0] + x, center[1] + y, center[2] + z]);
}

// ── Tooltip card ─────────────────────────────────────────────────────────────

function Tooltip({
  title,
  body,
  accent = "rgba(255,255,255,0.12)",
}: {
  title: string;
  body: string;
  accent?: string;
}) {
  return (
    <div
      style={{
        background: "rgba(6,6,6,0.92)",
        border: `1px solid ${accent}`,
        borderRadius: 10,
        padding: "10px 14px",
        fontFamily: "monospace",
        fontSize: 11,
        whiteSpace: "nowrap",
        pointerEvents: "none",
        backdropFilter: "blur(12px)",
        maxWidth: 220,
        lineHeight: 1.5,
      }}
    >
      <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 10, marginBottom: 4, letterSpacing: 1 }}>
        {title}
      </div>
      <div style={{ color: "rgba(255,255,255,0.82)", whiteSpace: "normal" }}>{body}</div>
    </div>
  );
}

// ── Central node (you) ───────────────────────────────────────────────────────

function CentralNode() {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(() => {
    if (!ref.current) return;
    const s = 1 + 0.06 * Math.sin(performance.now() * 0.002);
    ref.current.scale.setScalar(s);
  });
  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.48, 48, 48]} />
      <meshStandardMaterial
        color="#c62828"
        emissive="#c62828"
        emissiveIntensity={3.5}
        roughness={0.08}
        metalness={0.9}
      />
    </mesh>
  );
}

// ── Fact node ────────────────────────────────────────────────────────────────

function FactNode({
  pos,
  label,
  value,
  idx,
}: {
  pos: [number, number, number];
  label: string;
  value: string;
  idx: number;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);

  useFrame(() => {
    if (!groupRef.current) return;
    const t = performance.now() * 0.001 + idx * 0.9;
    groupRef.current.position.set(pos[0], pos[1] + Math.sin(t * 0.55) * 0.22, pos[2]);
  });

  return (
    <group ref={groupRef} position={pos}>
      <mesh
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[hovered ? 0.23 : 0.16, 24, 24]} />
        <meshStandardMaterial
          color="white"
          emissive="white"
          emissiveIntensity={hovered ? 1.4 : 0.38}
          roughness={0.2}
          metalness={0.7}
        />
      </mesh>
      {hovered && (
        <Html center distanceFactor={10} zIndexRange={[100, 0]}>
          <Tooltip title={label} body={value} />
        </Html>
      )}
    </group>
  );
}

// ── Category node (octahedron) ───────────────────────────────────────────────

function CategoryNode({
  pos,
  category,
  count,
}: {
  pos: [number, number, number];
  category: string;
  count: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const color = categoryColor(category);

  useFrame((_, dt) => {
    if (!ref.current) return;
    ref.current.rotation.y += dt * 0.9;
    ref.current.rotation.x += dt * 0.35;
  });

  return (
    <mesh
      ref={ref}
      position={pos}
      onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
      onPointerOut={() => setHovered(false)}
    >
      <octahedronGeometry args={[hovered ? 0.38 : 0.3, 0]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={hovered ? 2.5 : 1.1}
        roughness={0.08}
        metalness={0.95}
      />
      {hovered && (
        <Html center distanceFactor={10} zIndexRange={[100, 0]}>
          <Tooltip
            title={category.replace(/_/g, " ")}
            body={`${count} task${count !== 1 ? "s" : ""}`}
            accent={`${color}50`}
          />
        </Html>
      )}
    </mesh>
  );
}

// ── Task node ────────────────────────────────────────────────────────────────

function TaskNode({
  pos,
  task,
  category,
  idx,
}: {
  pos: [number, number, number];
  task: string;
  category: string;
  idx: number;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);
  const color = categoryColor(category);

  useFrame(() => {
    if (!groupRef.current) return;
    const t = performance.now() * 0.001 + idx * 1.7;
    groupRef.current.position.set(pos[0], pos[1] + Math.sin(t * 0.7) * 0.1, pos[2]);
  });

  return (
    <group ref={groupRef} position={pos}>
      <mesh
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[hovered ? 0.14 : 0.09, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={hovered ? 2 : 0.55}
          roughness={0.3}
          metalness={0.6}
          transparent
          opacity={hovered ? 1 : 0.78}
        />
      </mesh>
      {hovered && (
        <Html center distanceFactor={10} zIndexRange={[100, 0]}>
          <Tooltip title={category.replace(/_/g, " ")} body={task} accent={`${color}40`} />
        </Html>
      )}
    </group>
  );
}

// ── Edges (all drawn as one LineSegments call) ───────────────────────────────

interface EdgeDef {
  from: [number, number, number];
  to: [number, number, number];
  color: string;
  opacity: number;
}

function EdgeGroup({ edges, color, opacity }: { edges: EdgeDef[]; color: string; opacity: number }) {
  const geo = useMemo(() => {
    const pts: number[] = [];
    edges.forEach(({ from, to }) => pts.push(...from, ...to));
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pts), 3));
    return g;
  }, [edges]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <lineSegments geometry={geo}>
      <lineBasicMaterial color={color} transparent opacity={opacity} />
    </lineSegments>
  );
}

function Edges({ connections }: { connections: EdgeDef[] }) {
  // Group by color to minimize draw calls
  const byColor = useMemo(() => {
    const map = new Map<string, EdgeDef[]>();
    connections.forEach((e) => {
      const key = `${e.color}:${e.opacity}`;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(e);
    });
    return Array.from(map.entries()).map(([key, edges]) => {
      const [color, opacity] = key.split(":");
      return { color, opacity: parseFloat(opacity), edges };
    });
  }, [connections]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      {byColor.map(({ color, opacity, edges }, i) => (
        <EdgeGroup key={i} edges={edges} color={color} opacity={opacity} />
      ))}
    </>
  );
}

// ── Ambient dust particles ───────────────────────────────────────────────────

function Dust() {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(500 * 3);
    for (let i = 0; i < arr.length; i++) arr[i] = (Math.random() - 0.5) * 38;
    return arr;
  }, []);

  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * 0.012;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.045} color="white" transparent opacity={0.18} sizeAttenuation />
    </points>
  );
}

// ── Full scene ───────────────────────────────────────────────────────────────

function Scene({
  facts,
  tasksByCategory,
}: {
  facts: MemoryFact[];
  tasksByCategory: Record<string, MemoryTask[]>;
}) {
  const groupRef = useRef<THREE.Group>(null);
  useFrame((_, dt) => {
    if (groupRef.current) groupRef.current.rotation.y += dt * 0.05;
  });

  const categories = Object.keys(tasksByCategory);

  const factPositions = useMemo(
    () => fibonacciSphere(Math.max(facts.length, 1), 3.6).slice(0, facts.length) as [number, number, number][],
    [facts.length],
  );

  const catPositions = useMemo(() => {
    const result: Record<string, [number, number, number]> = {};
    categories.forEach((cat, i) => {
      if (CATEGORY_POSITIONS[cat]) {
        result[cat] = CATEGORY_POSITIONS[cat];
      } else {
        const angle = (i / categories.length) * Math.PI * 2;
        result[cat] = [Math.cos(angle) * 6.2, (i % 2 === 0 ? 1 : -1) * 1.5, Math.sin(angle) * 6.2];
      }
    });
    return result;
  }, [categories.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  // Precompute task positions per category
  const taskPositions = useMemo(() => {
    const result: Record<string, [number, number, number][]> = {};
    categories.forEach((cat) => {
      const pos = catPositions[cat];
      if (pos) result[cat] = clusterAround(pos, tasksByCategory[cat].length, 1.55);
    });
    return result;
  }, [catPositions, tasksByCategory]); // eslint-disable-line react-hooks/exhaustive-deps

  // All edges in one flat array
  const connections = useMemo<EdgeDef[]>(() => {
    const edges: EdgeDef[] = [];
    // User → facts
    factPositions.forEach((p) => {
      edges.push({ from: [0, 0, 0], to: p, color: "#ffffff", opacity: 0.05 });
    });
    // User → categories + category → tasks
    categories.forEach((cat) => {
      const cp = catPositions[cat];
      if (!cp) return;
      const color = categoryColor(cat);
      edges.push({ from: [0, 0, 0], to: cp, color, opacity: 0.18 });
      (taskPositions[cat] ?? []).forEach((tp) => {
        edges.push({ from: cp, to: tp, color, opacity: 0.09 });
      });
    });
    return edges;
  }, [factPositions, catPositions, taskPositions, categories.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <group ref={groupRef}>
      <CentralNode />

      {facts.map((f, i) => (
        <FactNode key={f.key} pos={factPositions[i]} label={f.key} value={f.value} idx={i} />
      ))}

      {categories.map((cat) => {
        const cp = catPositions[cat];
        if (!cp) return null;
        const tasks = tasksByCategory[cat];
        const tps = taskPositions[cat] ?? [];
        return (
          <group key={cat}>
            <CategoryNode pos={cp} category={cat} count={tasks.length} />
            {tasks.map((t, j) => (
              <TaskNode key={j} pos={tps[j] ?? cp} task={t.task} category={cat} idx={j} />
            ))}
          </group>
        );
      })}

      <Edges connections={connections} />
      <Dust />
    </group>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function MemoryPage() {
  const [facts, setFacts] = useState<MemoryFact[]>([]);
  const [tasksByCategory, setTasksByCategory] = useState<Record<string, MemoryTask[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();
    Promise.all([
      supabase.from("memory_facts").select("key, value"),
      supabase
        .from("memory_tasks")
        .select("task, category")
        .order("created_at", { ascending: false })
        .limit(40),
    ]).then(([factsRes, tasksRes]) => {
      if (factsRes.data) setFacts(factsRes.data);
      if (tasksRes.data) {
        const bycat: Record<string, MemoryTask[]> = {};
        for (const t of tasksRes.data) {
          (bycat[t.category] ??= []).push(t);
        }
        setTasksByCategory(bycat);
      }
      setLoading(false);
    });
  }, []);

  const categories = Object.keys(tasksByCategory);
  const totalTasks = Object.values(tasksByCategory).flat().length;

  return (
    <div
      style={{
        width: "100%",
        height: "100vh",
        background: "#0a0a0a",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          position: "absolute",
          top: 32,
          left: 32,
          zIndex: 10,
          pointerEvents: "none",
        }}
      >
        <h2
          style={{
            fontFamily: "var(--font-outfit)",
            fontWeight: 200,
            fontSize: 26,
            letterSpacing: "0.28em",
            color: "rgba(255,255,255,0.85)",
            margin: 0,
            textTransform: "lowercase",
          }}
        >
          memory
        </h2>
        {!loading && (
          <p
            style={{
              fontFamily: "var(--font-space-mono)",
              fontSize: 10,
              letterSpacing: "2px",
              color: "rgba(255,255,255,0.2)",
              margin: "6px 0 0",
            }}
          >
            {facts.length} facts · {totalTasks} tasks
          </p>
        )}
      </div>

      {/* Legend */}
      {!loading && (
        <div
          style={{
            position: "absolute",
            bottom: 32,
            right: 32,
            zIndex: 10,
            display: "flex",
            flexDirection: "column",
            gap: 10,
            pointerEvents: "none",
          }}
        >
          {[
            { color: "#c62828", label: "you" },
            { color: "rgba(255,255,255,0.7)", label: "facts" },
            ...categories.map((c) => ({ color: categoryColor(c), label: c.replace(/_/g, " ") })),
          ].map(({ color, label }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: color,
                  boxShadow: `0 0 7px ${color}`,
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontSize: 10,
                  letterSpacing: "1.5px",
                  color: "rgba(255,255,255,0.28)",
                }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Hint */}
      <div
        style={{
          position: "absolute",
          bottom: 32,
          left: 32,
          zIndex: 10,
          pointerEvents: "none",
        }}
      >
        <p
          style={{
            fontFamily: "var(--font-space-mono)",
            fontSize: 10,
            letterSpacing: "1.5px",
            color: "rgba(255,255,255,0.12)",
            margin: 0,
          }}
        >
          drag to orbit · scroll to zoom · hover nodes
        </p>
      </div>

      {loading ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-space-mono)",
              fontSize: 11,
              letterSpacing: "3px",
              color: "rgba(255,255,255,0.18)",
            }}
          >
            loading memory...
          </span>
        </div>
      ) : (
        <Canvas
          camera={{ position: [0, 3, 15], fov: 50 }}
          gl={{ antialias: true, alpha: false }}
          style={{ background: "#0a0a0a" }}
        >
          <color attach="background" args={["#0a0a0a"]} />
          <ambientLight intensity={0.2} />
          <pointLight position={[6, 10, 8]} intensity={0.5} />
          <pointLight position={[-8, -6, -5]} intensity={0.3} color="#c62828" />

          <Suspense fallback={null}>
            <Scene facts={facts} tasksByCategory={tasksByCategory} />
            <EffectComposer>
              <Bloom
                intensity={1.5}
                luminanceThreshold={0.22}
                luminanceSmoothing={0.88}
                mipmapBlur
              />
            </EffectComposer>
          </Suspense>

          <OrbitControls
            enablePan={false}
            enableZoom
            minDistance={5}
            maxDistance={30}
            makeDefault
          />
        </Canvas>
      )}
    </div>
  );
}
