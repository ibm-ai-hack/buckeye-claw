import LeftRail from "@/components/LeftRail";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0a0a0a" }}>
      <LeftRail />
      <main
        style={{
          marginLeft: 64,
          flex: 1,
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          position: "relative",
        }}
      >
        {children}
      </main>
    </div>
  );
}
