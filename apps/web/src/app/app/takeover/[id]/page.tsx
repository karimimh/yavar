"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, type Task } from "@/lib/api";

export default function TakeoverPage() {
  const params = useParams<{ id: string }>();
  const { data: task } = useQuery({
    queryKey: ["task", params.id],
    queryFn: () => api<Task>(`/api/tasks/${params.id}/`),
  });
  const takeover = (task?.payload as { takeover?: { reason?: string; domain?: string } })?.takeover;
  const handoff = (task?.payload as { payment_handoff?: { url?: string }; handoff?: { url?: string; note_fa?: string } });

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">ادامه توسط شما</h1>
      <p>{task?.current_activity_fa}</p>
      {takeover ? (
        <p className="text-sm">
          علت: {takeover.reason} {takeover.domain ? `(${takeover.domain})` : ""}
        </p>
      ) : null}
      {handoff?.handoff?.url ? (
        <a className="underline" href={handoff.handoff.url} target="_blank" rel="noreferrer">
          ادامه در ارائه‌دهنده (آزمایشی)
        </a>
      ) : null}
      {handoff?.payment_handoff?.url ? (
        <a className="underline" href={handoff.payment_handoff.url} target="_blank" rel="noreferrer">
          صفحه پرداخت آزمایشی
        </a>
      ) : null}
      <p className="text-sm text-muted-foreground">
        بستن برنامه به معنی تأیید نیست. رمز و کارت را فقط در صفحهٔ ارائه‌دهنده وارد کنید.
      </p>
    </div>
  );
}
