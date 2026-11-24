"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, RefreshCw, Search, Upload } from "lucide-react";
import { api, formatDate, relativeDate, type DocumentSummary } from "@/lib/api";
import { COMPANY } from "@/lib/brand";
import { ImportDialog } from "@/components/import-dialog";
import { ErrorNote, PageHeader, Spinner } from "@/components/ui";

type Filter = "todas" | "pendencias" | "prontas" | "exportadas" | "erro";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "todas", label: "Todas" },
  { value: "pendencias", label: "Com pendências" },
  { value: "prontas", label: "Prontas para exportar" },
  { value: "exportadas", label: "Exportadas" },
  { value: "erro", label: "Com erro" },
];

function status(doc: DocumentSummary) {
  if (doc.state === "PROCESSANDO") return { label: "Lendo PDF", tone: "badge-brand" };
  if (doc.state === "ERRO") return { label: "Erro na leitura", tone: "badge-danger" };
  if (doc.pending > 0) return { label: `${doc.pending} pendência${doc.pending > 1 ? "s" : ""}`, tone: "badge-warn" };
  if (doc.exports > 0) return { label: "Exportada", tone: "badge-ok" };
  return { label: "Pronta", tone: "badge-neutral" };
}

function matches(doc: DocumentSummary, filter: Filter) {
  switch (filter) {
    case "pendencias": return doc.state === "EM_REVISAO" && doc.pending > 0;
    case "prontas": return doc.state === "EM_REVISAO" && doc.pending === 0;
    case "exportadas": return doc.exports > 0;
    case "erro": return doc.state === "ERRO";
    default: return true;
  }
}

export default function Apolices() {
  const router = useRouter();
  const [docs, setDocs] = useState<DocumentSummary[] | null>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("todas");
  const [insurer, setInsurer] = useState("");
  const [importing, setImporting] = useState(false);

  const load = useCallback(async () => {
    try { setDocs(await api<DocumentSummary[]>("documents")); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível carregar as apólices."); }
  }, []);
  useEffect(() => { load(); }, [load]); // eslint-disable-line react-hooks/set-state-in-effect

  const insurers = useMemo(() => [...new Set((docs ?? []).map((doc) => doc.insurer).filter(Boolean))].sort(), [docs]);
  const counts = useMemo(() => Object.fromEntries(FILTERS.map(({ value }) => [value, (docs ?? []).filter((doc) => matches(doc, value)).length])), [docs]);
  const visible = useMemo(() => {
    const term = query.trim().toLowerCase();
    return (docs ?? []).filter((doc) => matches(doc, filter) && (!insurer || doc.insurer === insurer)
      && (!term || `${doc.name} ${doc.insurer} ${doc.filename} ${doc.author}`.toLowerCase().includes(term)));
  }, [docs, filter, insurer, query]);

  return (
    <>
      <PageHeader title="Apólices" description={`Importe o PDF da seguradora, confira os veículos e gere o Excel no padrão ${COMPANY}.`}
        actions={<button className="btn btn-primary" onClick={() => setImporting(true)}><Upload size={15} /> Importar PDF</button>} />

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden p-6">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-72">
            <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-3" />
            <input className="field h-8 pl-8" placeholder="Buscar por arquivo, seguradora ou autor" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Buscar apólices" />
          </div>
          <div className="flex flex-wrap gap-1" role="tablist" aria-label="Filtrar por situação">
            {FILTERS.map(({ value, label }) => (
              <button key={value} role="tab" aria-selected={filter === value} onClick={() => setFilter(value)}
                className={`h-8 rounded-md px-2.5 text-xs font-medium ${filter === value ? "bg-brand-soft text-brand-ink" : "text-ink-2 hover:bg-surface-2"}`}>
                {label} <span className="tabular ml-1 text-ink-3">{docs ? counts[value] : ""}</span>
              </button>
            ))}
          </div>
          {insurers.length > 1 && (
            <select className="field h-8 w-auto" value={insurer} onChange={(event) => setInsurer(event.target.value)} aria-label="Seguradora">
              <option value="">Todas as seguradoras</option>
              {insurers.map((name) => <option key={name}>{name}</option>)}
            </select>
          )}
          <button className="btn btn-ghost btn-icon ml-auto" onClick={load} aria-label="Atualizar lista" title="Atualizar"><RefreshCw size={14} /></button>
        </div>

        <ErrorNote>{error}</ErrorNote>

        <div className="card min-h-0 flex-1 overflow-auto">
          {docs === null && !error ? (
            <div className="grid h-40 place-items-center text-ink-3"><Spinner label="Carregando apólices" /></div>
          ) : docs && docs.length === 0 ? (
            <div className="grid place-items-center px-6 py-20 text-center">
              <span className="grid h-12 w-12 place-items-center rounded-full bg-brand-soft text-brand-ink"><FileText size={22} /></span>
              <h2 className="mt-4 text-[15px] font-semibold">Nenhuma apólice ainda</h2>
              <p className="mt-1 max-w-sm text-ink-2">Importe o PDF de uma seguradora para começar. Você pode enviar vários de uma vez.</p>
              <button className="btn btn-primary mt-4" onClick={() => setImporting(true)}><Upload size={15} /> Importar PDF</button>
            </div>
          ) : (
            <table className="w-full text-left">
              <thead className="sticky top-0 z-10 bg-surface-2 text-xs text-ink-2">
                <tr className="[&>th]:border-b [&>th]:border-line [&>th]:px-4 [&>th]:py-2 [&>th]:font-medium">
                  <th>Arquivo</th><th>Seguradora</th><th className="text-right">Veículos</th><th>Situação</th><th>Última alteração</th><th>Excel</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((doc) => {
                  const badge = status(doc);
                  return (
                    <tr key={doc.id} onClick={() => doc.state !== "ERRO" && router.push(`/apolices/${doc.id}`)}
                      className={`border-b border-line [&>td]:px-4 [&>td]:py-2.5 ${doc.state === "ERRO" ? "" : "cursor-pointer hover:bg-surface-2"}`}>
                      <td className="max-w-[360px]">
                        {doc.state === "ERRO"
                          ? <span className="block truncate font-medium">{doc.name}</span>
                          : <a href={`/apolices/${doc.id}`} onClick={(event) => event.preventDefault()} className="block truncate font-medium hover:text-brand-ink">{doc.name}</a>}
                        {doc.state === "ERRO" && doc.error && <span className="block truncate text-xs text-danger">{doc.error}</span>}
                      </td>
                      <td className="text-ink-2">{doc.insurer || "—"}</td>
                      <td className="tabular text-right">{doc.vehicles || "—"}</td>
                      <td><span className={`badge ${badge.tone}`}>{badge.label}</span></td>
                      <td className="text-ink-2" title={formatDate(doc.updated)}>{relativeDate(doc.updated)} · {doc.author}</td>
                      <td className="text-ink-2">{doc.exports ? <span title={doc.last_export ? formatDate(doc.last_export) : ""}>v{doc.exports} · {relativeDate(doc.last_export!)}</span> : "—"}</td>
                    </tr>
                  );
                })}
                {visible.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-12 text-center text-ink-3">Nenhuma apólice com esses filtros.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {importing && <ImportDialog onClose={() => setImporting(false)} onImported={load} onOpen={(id) => router.push(`/apolices/${id}`)} />}
    </>
  );
}
