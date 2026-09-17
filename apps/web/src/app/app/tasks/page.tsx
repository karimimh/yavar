"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Task } from "@/lib/api";
import { TaskCard } from "@/components/TaskCard";

export default function TasksPage() {
  const [filter, setFilter] = useState("");
  const [q, setQ] = useState("");
  const { data } = useQuery({
    queryKey: ["tasks", filter, q],
    queryFn: () =>
      api<{ tasks: Task[] }>(
        `/api/tasks/?filter=${encodeURIComponent(filter)}&q=${encodeURIComponent(q)}`,
      ),
  });

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">کارها</h1>
      <div className="flex flex-wrap gap-2">
        {[
          ["", "همه"],
          ["attention", "نیاز به توجه"],
          ["delivered", "تحویل‌شده"],
          ["closed", "بسته‌شده"],
        ].map(([id, label]) => (
          <button
            key={id}
            className={`rounded-full border px-3 py-1 text-sm ${filter === id ? "bg-muted" : ""}`}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <input
        className="rounded-lg border px-3 py-2"
        placeholder="جستجو"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="جستجوی کارها"
      />
      {(data?.tasks ?? []).map((t) => (
        <TaskCard key={t.id} task={t} />
      ))}
    </div>
  );
}
