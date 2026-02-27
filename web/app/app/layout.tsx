import LeftRail from "@/components/LeftRail";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--color-bg)" }}>
      <LeftRail />
      <main
        style={{
          marginLeft: 80,
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
