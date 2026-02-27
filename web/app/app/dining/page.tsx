"use client";

import DomainHero from "@/components/DomainHero";
import DiningCard from "@/components/domain/DiningCard";
import InputBar from "@/components/InputBar";

const DEMO_HALLS = [
  {
    hallName: "scott traditions",
    mealPeriod: "lunch",
    hours: "11:00 am — 2:00 pm",
    isOpen: true,
    stations: [
      { name: "grilled chicken", items: ["breast w/ herb butter", "thigh w/ bbq glaze"] },
      { name: "pasta bar", items: ["marinara", "alfredo", "pesto"] },
      { name: "salad bar", items: ["caesar", "garden", "greek"] },
      { name: "soup station", items: ["tomato bisque", "chicken noodle"] },
    ],
  },
  {
    hallName: "kennedy commons",
    mealPeriod: "lunch",
    hours: "11:00 am — 1:30 pm",
    isOpen: true,
    stations: [
      { name: "grill", items: ["burgers", "chicken tenders", "fries"] },
      { name: "deli", items: ["club sandwich", "wrap", "soup combo"] },
      { name: "stir fry", items: ["teriyaki chicken", "lo mein", "fried rice"] },
    ],
  },
  {
    hallName: "north commons",
    mealPeriod: "closed",
    hours: "opens at 4:30 pm",
    isOpen: false,
    stations: [],
  },
  {
    hallName: "morrill commons",
    mealPeriod: "lunch",
    hours: "11:00 am — 2:00 pm",
    isOpen: true,
    stations: [
      { name: "comfort food", items: ["mac & cheese", "meatloaf", "mashed potatoes"] },
      { name: "pizza", items: ["cheese", "pepperoni", "veggie"] },
      { name: "desserts", items: ["brownies", "cookies", "fruit"] },
    ],
  },
  {
    hallName: "traditions at scott",
    mealPeriod: "lunch",
    hours: "11:00 am — 2:00 pm",
    isOpen: true,
    stations: [
      { name: "sushi bar", items: ["california roll", "spicy tuna", "edamame"] },
      { name: "ramen", items: ["tonkotsu", "shoyu", "miso"] },
    ],
  },
  {
    hallName: "berry cafe",
    mealPeriod: "closed",
    hours: "opens at 7:00 am tomorrow",
    isOpen: false,
    stations: [],
  },
];

export default function DiningPage() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="dining" accentColor="rgb(198,40,40)" />

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "0 32px 32px",
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 16,
          }}
        >
          {DEMO_HALLS.map((hall) => (
            <DiningCard
              key={hall.hallName}
              hallName={hall.hallName}
              mealPeriod={hall.mealPeriod}
              hours={hall.hours}
              isOpen={hall.isOpen}
              stations={hall.stations}
            />
          ))}
        </div>
      </div>

      <InputBar
        placeholder="ask about dining..."
        onSubmit={(msg) => console.log("dining:", msg)}
      />
    </div>
  );
}
