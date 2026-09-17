"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function SignInPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function requestCode(e: FormEvent) {
    e.preventDefault();
    setError("");
    const data = await api<{ message: string; ok?: boolean; error?: string }>(
      "/api/auth/otp/request/",
      { method: "POST", json: { phone } },
    );
    setMessage(data.message);
    setStep("code");
  }

  async function verify(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const data = await api<{ ok: boolean; user: { onboarding_completed: boolean } }>(
        "/api/auth/otp/verify/",
        { method: "POST", json: { phone, code } },
      );
      router.push(data.user.onboarding_completed ? "/app/assistant" : "/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "ورود ناموفق");
    }
  }

  return (
    <main className="mx-auto flex max-w-md flex-1 flex-col gap-4 px-4 py-10">
      <h1 className="text-2xl font-bold">ورود</h1>
      <p className="text-sm text-muted-foreground">
        ورود فقط با شماره موبایل ایرانی و کد یکبارمصرف. گوگل یا تلگرام لازم نیست.
        در محیط توسعه کد در لاگ بک‌اند چاپ می‌شود.
      </p>
      {step === "phone" ? (
        <form onSubmit={requestCode} className="grid gap-3">
          <label className="grid gap-1 text-sm">
            شماره موبایل
            <input
              className="rounded-lg border px-3 py-2"
              inputMode="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              dir="ltr"
            />
          </label>
          <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">
            ارسال کد
          </button>
        </form>
      ) : (
        <form onSubmit={verify} className="grid gap-3">
          <p className="text-sm">{message}</p>
          <label className="grid gap-1 text-sm">
            کد تأیید
            <input
              className="rounded-lg border px-3 py-2"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              dir="ltr"
            />
          </label>
          <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">
            ورود
          </button>
        </form>
      )}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </main>
  );
}
