import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@fontsource/fraunces/600.css";
import "@fontsource/source-sans-3/400.css";
import "@fontsource/source-sans-3/600.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "MCP Server App",
  description: "Chat with the LangGraph agent and run the MCP tools in the browser.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
