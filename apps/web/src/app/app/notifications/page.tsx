"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["inbox"],
    queryFn: () =>
      api<{
        notifications: {
          id: number;
          title_fa: string;
          body_fa: string;
          read: boolean;
          delivery_status: string;
        }[];
      }>("/api/notifications/"),
  });
  const read = useMutation({
    mutationFn: (id: number) => api(`/api/notifications/${id}/read/`, { method: "POST", json: {} }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbox"] }),
  });

  return (
    <div className="grid gap-3">
      <h1 className="text-2xl font-bold">اعلان‌ها</h1>
      {(data?.notifications ?? []).map((n) => (
        <button
          key={n.id}
          className={`rounded-xl border p-3 text-right ${n.read ? "opacity-70" : ""}`}
          onClick={() => read.mutate(n.id)}
        >
          <div className="font-medium">{n.title_fa}</div>
          <div className="text-sm">{n.body_fa}</div>
          <div className="text-xs">وضعیت تحویل: {n.delivery_status}</div>
        </button>
      ))}
    </div>
  );
}
