"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Task } from "@/lib/api";

export default function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { data: task } = useQuery({
    queryKey: ["task", params.id],
    queryFn: () => api<Task>(`/api/tasks/${params.id}/`),
  });
  const act = useMutation({
    mutationFn: (action: string) =>
      api(`/api/tasks/${params.id}/`, { method: "POST", json: { action } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["task", params.id] }),
  });

  if (!task) return <p>در حال بارگذاری…</p>;
  const pendingApproval = task.execution_state === "needs_approval";

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">{task.title}</h1>
      {task.can_stop ? (
        <button
          className="w-fit rounded-lg border border-destructive px-4 py-2"
          onClick={() => act.mutate("stop")}
        >
          توقف
        </button>
      ) : (
        <p className="text-sm text-muted-foreground">توقف در این وضعیت لازم نیست.</p>
      )}
      <section className="rounded-xl border p-4 text-sm leading-7">
        <p>
          <strong>هدف اولیه:</strong> {task.original_goal}
        </p>
        <p>
          <strong>تحویل توافق‌شده:</strong> {task.agreed_deliverable}
        </p>
        <p>
          وضعیت اجرا: {task.execution_state_fa} — نتیجه: {task.external_outcome_fa}
        </p>
        <p>{task.current_activity_fa}</p>
        {task.remaining_work ? <p>باقی‌مانده: {task.remaining_work}</p> : null}
      </section>
      <section>
        <h2 className="font-semibold">برنامه</h2>
        <ol className="list-decimal pr-5 text-sm">
          {(task.plan_checklist ?? []).map((s, i) => (
            <li key={i}>{s.fa}</li>
          ))}
        </ol>
      </section>
      <section>
        <h2 className="font-semibold">شواهد</h2>
        <ul className="text-sm">
          {task.evidence.map((e, i) => (
            <li key={i}>
              {e.summary_fa} ({e.proves}
              {e.reference ? ` — ${e.reference}` : ""})
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="font-semibold">تاریخچه</h2>
        <ol className="text-sm">
          {task.events.map((e, i) => (
            <li key={i}>{e.summary_fa}</li>
          ))}
        </ol>
      </section>
      <div className="flex flex-wrap gap-2 text-sm">
        {pendingApproval && task.latest_approval_id ? (
          <Link className="rounded-lg bg-primary px-3 py-2 text-primary-foreground" href={`/app/approvals/${task.latest_approval_id}`}>
            باز کردن پیش‌نمایش تأیید
          </Link>
        ) : null}
        {task.execution_state === "needs_user_takeover" ? (
          <Link className="rounded-lg border px-3 py-2" href={`/app/takeover/${task.id}`}>
            ادامه توسط شما
          </Link>
        ) : null}
        {task.kind === "research" || task.kind === "travel_search" ? (
          <Link className="rounded-lg border px-3 py-2" href={`/app/compare/${task.id}`}>
            مقایسه
          </Link>
        ) : null}
        <button className="rounded-lg border px-3 py-2" onClick={() => act.mutate("complete")}>
          علامت‌گذاری به‌عنوان تکمیل کاربر
        </button>
        <button className="rounded-lg border px-3 py-2" onClick={() => act.mutate("cancel")}>
          لغو
        </button>
      </div>
    </div>
  );
}
