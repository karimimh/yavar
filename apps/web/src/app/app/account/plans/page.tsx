"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function PlansPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["plans"],
    queryFn: () =>
      api<{
        current: {
          plan_name_fa: string;
          task_runs_remaining: number;
          sms_remaining: number;
          task_run_limit: number;
        };
        pro_price_fa: string;
        auto_renew: boolean;
        sandbox: boolean;
      }>("/api/billing/plans/"),
  });
  const pay = useMutation({
    mutationFn: async () => {
      const started = await api<{ authority: string }>("/api/billing/checkout/", {
        method: "POST",
        json: {},
      });
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/billing/sandbox/pay/?authority=${started.authority}`,
        { credentials: "include" },
      );
      return api("/api/billing/verify/", {
        method: "POST",
        json: { authority: started.authority },
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plans"] }),
  });

  return (
    <div className="grid gap-4">
      <h1 className="text-2xl font-bold">طرح و استفاده</h1>
      <p>طرح فعلی: {data?.current.plan_name_fa}</p>
      <p>
        اجراهای باقی‌مانده: {data?.current.task_runs_remaining} از{" "}
        {data?.current.task_run_limit}
      </p>
      <p>پیامک باقی‌مانده: {data?.current.sms_remaining}</p>
      <p>قیمت حرفه‌ای: {data?.pro_price_fa}</p>
      <p className="text-sm">تمدید خودکار وجود ندارد. درگاه آزمایشی محصول یاور است.</p>
      <button className="w-fit rounded-lg bg-primary px-4 py-2 text-primary-foreground" onClick={() => pay.mutate()}>
        خرید آزمایشی حرفه‌ای
      </button>
    </div>
  );
}
