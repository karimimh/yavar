import Link from "next/link";
import type { Task } from "@/lib/api";

export function TaskCard({ task }: { task: Task }) {
  return (
    <article className="rounded-xl border p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold">
          <Link
            href={`/app/tasks/${task.id}`}
            className="underline-offset-4 hover:underline focus-visible:outline"
          >
            {task.title}
          </Link>
        </h3>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
          {task.execution_state_fa}
        </span>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{task.current_activity_fa}</p>
      <p className="mt-1 text-sm">
        نتیجه: <span className="font-medium">{task.external_outcome_fa}</span>
      </p>
      {task.remaining_work ? (
        <p className="mt-1 text-sm">باقی‌مانده: {task.remaining_work}</p>
      ) : null}
    </article>
  );
}
