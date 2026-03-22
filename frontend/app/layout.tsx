import type { Metadata } from "next";
import "./globals.css";
import { Navigation } from "@/components/Navigation";

export const metadata: Metadata = {
  title: "Algo Trading Bot",
  description: "Algorithmic trading dashboard with strategy execution and backtesting"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <Navigation />
          {children}
        </div>
      </body>
    </html>
  );
}
