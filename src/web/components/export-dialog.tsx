"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, Download, FileSpreadsheet } from "lucide-react";
import { api, fileUrl, json } from "@/lib/api";
import { excelName } from "@/lib/review";
import { ErrorNote, Modal, Spinner } from "./ui";

type Result = { id: string; version: number; filename: string };

export function ExportDialog({ documentId, filename, issues, onRename, flush, revision, onExported, onClose, onShowIssues }: {
  documentId: string;
  filename: string;
  issues: number;
  onRename: (value: string) => void;
  flush: () => Promise<boolean>;
  revision: () => number;
  onExported: () => void;
  onClose: () => void;
  onShowIssues: () => void;
}) {
  const [name, setName] = useState(filename.replace(/\.xlsx$/i, ""));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Result | null>(null);

  function download(id: string) {
    const link = document.createElement("a");
    link.href = fileUrl(`exports/${id}`);
    link.download = "";
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  async function generate(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const target = excelName(name);
      if (target !== filename) onRename(target);
      if (!(await flush())) throw new Error("Não foi possível salvar as alterações antes de exportar. Confira o aviso no topo da tela.");
      const value = await api<Result>(`documents/${documentId}/exports`, json("POST", { revision: revision() }));
      setResult(value);
      onExported();
      download(value.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível gerar o Excel.");
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <Modal title="Excel gerado" onClose={onClose} width={440}
        footer={<><button className="btn" onClick={() => download(result.id)}><Download size={14} /> Baixar de novo</button><button className="btn btn-primary" onClick={onClose}>Concluir</button></>}>
        <div className="flex gap-3">
          <CheckCircle2 size={22} className="shrink-0 text-ok" />
          <div>
            <p className="font-medium">{result.filename}</p>
            <p className="mt-0.5 text-ink-2">Versão {result.version} guardada no histórico. O download começou.</p>
          </div>
        </div>
      </Modal>
    );
  }

  return (
    <Modal title="Exportar Excel" description="Gera a planilha no layout padrão e guarda esta versão no histórico." onClose={onClose} width={460}>
      <form onSubmit={generate} className="space-y-4">
        <label className="block">
          <span className="label">Nome do arquivo</span>
          <div className="flex items-center rounded-md border border-line-strong bg-surface focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20">
            <FileSpreadsheet size={15} className="ml-2.5 shrink-0 text-ok" />
            <input className="h-9 min-w-0 flex-1 bg-transparent px-2 outline-none focus-visible:outline-none" value={name} onChange={(event) => setName(event.target.value)} required maxLength={150} />
            <span className="pr-3 text-ink-3">.xlsx</span>
          </div>
        </label>
        {issues > 0 && (
          <div className="flex gap-2.5 rounded-md bg-warn-soft p-3 text-warn">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Ainda há {issues} pendência{issues > 1 ? "s" : ""}.</p>
              <p className="mt-0.5 opacity-90">Você pode exportar assim mesmo. Os campos pendentes saem como estão.</p>
              <button type="button" className="mt-1.5 font-medium underline underline-offset-2" onClick={onShowIssues}>Revisar pendências primeiro</button>
            </div>
          </div>
        )}
        <ErrorNote>{error}</ErrorNote>
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? <Spinner label="Gerando" size={14} /> : issues ? "Exportar mesmo assim" : "Gerar Excel"}</button>
        </div>
      </form>
    </Modal>
  );
}
