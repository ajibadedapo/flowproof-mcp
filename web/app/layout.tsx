import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FlowProof",
  description: "Reproducible bioinformatics pipelines over MCP. Manage your access keys.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
