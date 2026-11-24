import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "./globals.css";
import { DEMO } from "@/lib/brand";

export const metadata: Metadata = {
  title: DEMO ? "Automação de Frotas · demonstração" : "Automação de Frotas",
  description: "Leitura de apólices de frota em PDF e geração da planilha padrão.",
};

/** Aplica o tema antes da primeira pintura para não piscar. */
const themeScript = `try{var t=localStorage.getItem("frotas-tema")||"system";var d=t==="dark"||(t==="system"&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.dataset.theme=d?"dark":"light"}catch(e){}`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
      <body>{children}</body>
    </html>
  );
}
