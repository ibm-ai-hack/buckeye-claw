import GraphBg from "@/components/GraphBg";
import GlassPanel from "@/components/GlassPanel";

export const dynamic = "force-dynamic";

export default function Home() {
  return (
    <div
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: "#0a0a0a",
      }}
    >
      <GraphBg />
      <GlassPanel />
    </div>
  );
}
