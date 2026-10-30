import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocuMind AI — Evidence-Grounded Document Intelligence Platform",
  description: "Enterprise Document Intelligence, Hybrid RAG with Reciprocal Rank Fusion, Claim-Level Evidence Verification, and Contradiction Intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090D16] text-slate-100 antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
        {children}
      </body>
    </html>
  );
}
