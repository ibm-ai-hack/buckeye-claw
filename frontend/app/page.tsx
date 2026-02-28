import Dither from "@/components/Dither";
import GlassPanel from "@/components/GlassPanel";

export default function Home() {
  return (
    <div className="relative h-screen w-screen overflow-hidden bg-[#666666]">
      <Dither
        waveColor={[0.75, 0.0, 0.07]}
        baseColor={[0.22, 0.22, 0.22]}
        waveSpeed={0.05}
        waveFrequency={2}
        waveAmplitude={0.45}
        colorNum={5}
        pixelSize={1.5}
        enableMouseInteraction={true}
        mouseRadius={0.6}
      />
      <GlassPanel />
    </div>
  );
}
