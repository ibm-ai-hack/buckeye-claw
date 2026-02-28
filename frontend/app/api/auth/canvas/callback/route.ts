import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { createClient as createSessionClient } from "@/lib/supabase/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const error = searchParams.get("error");

  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://buckeyeclaw.vercel.app";

  if (error || !code) {
    return NextResponse.redirect(`${appUrl}/app/connect?error=canvas_denied`);
  }

  // Exchange code for access token
  const canvasUrl = process.env.CANVAS_URL ?? "https://osu.instructure.com";
  const redirectUri = `${appUrl}/api/auth/canvas/callback`;

  let accessToken: string;
  try {
    const tokenRes = await fetch(`${canvasUrl}/login/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        grant_type: "authorization_code",
        client_id: process.env.CANVAS_CLIENT_ID,
        client_secret: process.env.CANVAS_CLIENT_SECRET,
        redirect_uri: redirectUri,
        code,
      }),
    });
    if (!tokenRes.ok) {
      throw new Error(`Token exchange failed: ${tokenRes.status}`);
    }
    const data = await tokenRes.json();
    accessToken = data.access_token;
  } catch {
    return NextResponse.redirect(`${appUrl}/app/connect?error=token_exchange`);
  }

  // Get authenticated user from session
  const sessionClient = await createSessionClient();
  const {
    data: { user },
  } = await sessionClient.auth.getUser();

  if (!user) {
    return NextResponse.redirect(`${appUrl}/?error=not_authenticated`);
  }

  // Use service-role client to bypass RLS
  const adminClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  // Look up profile by auth_id
  const { data: profile } = await adminClient
    .from("profiles")
    .select("id")
    .eq("auth_id", user.id)
    .single();

  if (!profile) {
    return NextResponse.redirect(`${appUrl}/app/connect?error=no_profile`);
  }

  // Upsert canvas token
  await adminClient.from("user_integrations").upsert(
    {
      user_id: profile.id,
      canvas_token: accessToken,
      canvas_connected_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" }
  );

  return NextResponse.redirect(`${appUrl}/app/connect?success=canvas`);
}
