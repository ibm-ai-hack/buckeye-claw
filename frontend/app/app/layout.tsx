import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import LeftRail from "@/components/LeftRail";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/");

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0a0a0a" }}>
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
