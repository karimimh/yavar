"use client";

import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function HelpPage() {
  const [taskId, setTaskId] = useState("");
  const [message, setMessage] = useState("");
  const [consent, setConsent] = useState(false);
  const [ok, setOk] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    const data = await api<{ incident_id: number }>("/api/ops/report/", {
      method: "POST",
      json: {
        task_id: taskId ? Number(taskId) : null,
        message,
        consent_share_task: consent,
      },
    });
    setOk(`گزارش ثبت شد (#${data.incident_id}).`);
  }

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">راهنما و گزارش مشکل</h1>
      <ul className="list-disc pr-5 text-sm leading-7">
        <li>یاور کارت، رمز بانکی یا OTP ارائه‌دهنده را در گفتگو نمی‌گیرد.</li>
        <li>تحویل به سایت ارائه‌دهنده به معنی خرید یا پرداخت قطعی نیست.</li>
        <li>ارسال فرم فقط برای جریان سندباکس تأییدشده است.</li>
      </ul>
      <form onSubmit={submit} className="grid gap-2 text-sm">
        <label>
          شناسه کار (اختیاری)
          <input
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={taskId}
            onChange={(e) => setTaskId(e.target.value)}
            dir="ltr"
          />
        </label>
        <label className="flex gap-2">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          رضایت می‌دهم همین کار برای پشتیبانی به اشتراک گذاشته شود.
        </label>
        <textarea
          className="min-h-24 rounded-lg border p-3"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          required
        />
        <button className="w-fit rounded-lg bg-primary px-4 py-2 text-primary-foreground">
          ارسال گزارش
        </button>
      </form>
      {ok ? <p>{ok}</p> : null}
    </div>
  );
}
