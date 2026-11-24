"use client";

import { useRef, useState } from "react";
import { CheckCircle2, FileUp, TriangleAlert, Upload, X } from "lucide-react";
import { api, type SavedDocument } from "@/lib/api";
import { Modal, Spinner } from "./ui";

type Item = { key: string; file: File; status: "fila" | "lendo" | "ok" | "erro"; message?: string; doc?: SavedDocument };

const MAX = 25 * 1024 * 1024;

/** Envia os PDFs um por vez (a leitura é pesada) e mostra o resultado de cada um. */
export function ImportDialog({ onClose, onImported, onOpen }: {
  onClose: () => void;
  onImported: () => void;
  onOpen: (id: string) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [drag, setDrag] = useState(false);
  const [running, setRunning] = useState(false);

  const update = (key: string, patch: Partial<Item>) =>
    setItems((list) => list.map((item) => (item.key === key ? { ...item, ...patch } : item)));

  async function add(files: FileList | File[]) {
    const fresh: Item[] = Array.from(files).map((file) => {
      const key = crypto.randomUUID();
      if (!file.name.toLowerCase().endsWith(".pdf")) return { key, file, status: "erro", message: "Não é um PDF." };
      if (file.size > MAX) return { key, file, status: "erro", message: "Maior que 25 MB." };
      return { key, file, status: "fila" };
    });
    setItems((list) => [...list, ...fresh]);
    const queue = fresh.filter((item) => item.status === "fila");
    if (!queue.length) return;
    setRunning(true);
    for (const item of queue) {
      update(item.key, { status: "lendo" });
      const body = new FormData();
      body.append("file", item.file);
      try {
        const doc = await api<SavedDocument>("documents", { method: "POST", body });
        update(item.key, { status: "ok", doc });
      } catch (cause) {
        update(item.key, { status: "erro", message: cause instanceof Error ? cause.message : "Falha na leitura." });
      }
      onImported();
    }
    setRunning(false);
  }

  const done = items.filter((item) => item.status === "ok");

  return (
    <Modal title="Importar apólices" description="Envie um ou mais PDFs. O sistema identifica a seguradora e lê os veículos." onClose={onClose} width={600}
      footer={<>
        <button className="btn" onClick={onClose}>{running ? "Continuar em segundo plano" : "Fechar"}</button>
        {done.length === 1 && !running && <button className="btn btn-primary" onClick={() => onOpen(done[0].doc!.id)}>Revisar agora</button>}
      </>}>
      <div
        onDragOver={(event) => { event.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(event) => { event.preventDefault(); setDrag(false); add(event.dataTransfer.files); }}
        className={`grid place-items-center rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors ${drag ? "border-brand bg-brand-soft" : "border-line-strong bg-surface-2"}`}>
        <FileUp size={26} className="text-brand-ink" aria-hidden="true" />
        <p className="mt-2 font-medium">Arraste os PDFs para cá</p>
        <p className="text-ink-3">ou</p>
        <button className="btn btn-primary mt-2" onClick={() => input.current?.click()}><Upload size={14} /> Selecionar arquivos</button>
        <input ref={input} type="file" accept="application/pdf,.pdf" multiple hidden
          onChange={(event) => { if (event.target.files) add(event.target.files); event.target.value = ""; }} />
        <p className="mt-3 text-xs text-ink-3">Até 25 MB por arquivo.</p>
      </div>

      {items.length > 0 && (
        <ul className="mt-4 divide-y divide-line rounded-lg border border-line">
          {items.map((item) => (
            <li key={item.key} className="flex items-center gap-3 px-3 py-2.5">
              <span className="w-5 shrink-0 text-center">
                {item.status === "fila" && <span className="inline-block h-2 w-2 rounded-full bg-line-strong" />}
                {item.status === "lendo" && <Spinner size={15} />}
                {item.status === "ok" && <CheckCircle2 size={16} className="text-ok" />}
                {item.status === "erro" && <TriangleAlert size={16} className="text-danger" />}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium">{item.file.name}</span>
                <span className={`block text-xs ${item.status === "erro" ? "text-danger" : "text-ink-3"}`}>
                  {item.status === "fila" && "Aguardando"}
                  {item.status === "lendo" && "Lendo o PDF… pode levar alguns segundos"}
                  {item.status === "ok" && `${item.doc!.insurer || "Seguradora não identificada"} · ${item.doc!.veiculos.length} veículos`}
                  {item.status === "erro" && item.message}
                </span>
              </span>
              {item.status === "ok" && <button className="btn btn-sm" onClick={() => onOpen(item.doc!.id)}>Revisar</button>}
              {item.status === "erro" && <button className="btn btn-ghost btn-icon btn-sm" aria-label="Remover da lista" onClick={() => setItems((list) => list.filter((value) => value.key !== item.key))}><X size={14} /></button>}
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}
