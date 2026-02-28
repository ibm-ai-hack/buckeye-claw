"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { createClient } from "./client";
import type { RealtimeChannel } from "@supabase/supabase-js";

// ── useUserPhone ─────────────────────────────────────────

export function useUserPhone() {
  const [phone, setPhone] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) {
        setLoading(false);
        return;
      }
      supabase
        .from("profiles")
        .select("phone")
        .eq("id", user.id)
        .maybeSingle()
        .then(({ data }) => {
          if (data?.phone) setPhone(data.phone);
          setLoading(false);
        });
    });
  }, []);

  return { phone, loading };
}

// ── Types ────────────────────────────────────────────────

export interface Message {
  id: string;
  phone: string;
  role: "user" | "agent";
  text: string;
  run_id: string | null;
  created_at: string;
}

export interface AgentRun {
  id: string;
  phone: string;
  status: "running" | "completed" | "error";
  intent: string | null;
  user_message: string | null;
  final_response: string | null;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface AgentEvent {
  id: string;
  run_id: string;
  event_type: string;
  step: string | null;
  tool_name: string | null;
  tool_args: Record<string, unknown> | null;
  tool_result: Record<string, unknown> | null;
  duration_ms: number | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

// ── useMessages ──────────────────────────────────────────

export function useMessages(phone: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const channelRef = useRef<RealtimeChannel | null>(null);

  useEffect(() => {
    if (!phone) return;
    const supabase = createClient();

    // Initial fetch
    supabase
      .from("messages")
      .select("*")
      .eq("phone", phone)
      .order("created_at", { ascending: true })
      .limit(200)
      .then(({ data }) => {
        if (data) setMessages(data as Message[]);
      });

    // Subscribe to inserts
    channelRef.current = supabase
      .channel(`messages:${phone}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
          filter: `phone=eq.${phone}`,
        },
        (payload) => {
          setMessages((prev) => [...prev, payload.new as Message]);
        }
      )
      .subscribe();

    return () => {
      channelRef.current?.unsubscribe();
    };
  }, [phone]);

  return messages;
}

// ── useAgentRuns ─────────────────────────────────────────

export function useAgentRuns(phone: string | null) {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const channelRef = useRef<RealtimeChannel | null>(null);

  useEffect(() => {
    if (!phone) return;
    const supabase = createClient();

    // Initial fetch (most recent first)
    supabase
      .from("agent_runs")
      .select("*")
      .eq("phone", phone)
      .order("started_at", { ascending: false })
      .limit(50)
      .then(({ data }) => {
        if (data) setRuns((data as AgentRun[]).reverse());
      });

    // Subscribe to inserts and updates
    channelRef.current = supabase
      .channel(`agent_runs:${phone}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "agent_runs",
          filter: `phone=eq.${phone}`,
        },
        (payload) => {
          setRuns((prev) => [...prev, payload.new as AgentRun]);
        }
      )
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "agent_runs",
          filter: `phone=eq.${phone}`,
        },
        (payload) => {
          setRuns((prev) =>
            prev.map((r) =>
              r.id === (payload.new as AgentRun).id
                ? (payload.new as AgentRun)
                : r
            )
          );
        }
      )
      .subscribe();

    return () => {
      channelRef.current?.unsubscribe();
    };
  }, [phone]);

  return runs;
}

// ── useAgentEvents ───────────────────────────────────────

export function useAgentEvents(runIds: string[]) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const channelRef = useRef<RealtimeChannel | null>(null);
  const runIdSet = useRef(new Set<string>());

  // Keep the ref set in sync
  useEffect(() => {
    runIdSet.current = new Set(runIds);
  }, [runIds]);

  useEffect(() => {
    if (runIds.length === 0) return;
    const supabase = createClient();

    // Initial fetch for all known run IDs
    supabase
      .from("agent_events")
      .select("*")
      .in("run_id", runIds)
      .order("created_at", { ascending: true })
      .then(({ data }) => {
        if (data) setEvents(data as AgentEvent[]);
      });

    // Subscribe to all agent_events inserts, filter client-side
    channelRef.current = supabase
      .channel("agent_events:all")
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "agent_events",
        },
        (payload) => {
          const evt = payload.new as AgentEvent;
          if (runIdSet.current.has(evt.run_id)) {
            setEvents((prev) => [...prev, evt]);
          }
        }
      )
      .subscribe();

    return () => {
      channelRef.current?.unsubscribe();
    };
    // Re-subscribe when the serialized runIds change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runIds.join(",")]);

  return events;
}
