"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight, FileSpreadsheet, FileText, ShieldCheck } from "lucide-react";
import { api, json } from "@/lib/api";
import { COMPANY, DEMO } from "@/lib/brand";
import { ErrorNote, Logo, Spinner } from "@/components/ui";

export default function Page() {
  return <Suspense><Login /></Suspense>;
}

function Login() {
  const router = useRouter();
  const params = useSearchParams();
  const [setup, setSetup] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(params.get("expirou") ? "Sua sessão expirou. Entre novamente; o trabalho salvo continua lá." : "");

  useEffect(() => {
    api<{ setup_required: boolean }>("auth/status")
      .then((value) => setSetup(value.setup_required))
      .catch((cause) => { setSetup(false); setError(cause.message); });
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    setError("");
    if (setup && data.password !== data.confirm) { setError("A confirmação não é igual à senha."); return; }
    setBusy(true);
    try {
      await api(setup ? "auth/setup" : "auth/login", json("POST", setup
        ? { name: data.name, email: data.email, password: data.password }
        : { email: data.email, password: data.password }));
      const back = params.get("voltar");
      router.replace(back && back.startsWith("/") && !back.startsWith("//") ? back : "/");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível entrar.");
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_minmax(440px,520px)]">
      <section className="relative hidden overflow-hidden bg-[#000063] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -right-24 -top-24 h-[520px] w-[520px] rounded-full border border-white/10" />
        <div className="pointer-events-none absolute -right-8 top-40 h-[360px] w-[360px] rounded-full border border-white/10" />
        <div className="flex items-center gap-3">
          <span aria-hidden="true" className="block h-10 w-14 bg-white" style={{ mask: "url(/brand/frotas-mark.svg) center / contain no-repeat", WebkitMask: "url(/brand/frotas-mark.svg) center / contain no-repeat" }} />
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/60">{DEMO ? "Frotas · Demonstração" : "Frotas · Sistema interno"}</p>
        </div>
        <div className="max-w-md">
          <h1 className="text-[34px] font-semibold leading-tight tracking-tight">Do PDF da seguradora à planilha padrão, sem digitar veículo por veículo.</h1>
          <ul className="mt-8 space-y-4 text-[14px] text-white/80">
            <li className="flex gap-3"><FileText size={18} className="mt-0.5 shrink-0" /> O sistema reconhece a seguradora e lê todos os veículos da apólice.</li>
            <li className="flex gap-3"><ShieldCheck size={18} className="mt-0.5 shrink-0" /> O que precisa de conferência fica marcado, com o PDF original ao lado.</li>
            <li className="flex gap-3"><FileSpreadsheet size={18} className="mt-0.5 shrink-0" /> O Excel sai no layout {COMPANY}, com cada versão guardada.</li>
          </ul>
        </div>
        <p className="text-xs text-white/50">Layouts validados: Porto Seguro · Bradesco · Sura</p>
      </section>

      <section className="flex flex-col justify-center bg-surface px-8 py-12 sm:px-14">
        <div className="mx-auto w-full max-w-sm">
          <Logo />
          {setup === null ? (
            <div className="mt-12 text-ink-3"><Spinner label="Carregando" /></div>
          ) : (
            <form onSubmit={submit} className="mt-10 space-y-4">
              <div>
                <h2 className="text-xl font-semibold tracking-tight">{setup ? "Criar o administrador" : "Entrar"}</h2>
                <p className="mt-1 text-ink-2">{setup
                  ? "Primeiro acesso. Esta conta vai cadastrar os demais funcionários."
                  : "Use o e-mail e a senha cadastrados pelo administrador."}</p>
              </div>
              {setup && <label className="block"><span className="label">Nome</span><input className="field h-10" name="name" autoComplete="name" minLength={2} required /></label>}
              <label className="block"><span className="label">E-mail</span><input className="field h-10" name="email" type="email" autoComplete="username" required defaultValue={DEMO && !setup ? "demo@frotas.local" : undefined} /></label>
              <label className="block"><span className="label">Senha</span><input className="field h-10" name="password" type="password" autoComplete={setup ? "new-password" : "current-password"} minLength={setup ? 12 : 1} required /></label>
              {setup && <label className="block"><span className="label">Repita a senha</span><input className="field h-10" name="confirm" type="password" autoComplete="new-password" minLength={12} required /></label>}
              {setup && <p className="text-xs text-ink-3">Mínimo de 12 caracteres.</p>}
              <ErrorNote>{error}</ErrorNote>
              <button className="btn btn-primary h-10 w-full" disabled={busy}>
                {busy ? <Spinner /> : <>{setup ? "Criar e entrar" : "Entrar"} <ArrowRight size={15} /></>}
              </button>
              {!setup && <p className="text-xs text-ink-3">Esqueceu a senha? Peça ao administrador ou rode <code className="font-mono">redefinir-senha.bat</code> no computador do sistema.</p>}
            </form>
          )}
        </div>
      </section>
    </div>
  );
}
