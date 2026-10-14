import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Orbiq — Satellite Flood Damage Mapping & Hydrodynamic Intelligence",
    template: "%s · Orbiq",
  },
  description:
    "Multi-sensor satellite flood damage mapping, rescue access intelligence, and hydrodynamic dam-break decision system.",
  applicationName: "Orbiq",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: "#0e0e10",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      {/*
        No webfont <link> here. The previous shell pulled the Material Symbols
        variable font from Google on every load — a third-party, render-blocking
        request that duplicated an icon set we already ship. lucide-react is the
        single icon system now.
      */}
      <body className={`${inter.variable} ${jetbrains.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
