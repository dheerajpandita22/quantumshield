import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuantumShield Attack Lab",
  description: "Authorized Quantum-Assisted Cybersecurity Simulation Environment",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
