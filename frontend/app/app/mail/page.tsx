"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import DomainHero from "@/components/DomainHero";
import InputBar from "@/components/InputBar";

type Status = "loading" | "connected" | "not_connected" | "no_phone" | "error";

export default function MailPage() {
  const [status, setStatus] = useState<Status>("loading");
  const [phone, setPhone] = useState<string | null>(null);
  const supabase = createClient();

  useEffect(() => {
    (async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();
        if (!user) {
          setStatus("error");
          return;
        }

        const { data: profile } = await supabase
          .from("profiles")
          .select("phone")
          .eq("id", user.id)
          .maybeSingle();

        if (!profile?.phone) {
          setStatus("no_phone");
          return;
        }
        setPhone(profile.phone);

        const res = await fetch(
          `/api/buckeyemail/status?phone=${encodeURIComponent(profile.phone)}`
        );
        if (!res.ok) {
          setStatus("not_connected");
          return;
        }
        const json = await res.json();
        setStatus(json.connected ? "connected" : "not_connected");
      } catch {
        setStatus("error");
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleConnect = () => {
    if (phone) {
      window.location.href = `/auth/buckeyemail/start?phone=${encodeURIComponent(phone)}`;
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="buckeyemail" accentColor="rgb(0,120,212)" />

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "0 32px 32px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 32,
        }}
      >
        {/* Envelope icon */}
        <svg
          width="64"
          height="64"
          viewBox="0 0 24 24"
          fill="none"
          stroke="rgba(255,255,255,0.25)"
          strokeWidth="1"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <path d="M22 7l-10 6L2 7" />
        </svg>

        {status === "loading" && (
          <p
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 13,
              color: "rgba(255,255,255,0.35)",
              letterSpacing: "1px",
            }}
          >
            checking connection...
          </p>
        )}

        {status === "not_connected" && (
          <>
            <div style={{ textAlign: "center", maxWidth: 400 }}>
              <h2
                style={{
                  fontFamily: "var(--font-jakarta)",
                  fontWeight: 200,
                  fontSize: 22,
                  color: "rgba(255,255,255,0.85)",
                  margin: "0 0 8px",
                  letterSpacing: "0.1em",
                  textTransform: "lowercase",
                }}
              >
                connect buckeyemail
              </h2>
              <p
                style={{
                  fontFamily: "var(--font-jakarta)",
                  fontSize: 13,
                  color: "rgba(255,255,255,0.45)",
                  margin: 0,
                  lineHeight: 1.6,
                }}
              >
                one tap to link your osu microsoft 365 inbox.
                <br />
                then just text &quot;check my email&quot; anytime.
              </p>
            </div>

            <button
              onClick={handleConnect}
              style={{
                fontFamily: "var(--font-jakarta)",
                fontSize: 14,
                fontWeight: 400,
                letterSpacing: "0.5px",
                color: "white",
                background: "rgb(0,120,212)",
                border: "none",
                borderRadius: 8,
                padding: "14px 40px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgb(0,100,190)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgb(0,120,212)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              connect
            </button>
          </>
        )}

        {status === "connected" && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 12,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontFamily: "var(--font-jakarta)",
                fontSize: 12,
                color: "rgba(80,200,120,0.8)",
              }}
            >
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "rgb(80,200,120)",
                }}
              />
              buckeyemail connected
            </div>
            <p
              style={{
                fontFamily: "var(--font-jakarta)",
                fontSize: 13,
                color: "rgba(255,255,255,0.35)",
                margin: 0,
                textAlign: "center",
                lineHeight: 1.6,
              }}
            >
              text &quot;check my email&quot; to read your inbox.
            </p>
          </div>
        )}

        {status === "no_phone" && (
          <p
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 13,
              color: "rgba(255,255,255,0.45)",
              textAlign: "center",
              lineHeight: 1.6,
            }}
          >
            register your phone number first to connect buckeyemail.
          </p>
        )}

        {status === "error" && (
          <p
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 13,
              color: "rgba(239,68,68,0.7)",
              textAlign: "center",
            }}
          >
            something went wrong. try refreshing.
          </p>
        )}
      </div>

      <InputBar
        placeholder="ask about your email..."
        onSubmit={(msg) => console.log("mail:", msg)}
      />
    </div>
  );
}
