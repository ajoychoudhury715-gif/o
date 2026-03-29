import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "THE DENTAL BOND",
  description: "Implant & Micro-dentistry Scheduling System",
  icons: {
    icon: "🦷",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
