"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Task } from "@/lib/api";
import { formatToman } from "@/lib/dates";

export default function ComparePage() {
  const params = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { data: task } = useQuery({
    queryKey: ["task", params.id],
    queryFn: () => api<Task & { payload: { search?: { ranking_explanation_fa?: string }; comparison?: { ranking_explanation_fa?: string; sources_checked?: string[] } } }>(
      `/api/tasks/${params.id}/`,
    ),
  });
  const select = useMutation({
    mutationFn: (offerId: string) =>
      api(`/api/travel/tasks/${params.id}/select/`, { method: "POST", json: { offer_id: offerId } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["task", params.id] }),
  });

  const comparison = task?.payload?.comparison as
    | { options?: Record<string, unknown>[]; ranking_explanation_fa?: string; sources_checked?: string[] }
    | undefined;
  const search = task?.payload?.search as
    | { matches?: Record<string, unknown>[]; near_matches?: Record<string, unknown>[]; disclaimer_fa?: string }
    | undefined;

  const rows = [
    ...((search?.matches as Record<string, unknown>[]) ?? []),
    ...((search?.near_matches as Record<string, unknown>[]) ?? []),
    ...((comparison?.options as Record<string, unknown>[]) ?? []),
  ];

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">مقایسه</h1>
      <p className="text-sm text-amber-800">منابع آزمایشی — «ارزان‌ترین ایران» ادعا نمی‌شود.</p>
      <p className="text-sm">{comparison?.ranking_explanation_fa || search?.disclaimer_fa}</p>
      <ul className="grid gap-3">
        {rows.map((row, i) => {
          const id = String(row.id ?? i);
          const amount = row.amount as string | undefined;
          const unit = (row.unit as string) || "";
          const isMatch = row.is_match !== false;
          return (
            <li key={id} className="rounded-xl border p-3 text-sm">
              <div className="flex justify-between gap-2">
                <strong>{String(row.title || row.carrier || row.provider || row.provider_name_fa)}</strong>
                <span>{isMatch ? "مطابق محدودیت سخت" : `نزدیک — ${row.violated_constraint || ""}`}</span>
              </div>
              {amount ? <p>{formatToman(amount, unit)}</p> : <p>قیمت نامشخص</p>}
              {Array.isArray(row.unverified) || Array.isArray(row.unverified_fields) ? (
                <p className="text-xs">نیاز به تأیید ارائه‌دهنده: پوشش/سرعت/تخفیف حساب</p>
              ) : null}
              {row.handoff_url || row.source_url ? (
                <a className="underline" href={String(row.handoff_url || row.source_url)} target="_blank" rel="noreferrer">
                  منبع
                </a>
              ) : null}
              {row.id && task?.kind?.startsWith("travel") ? (
                <button
                  className="mt-2 block rounded-lg border px-3 py-1"
                  onClick={() => select.mutate(String(row.id))}
                >
                  انتخاب و ادامه در ارائه‌دهنده
                </button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
