"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function OpsPage() {
  const qc = useQueryClient();
  const { data, error } = useQuery({
    queryKey: ["ops"],
    queryFn: () =>
      api<{
        pause_all_external_submissions: boolean;
        capabilities: { slug: string; operator_disabled: boolean; status: string }[];
      }>("/api/ops/dashboard/"),
  });
  const disable = useMutation({
    mutationFn: (slug: string) =>
      api("/api/ops/capabilities/disable/", { method: "POST", json: { slug, disabled: true } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ops"] }),
  });
  const pause = useMutation({
    mutationFn: () => api("/api/ops/pause-submissions/", { method: "POST", json: { paused: true } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ops"] }),
  });

  if (error) return <p className="p-4">دسترسی اپراتور لازم است.</p>;

  return (
    <main className="mx-auto max-w-3xl p-4">
      <h1 className="text-2xl font-bold">عملیات</h1>
      <p className="text-sm">اپراتور نمی‌تواند به جای کاربر تأیید کند، رمز وارد کند یا جعل هویت کند.</p>
      <button className="mt-3 rounded-lg border px-3 py-2" onClick={() => pause.mutate()}>
        توقف همهٔ ارسال‌های خارجی
      </button>
      <ul className="mt-4 grid gap-2">
        {data?.capabilities.map((c) => (
          <li key={c.slug} className="flex items-center justify-between rounded-lg border p-3">
            <span>
              {c.slug} — {c.status}
            </span>
            <button className="text-sm underline" onClick={() => disable.mutate(c.slug)}>
              غیرفعال‌سازی
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
