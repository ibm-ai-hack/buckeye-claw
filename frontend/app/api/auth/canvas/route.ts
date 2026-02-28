import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://buckeyeclaw.vercel.app";

  if (!user) {
    return NextResponse.redirect(`${appUrl}/`);
  }

  const clientId = process.env.CANVAS_CLIENT_ID;
  if (!clientId) {
    return NextResponse.redirect(`${appUrl}/app/connect?error=not_configured`);
  }

  const canvasUrl =
    process.env.CANVAS_URL ?? "https://osu.instructure.com";
  const redirectUri = `${appUrl}/api/auth/canvas/callback`;

  const authUrl = new URL(`${canvasUrl}/login/oauth2/auth`);
  authUrl.searchParams.set("client_id", clientId);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("redirect_uri", redirectUri);
  authUrl.searchParams.set("state", user.id);

  return NextResponse.redirect(authUrl.toString());
}
