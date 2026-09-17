"use client";

import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Task } from "@/lib/api";
import { TaskCard } from "@/components/TaskCard";

const EXAMPLES = [
  { label: "یادآور", text: "فردا ساعت ۱۰ یادم بنداز قبض رو بررسی کنم" },
  { label: "اینترنت", text: "این ماه اینترنت کدوم شرکت برای من ارزون‌تره؟ مقایسه کن." },
  { label: "پرواز داخلی", text: "برای پنجشنبه یه بلیط تهران به شیراز پیدا کن، صبح باشه و زیر ۵ میلیون." },
  { label: "قبض برق", text: "قبض برق خانه رو بررسی کن" },
];

export default function AssistantPage() {
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [warning, setWarning] = useState("");

  const send = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("text", text);
      if (conversationId) form.append("conversation_id", String(conversationId));
      if (file) form.append("screenshot", file);
      return api<{
        conversation_id: number;
        tasks: Task[];
        secret_warning?: boolean;
        duplicate_screenshot_warning_fa?: string;
        messages: { role: string; text: string }[];
      }>("/api/conversations/send/", { method: "POST", form });
    },
    onSuccess: (data) => {
      setConversationId(data.conversation_id);
      setText("");
      setFile(null);
      setWarning(
        data.secret_warning
          ? "رمز استفاده نشد. می‌توانید پیام را حذف کنید."
          : data.duplicate_screenshot_warning_fa || "",
      );
      qc.invalidateQueries({ queryKey: ["conversation", data.conversation_id] });
    },
  });

  const conv = useQuery({
    queryKey: ["conversation", conversationId],
    enabled: conversationId != null,
    queryFn: () =>
      api<{ messages: { id: number; role: string; text: string }[]; tasks: Task[] }>(
        `/api/conversations/${conversationId}/`,
      ),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    send.mutate();
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">دستیار</h1>
      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            type="button"
            className="rounded-full border px-3 py-1 text-sm"
            onClick={() => setText(ex.text)}
          >
            {ex.label}
          </button>
        ))}
      </div>
      <form onSubmit={onSubmit} className="grid gap-2">
        <label className="sr-only" htmlFor="composer">
          پیام
        </label>
        <textarea
          id="composer"
          className="min-h-24 rounded-xl border p-3"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="چه کاری دارید؟"
        />
        <label className="text-sm">
          یک تصویر (JPEG/PNG/WebP تا ۱۰ مگابایت)
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block"
          />
        </label>
        <button
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"
          disabled={send.isPending}
        >
          {send.isPending ? "در حال ارسال…" : "ارسال"}
        </button>
      </form>
      {warning ? <p className="text-sm text-amber-800">{warning}</p> : null}
      <div className="grid gap-2">
        {conv.data?.messages.map((m) => (
          <div
            key={m.id}
            className={`rounded-xl p-3 text-sm ${m.role === "user" ? "bg-muted" : "border"}`}
          >
            {m.text}
          </div>
        ))}
      </div>
      <div className="grid gap-3">
        {(conv.data?.tasks ?? send.data?.tasks ?? []).map((t) => (
          <TaskCard key={t.id} task={t} />
        ))}
      </div>
    </div>
  );
}
