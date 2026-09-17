"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Reminder = {
  id: number;
  title: string;
  display_fa: string;
  recurrence: string;
  cancelled: boolean;
};

export default function AgendaPage() {
  const [view, setView] = useState("today");
  const { data } = useQuery({
    queryKey: ["agenda", view],
    queryFn: () =>
      api<{ disclaimer_fa: string; items: Reminder[] }>(
        `/api/reminders/agenda/?view=${view}`,
      ),
  });

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">برنامه</h1>
      <p className="text-sm text-muted-foreground">{data?.disclaimer_fa}</p>
      <div className="flex gap-2">
        {[
          ["today", "امروز"],
          ["upcoming", "بعدی"],
          ["date", "تاریخ"],
        ].map(([id, label]) => (
          <button
            key={id}
            className={`rounded-full border px-3 py-1 ${view === id ? "bg-muted" : ""}`}
            onClick={() => setView(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <ul className="grid gap-2">
        {(data?.items ?? []).map((item) => (
          <li key={item.id} className="rounded-xl border p-3">
            <div className="font-medium">{item.title}</div>
            <div className="text-sm">{item.display_fa}</div>
            <div className="text-xs">{item.recurrence}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
