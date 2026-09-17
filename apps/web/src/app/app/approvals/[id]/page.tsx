"use client";

import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Approval = {
  id: number;
  action_label_fa: string;
  recipient_fa: string;
  destination: string;
  fields_snapshot: Record<string, string>;
  costs_fa: string;
  will_happen_fa: string;
  will_not_happen_fa: string;
  confirmation_how_fa: string;
  status: string;
  expires_at: string;
};

export default function ApprovalPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { data } = useQuery({
    queryKey: ["approval", params.id],
    queryFn: () => api<Approval>(`/api/approvals/${params.id}/`),
  });
  const decide = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api(`/api/approvals/${params.id}/decide/`, { method: "POST", json: payload }),
    onSuccess: () => router.push("/app/tasks"),
  });

  if (!data) return <p>در حال بارگذاری…</p>;

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">{data.action_label_fa}</h1>
      <p className="text-sm">گیرنده: {data.recipient_fa}</p>
      <p className="break-all text-sm">مقصد: {data.destination}</p>
      <dl className="grid gap-2 text-sm">
        {Object.entries(data.fields_snapshot).map(([k, v]) => (
          <div key={k} className="rounded-lg border p-2">
            <dt className="text-muted-foreground">{k}</dt>
            <dd>{String(v)}</dd>
          </div>
        ))}
      </dl>
      <p>{data.costs_fa}</p>
      <p>پس از تأیید: {data.will_happen_fa}</p>
      <p>انجام نمی‌شود: {data.will_not_happen_fa}</p>
      <p>تشخیص تأیید: {data.confirmation_how_fa}</p>
      <p className="text-xs">انقضا: {data.expires_at}</p>
      <div className="flex flex-col gap-2 sm:flex-row">
        <button
          className="rounded-lg bg-primary px-4 py-3 text-primary-foreground"
          onClick={() => decide.mutate({ action: "approve", fill_consent: true })}
        >
          {data.action_label_fa}
        </button>
        <button className="rounded-lg border px-4 py-3" onClick={() => decide.mutate({ action: "cancel" })}>
          انصراف
        </button>
      </div>
    </div>
  );
}
