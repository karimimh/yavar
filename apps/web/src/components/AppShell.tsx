import Link from "next/link";
import type { ReactNode } from "react";

const NAV = [
  { href: "/app/assistant", label: "دستیار" },
  { href: "/app/tasks", label: "کارها" },
  { href: "/app/agenda", label: "برنامه" },
  { href: "/app/account", label: "حساب" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-10 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <Link href="/app/assistant" className="font-bold">
            یاور
          </Link>
          <nav className="flex gap-3 text-sm" aria-label="اصلی">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded px-2 py-1 hover:bg-muted focus-visible:outline focus-visible:outline-2"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-4">{children}</main>
    </div>
  );
}
