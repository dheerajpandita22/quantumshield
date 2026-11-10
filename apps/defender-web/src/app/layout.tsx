import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QuantumShield Defender",
  description: "Quantum-Assisted Cybersecurity Monitoring and Protection Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
