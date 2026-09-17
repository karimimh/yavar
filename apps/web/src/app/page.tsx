"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type Coverage = {
  disclaimer_fa: string;
  capabilities: {
    slug: string;
    name_fa: string;
    description_fa: string;
    status_label_fa: string;
    sandbox: boolean;
    required_user_steps_fa: string;
  }[];
};

export default function Home() {
  const { data } = useQuery({
    queryKey: ["coverage"],
    queryFn: () => api<Coverage>("/api/coverage/"),
  });

  return (
    <main className="mx-auto flex max-w-3xl flex-1 flex-col gap-6 px-4 py-10">
      <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3">
        همهٔ ارائه‌دهندگان خارجی در این نسخه <strong>آزمایشی / سندباکس</strong> هستند.
        رسید ساختگی به‌عنوان موفقیت واقعی نشان داده نمی‌شود.
      </p>
      <h1 className="text-3xl font-bold">یاور</h1>
      <p className="text-lg leading-8">
        بگو چه کاری داری؛ پیداش می‌کنم، آماده‌اش می‌کنم و با تأیید تو، کارهای
        پشتیبانی‌شده را انجام می‌دهم.
      </p>
      <p className="text-muted-foreground leading-7">
        این محصول اتوماسیون همه‌چیز روی وب ایران نیست. فقط کارهای فهرست‌شده را
        انجام می‌دهد. خرید بلیط، پرداخت قبض و ورود به حساب ارائه‌دهنده با شماست.
      </p>
      <div className="flex flex-wrap gap-3">
        <Link
          href="/sign-in"
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground focus-visible:outline"
        >
          ورود با شماره موبایل
        </Link>
        <Link href="/coverage" className="rounded-lg border px-4 py-2">
          پوشش خدمات
        </Link>
      </div>
      <section>
        <h2 className="mb-3 text-xl font-semibold">اقدامات پشتیبانی‌شده</h2>
        <ul className="grid gap-3">
          {(data?.capabilities ?? []).map((c) => (
            <li key={c.slug} className="rounded-xl border p-4">
              <div className="flex justify-between gap-2">
                <strong>{c.name_fa}</strong>
                <span className="text-xs">{c.status_label_fa}</span>
              </div>
              <p className="mt-2 text-sm">{c.description_fa}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                گام باقی‌مانده با شما: {c.required_user_steps_fa}
              </p>
            </li>
          ))}
        </ul>
      </section>
      <p className="text-sm text-muted-foreground">{data?.disclaimer_fa}</p>
    </main>
  );
}
