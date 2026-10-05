import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Debugly",
  description:
    "AI-powered coding learning environment that identifies hidden programming misconceptions.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
