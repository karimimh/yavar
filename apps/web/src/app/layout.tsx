import type { Metadata, Viewport } from "next";
import { Vazirmatn } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const vazir = Vazirmatn({
  variable: "--font-vazirmatn",
  subsets: ["arabic", "latin"],
});

export const metadata: Metadata = {
  title: "یاور",
  description:
    "بگو چه کاری داری؛ پیداش می‌کنم، آماده‌اش می‌کنم و با تأیید تو، کارهای پشتیبانی‌شده را انجام می‌دهم.",
  applicationName: "یاور",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "یاور" },
};

export const viewport: Viewport = {
  themeColor: "#111111",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fa" dir="rtl" className={`${vazir.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
