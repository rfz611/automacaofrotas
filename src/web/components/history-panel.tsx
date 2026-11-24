"use client";

import { useEffect, useState } from "react";
import { Download, FileSpreadsheet, FileUp, Pencil, ScanText, TriangleAlert } from "lucide-react";
import { api, fileUrl, formatDate, relativeDate, type DocumentHistory } from "@/lib/api";
import { FLEET_COLUMNS, type FleetVehicle } from "@/lib/fleet";
import { ErrorNote, Spinner } from "./ui";

type Change = { vehicle: string; field: string; before: unknown; after: unknown };
const LABEL = Object.fromEntries(FLEET_COLUMNS.map((col) => [col.field, col.label]));
const ICON = { PDF_RECEBIDO: FileUp, EXTRACAO_CONCLUIDA: ScanText, EXTRACAO_FALHOU: TriangleAlert, REVISAO_SALVA: Pencil, EXCEL_GERADO: FileSpreadsheet } as const;

function parse(details: string | null): Record<string, unknown> {
  try { return details ? JSON.parse(details) : {}; } catch { return {}; }
}
const show = (value: unknown) => (value == null || value === "" ? "vazio" : String(value));

export function HistoryPanel({ documentId, rows, refreshKey }: { documentId: string; rows: FleetVehicle[]; refreshKey: number }) {
  const [history, setHistory] = useState<DocumentHistory | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<DocumentHistory>(`documents/${documentId}/history`).then(setHistory).catch((cause) => setError(cause.message));
  }, [documentId, refreshKey]);

  const vehicle = new Map(rows.map((row, index) => [row.id, `Item ${row.item_apolice ?? index + 1}${row.placa ? ` · ${row.placa}` : ""}`]));

  if (error) return <div className="p-4"><ErrorNote>{error}</ErrorNote></div>;
  if (!history) return <div className="grid h-32 place-items-center text-ink-3"><Spinner label="Carregando histórico" /></div>;

  function describe(action: string, details: Record<string, unknown>) {
    switch (action) {
      case "PDF_RECEBIDO": return "importou o PDF";
      case "EXTRACAO_CONCLUIDA": return typeof details.veiculos === "number" ? `Leitura concluída: ${details.veiculos} veículos` : "Leitura concluída";
      case "EXTRACAO_FALHOU": return "A leitura do PDF falhou";
      case "REVISAO_SALVA": return "alterou dados";
      case "EXCEL_GERADO": return `gerou o Excel v${details.version}`;
      default: return action;
    }
  }

  return (
    <div className="space-y-5 p-4">
      <section>
        <h3 className="eyebrow mb-2">Versões do Excel</h3>
        {history.exports.length === 0 ? <p className="text-ink-3">Nenhum Excel gerado ainda.</p> : (
          <ul className="divide-y divide-line rounded-lg border border-line">
            {history.exports.map((item) => (
              <li key={item.id} className="flex items-center gap-3 px-3 py-2">
                <span className="badge badge-brand">v{item.version}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{item.filename}</span>
                  <span className="block text-xs text-ink-3" title={formatDate(item.created)}>{item.author} · {relativeDate(item.created)}</span>
                </span>
                <a className="btn btn-ghost btn-icon btn-sm" href={fileUrl(`exports/${item.id}`)} download aria-label={`Baixar versão ${item.version}`} title="Baixar"><Download size={14} /></a>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3 className="eyebrow mb-2">Atividade</h3>
        <ol className="relative space-y-3 border-l border-line pl-4">
          {history.events.map((item, index) => {
            const details = parse(item.details);
            const Icon = ICON[item.action as keyof typeof ICON] ?? Pencil;
            const changes = (item.action === "REVISAO_SALVA" && Array.isArray(details.changes) ? details.changes : []) as Change[];
            return (
              <li key={index} className="relative">
                <span className="absolute -left-[25px] top-0.5 grid h-[17px] w-[17px] place-items-center rounded-full border border-line bg-surface text-ink-3"><Icon size={10} /></span>
                <p>{item.action.startsWith("EXTRACAO_")
                  ? <span className="text-ink-2">{describe(item.action, details)}</span>
                  : <><span className="font-medium">{item.author}</span> <span className="text-ink-2">{describe(item.action, details)}</span></>}</p>
                <p className="text-xs text-ink-3" title={formatDate(item.created)}>{relativeDate(item.created)}</p>
                {changes.length > 0 && (
                  <ul className="mt-1.5 space-y-1 rounded-md bg-surface-2 p-2 text-xs">
                    {changes.slice(0, 12).map((change, key) => (
                      <li key={key} className="leading-snug">
                        <span className="text-ink-2">{vehicle.get(change.vehicle) ?? "Veículo"} · {LABEL[change.field] ?? change.field}:</span>{" "}
                        <span className="text-ink-3 line-through">{show(change.before)}</span> → <span className="font-medium">{show(change.after)}</span>
                      </li>
                    ))}
                    {changes.length > 12 && <li className="text-ink-3">e mais {changes.length - 12} alterações</li>}
                    {typeof details.filename === "string" && changes.length === 0 && <li>Nome do Excel: {details.filename}</li>}
                  </ul>
                )}
              </li>
            );
          })}
        </ol>
      </section>
    </div>
  );
}
