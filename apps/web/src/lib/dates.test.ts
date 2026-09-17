import { formatIsoFa, formatToman, saturdayStart, toPersianDigits } from "./dates";
import { expect, test } from "vitest";

test("persian digits copy latin source", () => {
  expect(toPersianDigits("10")).toBe("۱۰");
});

test("toman conversion only with known rial unit", () => {
  expect(formatToman("10", "rial")).toContain("تومان");
  expect(formatToman("10", "unknown")).toContain("نامشخص");
});

test("saturday is first day of week helper", () => {
  const thursday = new Date("2026-09-17T12:00:00+03:30");
  const start = saturdayStart(thursday);
  expect(start.getDay()).toBe(6);
});

test("format iso uses persian calendar when available", () => {
  const text = formatIsoFa("2026-09-18T10:00:00+03:30");
  expect(text).toContain("ساعت");
});
