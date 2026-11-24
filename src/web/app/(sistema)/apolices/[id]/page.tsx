"use client";

import { use, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, Check, ChevronDown, ChevronUp, CloudOff, FileSpreadsheet, FileText, History, RefreshCw, Search, X } from "lucide-react";
import { api, ApiError, fileUrl, json, type SavedDocument } from "@/lib/api";
import { FLEET_COLUMNS, type FleetField, type FleetValue, type FleetVehicle } from "@/lib/fleet";
import { countIssues, hasIssues, importVehicles, payload, reviewVehicles } from "@/lib/review";
import { FleetGrid, type CellPos } from "@/components/fleet-grid";
import { HistoryPanel } from "@/components/history-panel";
import { ExportDialog } from "@/components/export-dialog";
import { ErrorNote, Spinner } from "@/components/ui";

type SaveState = "salvo" | "pendente" | "salvando" | "erro" | "conflito";
type Panel = "pdf" | "historico" | null;

export default function Review({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [doc, setDoc] = useState<SavedDocument | null>(null);
  const [loadError, setLoadError] = useState("");
  const [rows, setRows] = useState<FleetVehicle[]>([]);
  const [filename, setFilename] = useState("");
  const [save, setSave] = useState<{ state: SaveState; message?: string }>({ state: "salvo" });
  const [panel, setPanel] = useState<Panel>(null);
  const [panelWidth, setPanelWidth] = useState(520);
  const [onlyIssues, setOnlyIssues] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<CellPos | null>(null);
  const [exporting, setExporting] = useState(false);
  const [historyKey, setHistoryKey] = useState(0);

  const latest = useRef({ rows, filename, revision: 0 });
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlight = useRef<Promise<boolean> | null>(null);
  const dirty = useRef(false);

  const load = useCallback(async () => {
    setLoadError("");
    try {
      const value = await api<SavedDocument>(`documents/${id}`);
      const reviewed = reviewVehicles(importVehicles(value.veiculos));
      latest.current = { rows: reviewed, filename: value.filename, revision: value.revision };
      dirty.current = false;
      setDoc(value); setRows(reviewed); setFilename(value.filename); setSave({ state: "salvo" });
    } catch (cause) {
      setLoadError(cause instanceof Error ? cause.message : "Não foi possível abrir a apólice.");
    }
  }, [id]);
  useEffect(() => { load(); }, [load]); // eslint-disable-line react-hooks/set-state-in-effect

  /** Envia o estado mais recente. Retorna true quando tudo está salvo. */
  const flush = useCallback(async (): Promise<boolean> => {
    if (timer.current) { clearTimeout(timer.current); timer.current = null; }
    if (inFlight.current) await inFlight.current;
    // Repete enquanto houver edições feitas durante o envio anterior.
    while (dirty.current) {
      dirty.current = false;
      const snapshot = latest.current;
      setSave({ state: "salvando" });
      const run = (async () => {
        try {
          const result = await api<{ revision: number }>(`documents/${id}`, json("PUT", { revision: snapshot.revision, filename: snapshot.filename, veiculos: payload(snapshot.rows) }));
          latest.current = { ...latest.current, revision: result.revision };
          setHistoryKey((value) => value + 1);
          if (!dirty.current) setSave({ state: "salvo" });
          return true;
        } catch (cause) {
          dirty.current = true;
          if (cause instanceof ApiError && cause.status === 409) setSave({ state: "conflito", message: cause.message });
          else setSave({ state: "erro", message: cause instanceof Error ? cause.message : "Falha ao salvar." });
          return false;
        }
      })();
      inFlight.current = run;
      const ok = await run;
      inFlight.current = null;
      if (!ok) return false;
    }
    return true;
  }, [id]);

  const schedule = useCallback(() => {
    dirty.current = true;
    setSave((current) => (current.state === "conflito" ? current : { state: "pendente" }));
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { if (latest.current) flush(); }, 900);
  }, [flush]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (dirty.current) event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => { window.removeEventListener("beforeunload", warn); if (dirty.current) flush(); };
  }, [flush]);

  const change = useCallback((rowId: string, field: FleetField, value: FleetValue) => {
    const next = reviewVehicles(latest.current.rows.map((row) => row.id !== rowId ? row : {
      ...row, [field]: value,
      // Um aviso do leitor some quando o funcionário corrige o campo.
      flags_atencao: row.flags_atencao.filter((flag) => flag !== field && !flag.startsWith(`${field}_`)),
    }));
    latest.current = { ...latest.current, rows: next };
    setRows(next);
    schedule();
  }, [schedule]);

  const renameExcel = useCallback((value: string) => {
    latest.current = { ...latest.current, filename: value };
    setFilename(value);
    schedule();
  }, [schedule]);

  const issues = useMemo(() => countIssues(rows), [rows]);
  const issueCells = useMemo(() => rows.flatMap((row) => FLEET_COLUMNS.flatMap((spec, col) => row.issues?.[spec.field] ? [{ row: row.id, col }] : [])), [rows]);
  const visible = useMemo(() => {
    const term = query.trim().toUpperCase().replace(/[\s-]/g, "");
    return rows.filter((row) => (!onlyIssues || hasIssues(row) || row.id === active?.row)
      && (!term || [row.placa, row.chassi, row.item_apolice, row.modelo, row.marca].some((value) => String(value ?? "").toUpperCase().replace(/[\s-]/g, "").includes(term))));
  }, [rows, onlyIssues, query, active?.row]);

  function jump(step: 1 | -1) {
    if (!issueCells.length) return;
    const order = new Map(rows.map((row, index) => [row.id, index]));
    const current = active ? (order.get(active.row) ?? 0) * 100 + active.col : -1;
    const keyed = issueCells.map((cell) => ({ cell, key: (order.get(cell.row) ?? 0) * 100 + cell.col }));
    const target = step === 1
      ? keyed.find((item) => item.key > current) ?? keyed[0]
      : [...keyed].reverse().find((item) => item.key < current) ?? keyed[keyed.length - 1];
    if (query && !visible.some((row) => row.id === target.cell.row)) setQuery("");
    setActive(target.cell);
  }

  function startResize(event: React.PointerEvent) {
    event.preventDefault();
    const startX = event.clientX, startWidth = panelWidth;
    const moveTo = (move: PointerEvent) => setPanelWidth(Math.max(320, Math.min(window.innerWidth - 480, startWidth + startX - move.clientX)));
    const stop = () => { window.removeEventListener("pointermove", moveTo); window.removeEventListener("pointerup", stop); };
    window.addEventListener("pointermove", moveTo);
    window.addEventListener("pointerup", stop);
  }

  if (loadError) return <div className="p-6"><ErrorNote>{loadError}</ErrorNote><Link href="/" className="btn mt-4"><ArrowLeft size={14} /> Voltar para apólices</Link></div>;
  if (!doc) return <div className="grid flex-1 place-items-center text-ink-3"><Spinner label="Abrindo apólice" /></div>;

  const activeRow = active ? rows.find((row) => row.id === active.row) : undefined;
  const activeSpec = active ? FLEET_COLUMNS[active.col] : undefined;
  const activeIssues = activeRow && activeSpec ? activeRow.issues?.[activeSpec.field] : undefined;

  return (
    <>
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line bg-surface px-4 py-2.5">
        <Link href="/" className="btn btn-ghost btn-icon" aria-label="Voltar para apólices" title="Voltar"><ArrowLeft size={16} /></Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-[15px] font-semibold" title={doc.name}>{doc.name}</h1>
          <p className="text-xs text-ink-3">{doc.insurer || "Seguradora não identificada"} · {rows.length} veículos</p>
        </div>
        <SaveIndicator state={save.state} />
        <div className="flex items-center gap-1 rounded-md border border-line p-0.5">
          <button onClick={() => jump(-1)} disabled={!issues} className="btn btn-ghost btn-icon btn-sm" aria-label="Pendência anterior" title="Pendência anterior"><ChevronUp size={15} /></button>
          <button onClick={() => setOnlyIssues((value) => !value)} disabled={!issues && !onlyIssues}
            className={`badge ${issues ? "badge-warn" : "badge-ok"} h-6 cursor-pointer px-2.5 ${onlyIssues ? "ring-1 ring-warn" : ""}`} title={onlyIssues ? "Mostrar todos os veículos" : "Mostrar só os veículos com pendência"}>
            {issues ? <><AlertTriangle size={12} /> {issues} pendência{issues > 1 ? "s" : ""}</> : <><Check size={12} /> Sem pendências</>}
          </button>
          <button onClick={() => jump(1)} disabled={!issues} className="btn btn-ghost btn-icon btn-sm" aria-label="Próxima pendência" title="Próxima pendência"><ChevronDown size={15} /></button>
        </div>
        <div className="flex items-center gap-1.5">
          <button className={`btn ${panel === "pdf" ? "bg-brand-soft text-brand-ink" : ""}`} onClick={() => setPanel(panel === "pdf" ? null : "pdf")} aria-pressed={panel === "pdf"}><FileText size={14} /> PDF</button>
          <button className={`btn ${panel === "historico" ? "bg-brand-soft text-brand-ink" : ""}`} onClick={() => setPanel(panel === "historico" ? null : "historico")} aria-pressed={panel === "historico"}><History size={14} /> Histórico</button>
          <button className="btn btn-primary" onClick={() => setExporting(true)}><FileSpreadsheet size={14} /> Exportar Excel</button>
        </div>
      </header>

      {(save.state === "conflito" || save.state === "erro") && (
        <div className={`flex items-center gap-3 border-b px-4 py-2 ${save.state === "conflito" ? "border-warn/30 bg-warn-soft text-warn" : "border-danger/30 bg-danger-soft text-danger"}`} role="alert">
          {save.state === "conflito" ? <AlertTriangle size={15} /> : <CloudOff size={15} />}
          <span className="flex-1">{save.state === "conflito" ? "Outra pessoa salvou esta apólice enquanto você editava. Recarregue para ver a versão atual (suas últimas alterações não salvas serão descartadas)." : save.message}</span>
          {save.state === "conflito"
            ? <button className="btn btn-sm" onClick={load}><RefreshCw size={13} /> Recarregar</button>
            : <button className="btn btn-sm" onClick={flush}><RefreshCw size={13} /> Tentar de novo</button>}
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <section className="flex min-w-0 flex-1 flex-col bg-surface">
          <div className="flex items-center gap-2 border-b border-line px-3 py-2">
            <div className="relative w-64">
              <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-3" />
              <input className="field h-7 pl-8 text-xs" placeholder="Placa, chassi, item ou modelo" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Buscar veículo" />
              {query && <button className="absolute right-1.5 top-1/2 -translate-y-1/2 text-ink-3 hover:text-ink" onClick={() => setQuery("")} aria-label="Limpar busca"><X size={13} /></button>}
            </div>
            <label className="flex cursor-pointer items-center gap-1.5 text-xs text-ink-2">
              <input type="checkbox" checked={onlyIssues} onChange={(event) => setOnlyIssues(event.target.checked)} className="accent-[var(--brand)]" /> Só com pendência
            </label>
            <span className="ml-auto text-xs text-ink-3">{visible.length === rows.length ? `${rows.length} veículos` : `${visible.length} de ${rows.length} veículos`}</span>
          </div>
          <FleetGrid rows={visible} allRows={rows} active={active} onActive={setActive} onChange={change} />
          <footer className="flex h-8 items-center gap-3 border-t border-line bg-surface-2 px-3 text-xs text-ink-2">
            {activeRow && activeSpec ? (
              <>
                <span className="font-medium text-ink">Linha {rows.indexOf(activeRow) + 1} · {activeSpec.label}</span>
                {activeIssues ? <span className="marker truncate px-1">{activeIssues.join(" ")}</span> : <span className="text-ink-3">Sem pendência</span>}
              </>
            ) : <span className="text-ink-3">Clique numa célula ou use as setas. Enter ou digitar edita; Enter confirma; Esc cancela.</span>}
          </footer>
        </section>

        {panel && (
          <aside className="relative flex shrink-0 flex-col border-l border-line bg-surface" style={{ width: panelWidth }}>
            <div onPointerDown={startResize} className="absolute -left-1 top-0 z-10 h-full w-2 cursor-col-resize hover:bg-brand/20" aria-hidden="true" />
            <div className="flex h-10 items-center justify-between border-b border-line px-3">
              <span className="font-medium">{panel === "pdf" ? "PDF original" : "Histórico e versões"}</span>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setPanel(null)} aria-label="Fechar painel"><X size={14} /></button>
            </div>
            <div className="min-h-0 flex-1 overflow-auto">
              {panel === "pdf"
                ? <iframe src={fileUrl(`documents/${id}/pdf`)} title="PDF original da apólice" className="h-full w-full border-0 bg-surface-2" />
                : <HistoryPanel documentId={id} rows={rows} refreshKey={historyKey} />}
            </div>
          </aside>
        )}
      </div>

      {exporting && (
        <ExportDialog documentId={id} filename={filename} issues={issues} onRename={renameExcel} flush={flush}
          onExported={() => setHistoryKey((value) => value + 1)}
          revision={() => latest.current.revision}
          onClose={() => setExporting(false)} onShowIssues={() => { setExporting(false); setOnlyIssues(true); jump(1); }} />
      )}
    </>
  );
}

function SaveIndicator({ state }: { state: SaveState }) {
  const map = {
    salvo: { text: "Salvo", icon: <Check size={13} />, tone: "text-ok" },
    pendente: { text: "Alterações não salvas", icon: <span className="h-1.5 w-1.5 rounded-full bg-warn" />, tone: "text-ink-3" },
    salvando: { text: "Salvando…", icon: <Spinner size={12} />, tone: "text-ink-3" },
    erro: { text: "Não salvo", icon: <CloudOff size={13} />, tone: "text-danger" },
    conflito: { text: "Conflito", icon: <AlertTriangle size={13} />, tone: "text-warn" },
  }[state];
  return <span className={`flex items-center gap-1.5 text-xs ${map.tone}`} aria-live="polite">{map.icon} {map.text}</span>;
}
