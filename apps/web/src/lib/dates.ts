/** Small shared date helper: Saturday-first week and Jalali display from ISO strings. */

const WEEKDAYS_FA = [
  "دوشنبه",
  "سه‌شنبه",
  "چهارشنبه",
  "پنجشنبه",
  "جمعه",
  "شنبه",
  "یکشنبه",
];

export function toPersianDigits(value: string): string {
  const map = "۰۱۲۳۴۵۶۷۸۹";
  return value.replace(/\d/g, (d) => map[Number(d)] ?? d);
}

export function saturdayStart(d: Date): Date {
  const day = d.getDay(); // Sun=0 ... Sat=6
  const delta = (day + 1) % 7; // Saturday as 0
  const copy = new Date(d);
  copy.setDate(d.getDate() - delta);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

export function weekdayFa(d: Date): string {
  // JS: 0 Sunday ... convert to WEEKDAYS_FA Monday-based then Saturday
  const js = d.getDay();
  const python = js === 0 ? 6 : js - 1; // Monday=0
  return WEEKDAYS_FA[python] ?? "";
}

export function formatIsoFa(iso: string, includeTime = true): string {
  const d = new Date(iso);
  const date = d.toLocaleDateString("fa-IR-u-ca-persian", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  if (!includeTime) return `${weekdayFa(d)} ${date}`;
  const time = d.toLocaleTimeString("fa-IR", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${weekdayFa(d)} ${date} ساعت ${time}`;
}

export function formatToman(amount: string | number, unit: string): string {
  const n = Number(amount);
  if (!Number.isFinite(n) || !unit || unit === "unknown") {
    return "مبلغ با واحد نامشخص — قابل استفاده برای مقایسهٔ مالی نیست";
  }
  const toman = unit === "rial" ? n / 10 : n;
  const formatted = toPersianDigits(
    Math.round(toman).toLocaleString("en-US").replace(/,/g, "٬"),
  );
  if (unit === "rial") {
    return `${formatted} تومان (اصل: ${toPersianDigits(String(n))} ریال)`;
  }
  return `${formatted} تومان`;
}
