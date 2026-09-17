"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [terms, setTerms] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  const [sms, setSms] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/api/auth/onboarding/", {
        method: "POST",
        json: {
          terms_accepted: terms,
          privacy_accepted: privacy,
          timezone: "Asia/Tehran",
          sms_opt_in: sms,
          week_starts_on: "saturday",
        },
      });
      router.push("/app/assistant");
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطا");
    }
  }

  return (
    <main className="mx-auto flex max-w-md flex-1 flex-col gap-4 px-4 py-10">
      <h1 className="text-2xl font-bold">شروع</h1>
      <p className="text-sm leading-7">
        منطقهٔ زمانی پیشنهادی: تهران. مکان شما به‌صورت خاموش حدس زده نمی‌شود.
        گفتگوها برای آموزش مدل استفاده نمی‌شوند مگر رضایت جدا بدهید.
      </p>
      <form onSubmit={submit} className="grid gap-3 text-sm">
        <label className="flex gap-2">
          <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} />
          شرایط استفاده را می‌پذیرم.
        </label>
        <label className="flex gap-2">
          <input
            type="checkbox"
            checked={privacy}
            onChange={(e) => setPrivacy(e.target.checked)}
          />
          خلاصهٔ حریم خصوصی را خواندم.
        </label>
        <label className="flex gap-2">
          <input type="checkbox" checked={sms} onChange={(e) => setSms(e.target.checked)} />
          پیامک یادآور (اختیاری)
        </label>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">ادامه</button>
      </form>
      {error ? <p className="text-destructive">{error}</p> : null}
    </main>
  );
}
