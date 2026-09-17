export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function ensureCsrf(): Promise<string> {
  const existing = getCookie("csrftoken");
  if (existing) return existing;
  const res = await fetch(`${API_URL}/api/auth/csrf/`, { credentials: "include" });
  const data = (await res.json()) as { csrfToken: string };
  return data.csrfToken;
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit & { json?: unknown; form?: FormData } = {},
): Promise<T> {
  const csrf = await ensureCsrf();
  const headers = new Headers(options.headers);
  headers.set("X-CSRFToken", csrf);
  let body = options.body;
  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  }
  if (options.form) {
    body = options.form;
  }
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
    body,
  });
  const data = (await res.json().catch(() => ({}))) as T & { error?: string };
  if (!res.ok) {
    throw new Error(
      (data as { error?: string; message_fa?: string }).error ||
        (data as { message_fa?: string }).message_fa ||
        `خطای ${res.status}`,
    );
  }
  return data;
}

export type User = {
  id: number;
  phone: string;
  timezone: string;
  onboarding_completed: boolean;
  is_operator: boolean;
  preferred_name: string;
  sms_opt_in: boolean;
  improvement_consent: boolean;
  deletion_requested_at: string | null;
};

export type Task = {
  id: number;
  title: string;
  kind: string;
  original_goal: string;
  agreed_deliverable: string;
  execution_state: string;
  execution_state_fa: string;
  external_outcome: string;
  external_outcome_fa: string;
  remaining_work: string;
  current_activity_fa: string;
  can_stop: boolean;
  payload: Record<string, unknown>;
  events: { kind: string; summary_fa: string; created_at: string }[];
  evidence: {
    type: string;
    summary_fa: string;
    proves: string;
    reference: string;
  }[];
  plan_checklist: { fa: string }[];
  latest_approval_id?: number | null;
};

export async function getMe(): Promise<User | null> {
  const res = await fetch(`${API_URL}/api/auth/me/`, { credentials: "include" });
  if (res.status === 403 || res.status === 401) return null;
  if (!res.ok) return null;
  return res.json();
}
