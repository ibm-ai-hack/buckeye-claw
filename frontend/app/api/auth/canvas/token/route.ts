import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { createClient as createSessionClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  const { token } = await request.json();

  if (!token || typeof token !== "string" || !token.trim()) {
    return NextResponse.json({ error: "Token is required" }, { status: 400 });
  }

  // Validate the token against Canvas
  const canvasUrl = process.env.CANVAS_URL ?? "https://osu.instructure.com";
  const verifyRes = await fetch(`${canvasUrl}/api/v1/users/self`, {
    headers: { Authorization: `Bearer ${token.trim()}` },
  });

  if (!verifyRes.ok) {
    return NextResponse.json({ error: "Invalid Canvas token — make sure you copied it correctly" }, { status: 401 });
  }

  // Get the authenticated user from session
  const sessionClient = await createSessionClient();
  const { data: { user } } = await sessionClient.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const adminClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  const { data: profile } = await adminClient
    .from("profiles")
    .select("id")
    .eq("auth_id", user.id)
    .single();

  if (!profile) {
    return NextResponse.json({ error: "Profile not found" }, { status: 404 });
  }

  await adminClient.from("user_integrations").upsert(
    {
      user_id: profile.id,
      canvas_token: token.trim(),
      canvas_connected_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" }
  );

  return NextResponse.json({ ok: true });
}
