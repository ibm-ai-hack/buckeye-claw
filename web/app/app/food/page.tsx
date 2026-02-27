"use client";

import { useState } from "react";
import DomainHero from "@/components/DomainHero";
import InputBar from "@/components/InputBar";

const DEMO_RESTAURANTS = [
  { name: "chipotle", cuisine: "mexican", rating: "4.2", eta: "25-35 min" },
  { name: "raising cane's", cuisine: "chicken", rating: "4.5", eta: "20-30 min" },
  { name: "panda express", cuisine: "chinese", rating: "3.8", eta: "30-40 min" },
  { name: "jimmy john's", cuisine: "sandwiches", rating: "4.0", eta: "15-25 min" },
  { name: "blaze pizza", cuisine: "pizza", rating: "4.3", eta: "25-35 min" },
  { name: "kung fu tea", cuisine: "boba tea", rating: "4.4", eta: "20-30 min" },
];

export default function FoodPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = DEMO_RESTAURANTS.filter((r) =>
    `${r.name} ${r.cuisine}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="food" accentColor="rgb(80,160,80)" />

      <div style={{ flex: 1, overflowY: "auto", padding: "0 32px 32px" }}>
        {/* Search */}
        <div
          style={{
            marginBottom: 24,
            position: "relative",
          }}
        >
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="search restaurants..."
            style={{
              width: "100%",
              maxWidth: 500,
              padding: "12px 16px",
              background: "var(--color-surface-2)",
              border: "1px solid var(--color-border-medium)",
              borderRadius: 10,
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 15,
              color: "var(--color-text-primary)",
              outline: "none",
              caretColor: "var(--color-scarlet)",
              transition: "border-color 0.2s ease",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--color-border-focus)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--color-border-medium)";
            }}
          />
        </div>

        {/* Restaurant grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: 16,
          }}
        >
          {filtered.map((restaurant) => (
            <div
              key={restaurant.name}
              style={{
                background: "var(--color-surface-1)",
                border: "1px solid var(--color-surface-3)",
                borderRadius: 14,
                padding: 20,
                cursor: "pointer",
                transition: "border-color 0.15s ease, background 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border-bright)";
                e.currentTarget.style.background = "var(--color-surface-2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--color-surface-3)";
                e.currentTarget.style.background = "var(--color-surface-1)";
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-outfit)",
                  fontWeight: 300,
                  fontSize: 18,
                  color: "var(--color-text-heading)",
                  marginBottom: 8,
                }}
              >
                {restaurant.name}
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontWeight: 400,
                    fontSize: 12,
                    color: "var(--color-text-label)",
                    letterSpacing: "1px",
                  }}
                >
                  {restaurant.cuisine}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontWeight: 400,
                    fontSize: 12,
                    color: "var(--color-text-faint)",
                  }}
                >
                  {restaurant.rating} · {restaurant.eta}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <InputBar
        placeholder="order food..."
        onSubmit={(msg) => console.log("food:", msg)}
      />

      <style jsx>{`
        input::placeholder {
          color: var(--color-text-placeholder);
          font-family: var(--font-space-mono);
        }
      `}</style>
    </div>
  );
}
