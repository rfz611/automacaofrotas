"use client";

import { memo, useEffect, useLayoutEffect, useRef, useState } from "react";
import { FLEET_COLUMNS, type FleetField, type FleetValue, type FleetVehicle } from "@/lib/fleet";
import { MONO, display, draftOf, parseDraft } from "@/lib/review";

export type CellPos = { row: string; col: number };

const GROUPS = [
  { label: "Identificação", span: 2 },
  { label: "Veículo", span: 5 },
  { label: "Bônus e FIPE", span: 2 },
  { label: "Coberturas (R$)", span: 6 },
  { label: "Serviços", span: 1 },
  { label: "Controle", span: 1 },
];
const PIN_LEFT = [0, FLEET_COLUMNS[0].width];
const HEAD_ROW = 28;

type Props = {
  rows: FleetVehicle[];
  allRows: FleetVehicle[];
  active: CellPos | null;
  onActive: (pos: CellPos | null) => void;
  onChange: (id: string, field: FleetField, value: FleetValue) => void;
  readOnly?: boolean;
};

/**
 * Tabela no estilo planilha: setas navegam, Enter ou digitar edita, Enter confirma e desce,
 * Tab confirma e vai para a direita, Esc cancela.
 */
export function FleetGrid({ rows, allRows, active, onActive, onChange, readOnly }: Props) {
  const [editing, setEditing] = useState<{ draft: string; error: string } | null>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const position = new Map(allRows.map((row, index) => [row.id, index + 1]));

  const activeIndex = active ? rows.findIndex((row) => row.id === active.row) : -1;

  useLayoutEffect(() => {
    if (!active) return;
    const cell = wrap.current?.querySelector<HTMLElement>(`[data-cell="${active.row}:${active.col}"]`);
    if (!cell || !wrap.current) return;
    const box = wrap.current.getBoundingClientRect(), rect = cell.getBoundingClientRect();
    const top = box.top + HEAD_ROW * 2, left = box.left + PIN_LEFT[1] + FLEET_COLUMNS[1].width;
    if (rect.top < top) wrap.current.scrollTop -= top - rect.top;
    else if (rect.bottom > box.bottom) wrap.current.scrollTop += rect.bottom - box.bottom;
    if (active.col > 1 && rect.left < left) wrap.current.scrollLeft -= left - rect.left;
    else if (rect.right > box.right) wrap.current.scrollLeft += rect.right - box.right;
  }, [active]);

  function move(dRow: number, dCol: number) {
    if (!rows.length) return;
    const index = Math.max(0, Math.min(rows.length - 1, (activeIndex < 0 ? 0 : activeIndex) + dRow));
    const col = Math.max(0, Math.min(FLEET_COLUMNS.length - 1, (active?.col ?? 0) + dCol));
    onActive({ row: rows[index].id, col });
  }

  function commit(): boolean {
    if (!editing || !active) return true;
    const spec = FLEET_COLUMNS[active.col];
    const row = rows[activeIndex];
    try {
      const value = parseDraft(editing.draft, spec);
      if (row && value !== row[spec.field]) onChange(row.id, spec.field, value);
      setEditing(null);
      wrap.current?.focus();
      return true;
    } catch (cause) {
      setEditing({ ...editing, error: cause instanceof Error ? cause.message : "Valor inválido." });
      return false;
    }
  }

  function startEdit(initial?: string) {
    if (readOnly || !active || activeIndex < 0) return;
    const spec = FLEET_COLUMNS[active.col];
    setEditing({ draft: initial ?? draftOf(rows[activeIndex][spec.field], spec.kind), error: "" });
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (editing) return;
    const keys: Record<string, [number, number]> = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    if (keys[event.key]) { event.preventDefault(); move(...keys[event.key]); return; }
    if (event.key === "Tab") { event.preventDefault(); move(0, event.shiftKey ? -1 : 1); return; }
    if (event.key === "Enter" || event.key === "F2") { event.preventDefault(); startEdit(); return; }
    if ((event.key === "Delete" || event.key === "Backspace") && active && activeIndex >= 0 && !readOnly) {
      event.preventDefault();
      const spec = FLEET_COLUMNS[active.col];
      if (rows[activeIndex][spec.field] != null) onChange(active.row, spec.field, null);
      return;
    }
    if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey && active) { event.preventDefault(); startEdit(event.key); }
  }

  // Sai da edição se a célula ativa mudar por fora (ex.: setas de pendência).
  const activeKey = active ? `${active.row}:${active.col}` : "";
  const lastKey = useRef(activeKey);
  useEffect(() => { if (lastKey.current !== activeKey) { lastKey.current = activeKey; setEditing(null); } }, [activeKey]);

  return (
    <div ref={wrap} tabIndex={0} onKeyDown={onKeyDown} className="relative min-h-0 flex-1 overflow-auto outline-none" aria-label="Veículos da apólice" role="grid">
      <table className="grid-table tabular text-[12.5px]" style={{ width: FLEET_COLUMNS.reduce((sum, col) => sum + col.width, 0) }}>
        <colgroup>{FLEET_COLUMNS.map((col) => <col key={col.field} style={{ width: col.width }} />)}</colgroup>
        <thead className="text-[11px] text-ink-2">
          <tr style={{ height: HEAD_ROW }}>
            {GROUPS.map((group, index) => (
              <th key={group.label} colSpan={group.span} style={{ top: 0, ...(index === 0 ? { left: 0 } : {}) }}
                className={`px-2 text-left font-semibold uppercase tracking-[0.06em] text-ink-3 ${index === 0 ? "pin" : ""}`}>{group.label}</th>
            ))}
          </tr>
          <tr style={{ height: HEAD_ROW }}>
            {FLEET_COLUMNS.map((col, index) => (
              <th key={col.field} scope="col" style={{ top: HEAD_ROW, ...(index < 2 ? { left: PIN_LEFT[index] } : {}) }}
                className={`px-2 font-medium ${col.kind === "text" ? "text-left" : "text-right"} ${index < 2 ? "pin" : ""}`}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <Row key={row.id} row={row} line={position.get(row.id) ?? 0} activeCol={active?.row === row.id ? active.col : -1}
              editing={active?.row === row.id ? editing : null}
              onSelect={(col) => { if (editing && !commit()) return; onActive({ row: row.id, col }); wrap.current?.focus({ preventScroll: true }); }}
              onEdit={(col) => { onActive({ row: row.id, col }); if (!readOnly) setEditing({ draft: draftOf(row[FLEET_COLUMNS[col].field], FLEET_COLUMNS[col].kind), error: "" }); }}
              onDraft={(draft) => setEditing({ draft, error: "" })}
              onEditKey={(event) => {
                if (event.key === "Escape") { event.preventDefault(); setEditing(null); wrap.current?.focus(); }
                if (event.key === "Enter") { event.preventDefault(); if (commit()) move(event.shiftKey ? -1 : 1, 0); }
                if (event.key === "Tab") { event.preventDefault(); if (commit()) move(0, event.shiftKey ? -1 : 1); }
              }}
              onBlurEdit={() => { if (editing && !commit()) setEditing(null); }}
            />
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="px-4 py-10 text-center text-ink-3">Nenhum veículo com esse filtro.</p>}
    </div>
  );
}

const Row = memo(function Row({ row, line, activeCol, editing, onSelect, onEdit, onDraft, onEditKey, onBlurEdit }: {
  row: FleetVehicle; line: number; activeCol: number; editing: { draft: string; error: string } | null;
  onSelect: (col: number) => void; onEdit: (col: number) => void; onDraft: (draft: string) => void;
  onEditKey: (event: React.KeyboardEvent<HTMLInputElement>) => void; onBlurEdit: () => void;
}) {
  return (
    <tr data-current={activeCol >= 0} style={{ height: 30 }}>
      {FLEET_COLUMNS.map((spec, col) => {
        const issues = row.issues?.[spec.field];
        const isActive = activeCol === col;
        const value = display(row[spec.field], spec.kind);
        return (
          <td key={spec.field} data-cell={`${row.id}:${col}`} data-active={isActive} role="gridcell"
            aria-invalid={issues ? true : undefined}
            className={`relative p-0 ${col < 2 ? "pin" : ""} ${issues ? "cell-issue" : ""}`}
            style={col < 2 ? { left: PIN_LEFT[col] } : undefined}>
            {isActive && editing ? (
              <>
                <input autoFocus value={editing.draft} onChange={(event) => onDraft(event.target.value)} onKeyDown={onEditKey} onBlur={onBlurEdit}
                  aria-label={`${spec.label}, linha ${line}`} aria-invalid={!!editing.error}
                  className={`absolute inset-0 h-full w-full bg-surface px-2 outline-none ${spec.kind === "text" ? "" : "text-right"} ${MONO.has(spec.field) ? "font-mono" : ""} ${editing.error ? "ring-2 ring-danger ring-inset" : ""}`} />
                {editing.error && <span className="absolute left-0 top-full z-20 mt-0.5 whitespace-nowrap rounded bg-danger px-2 py-1 text-[11px] text-white shadow">{editing.error}</span>}
              </>
            ) : (
              <button type="button" tabIndex={-1} onMouseDown={(event) => { event.preventDefault(); onSelect(col); }} onDoubleClick={() => onEdit(col)}
                title={issues?.join(" ")}
                className={`block h-[29px] w-full truncate px-2 ${spec.kind === "text" ? "text-left" : "text-right"} ${MONO.has(spec.field) ? "font-mono text-[12px]" : ""} ${value ? "" : "text-ink-3"}`}>
                {value || (issues ? "vazio" : "")}
              </button>
            )}
          </td>
        );
      })}
    </tr>
  );
});
