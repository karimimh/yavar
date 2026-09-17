"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, type User } from "@/lib/api";

export default function AccountPage() {
  const router = useRouter();
  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: () => api<User>("/api/auth/me/"),
  });
  const { data: facts } = useQuery({
    queryKey: ["facts"],
    queryFn: () =>
      api<{ facts: { id: number; label: string; value: string; origin_fa: string }[] }>(
        "/api/memory/",
      ),
  });
  const { data: usage } = useQuery({
    queryKey: ["plans"],
    queryFn: () =>
      api<{ current: { plan_name_fa: string; task_runs_remaining: number; sms_remaining: number } }>(
        "/api/billing/plans/",
      ),
  });
  const logout = useMutation({
    mutationFn: () => api("/api/auth/logout/", { method: "POST", json: {} }),
    onSuccess: () => {
      router.push("/");
    },
  });
  const del = useMutation({
    mutationFn: () => api("/api/auth/delete/", { method: "POST", json: {} }),
    onSuccess: () => {
      router.push("/");
    },
  });

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">حساب</h1>
      <p className="text-sm">شماره: {user?.phone}</p>
      <p className="text-sm">منطقهٔ زمانی: {user?.timezone}</p>
      <p className="text-sm">
        طرح: {usage?.current.plan_name_fa} — باقی‌مانده اجرا:{" "}
        {usage?.current.task_runs_remaining} — پیامک: {usage?.current.sms_remaining}
      </p>
      <div className="flex flex-wrap gap-2 text-sm">
        <Link className="rounded-lg border px-3 py-2" href="/app/account/plans">
          طرح و استفاده
        </Link>
        <Link className="rounded-lg border px-3 py-2" href="/app/notifications">
          اعلان‌ها
        </Link>
        <Link className="rounded-lg border px-3 py-2" href="/coverage">
          پوشش خدمات
        </Link>
        <Link className="rounded-lg border px-3 py-2" href="/app/help">
          راهنما
        </Link>
        <a className="rounded-lg border px-3 py-2" href={`${process.env.NEXT_PUBLIC_API_URL}/api/auth/export/`}>
          برون‌بری داده
        </a>
      </div>
      <section>
        <h2 className="font-semibold">واقعیت‌های ذخیره‌شده</h2>
        <ul className="text-sm">
          {facts?.facts.map((f) => (
            <li key={f.id}>
              {f.label}: {f.value} — {f.origin_fa}
            </li>
          ))}
        </ul>
      </section>
      <p className="text-xs text-muted-foreground">
        آموزش مدل به‌صورت پیش‌فرض خاموش است. حذف حساب داده‌های ارائه‌دهنده را پاک
        نمی‌کند. پنجرهٔ حذف فعال ۳۰ روز و پشتیبان حداکثر ۹۰ روز است.
      </p>
      <button className="w-fit rounded-lg border px-3 py-2" onClick={() => logout.mutate()}>
        خروج
      </button>
      <button
        className="w-fit rounded-lg border border-destructive px-3 py-2"
        onClick={() => del.mutate()}
      >
        حذف حساب
      </button>
      {user?.is_operator ? (
        <Link className="text-sm underline" href="/ops">
          پنل اپراتور
        </Link>
      ) : null}
    </div>
  );
}
