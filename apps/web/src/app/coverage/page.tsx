"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

export default function CoveragePage() {
  const { data } = useQuery({
    queryKey: ["coverage"],
    queryFn: () =>
      api<{
        disclaimer_fa: string;
        capabilities: {
          slug: string;
          name_fa: string;
          description_fa: string;
          status_label_fa: string;
          geography_note_fa: string;
          required_user_steps_fa: string;
          identifier_type: string;
          sandbox: boolean;
        }[];
      }>("/api/coverage/"),
  });

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-bold">پوشش خدمات</h1>
      <p className="mt-2 text-sm text-amber-800">{data?.disclaimer_fa}</p>
      <ul className="mt-4 grid gap-3">
        {data?.capabilities.map((c) => (
          <li key={c.slug} className="rounded-xl border p-4">
            <div className="flex justify-between">
              <strong>{c.name_fa}</strong>
              <span>{c.status_label_fa}</span>
            </div>
            <p className="mt-2 text-sm">{c.description_fa}</p>
            <p className="text-sm">محدوده: {c.geography_note_fa}</p>
            <p className="text-sm">گام شما: {c.required_user_steps_fa}</p>
            {c.identifier_type ? (
              <p className="text-xs">نوع شناسه: {c.identifier_type}</p>
            ) : null}
          </li>
        ))}
      </ul>
      <Link href="/" className="mt-6 inline-block underline">
        بازگشت
      </Link>
    </main>
  );
}
