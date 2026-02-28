import { createServerClient } from "@supabase/ssr";
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";

const CANVAS_BASE = "https://osu.instructure.com";

/** Service-role client for server-side DB queries (bypasses RLS). */
function createServiceClient() {
  return createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
  );
}

/** Session-aware client used only to identify the logged-in user. */
async function createSessionClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: () => {},
      },
    },
  );
}

/**
 * Resolve the Canvas personal access token for the currently logged-in user.
 * Returns null if the user is not authenticated or has no token saved.
 */
export async function getCanvasToken(): Promise<string | null> {
  const session = await createSessionClient();
  const {
    data: { user },
  } = await session.auth.getUser();
  if (!user) return null;

  const db = createServiceClient();

  const { data: profile } = await db
    .from("profiles")
    .select("id")
    .eq("auth_id", user.id)
    .single();
  if (!profile) return null;

  const { data: integration } = await db
    .from("user_integrations")
    .select("canvas_token")
    .eq("user_id", profile.id)
    .not("canvas_token", "is", null)
    .maybeSingle();

  return integration?.canvas_token ?? null;
}

/** Fetch from the Canvas REST API with the user's token. */
export function canvasFetch(path: string, token: string) {
  return fetch(`${CANVAS_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
}

/** Urgency label + category matching the Flask api.py logic. */
export function computeUrgency(
  dueMs: number,
  nowMs: number,
): { dueLabel: string; urgency: "overdue" | "tomorrow" | "soon" | "normal" } {
  const diffMs = dueMs - nowMs;
  const hours = diffMs / 3_600_000;

  if (hours < 0) {
    const abs = Math.abs(hours);
    return {
      dueLabel: abs < 24 ? `overdue ${Math.floor(abs)}h` : `overdue ${Math.floor(abs / 24)}d`,
      urgency: "overdue",
    };
  }
  if (hours <= 24) return { dueLabel: "due tomorrow", urgency: "tomorrow" };
  if (hours <= 48)
    return { dueLabel: `due in 1d ${Math.floor(hours % 24)}h`, urgency: "soon" };
  if (hours <= 72)
    return { dueLabel: `due in 2d ${Math.floor(hours % 24)}h`, urgency: "soon" };

  const days = Math.floor(hours / 24);
  const remH = Math.floor(hours % 24);
  return {
    dueLabel: days < 7 && remH > 0 ? `due in ${days}d ${remH}h` : `due in ${days}d`,
    urgency: "normal",
  };
}

export const URGENCY_ORDER: Record<string, number> = {
  overdue: 0,
  tomorrow: 1,
  soon: 2,
  normal: 3,
};
