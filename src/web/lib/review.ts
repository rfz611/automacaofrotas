import { FLEET_COLUMNS, type ColumnSpec, type FleetField, type FleetValue, type FleetVehicle } from "./fleet";

/**
 * Regras de conferência. As mesmas regras existem em src/workspace/review.py
 * (usadas para o contador de pendências da lista); mantenha as duas iguais.
 */
export const REQUIRED = new Set<FleetField>(["item_apolice", "placa", "marca", "modelo", "ano_fabricacao", "ano_modelo", "chassi", "classe_bonus"]);
export const MONO = new Set<FleetField>(["placa", "chassi", "codigo_fipe", "codigo_identificacao"]);

const text = (value: FleetValue) => String(value ?? "").trim();
const key = (value: FleetValue) => text(value).toUpperCase().replace(/[\s-]/g, "");

export function importVehicles(rows: Record<string, unknown>[]): FleetVehicle[] {
  return rows.map((row) => ({
    ...Object.fromEntries(FLEET_COLUMNS.map(({ field }) => [field,
      typeof row[field] === "string" || typeof row[field] === "number" ? row[field] : null])),
    id: typeof row.id === "string" ? row.id : crypto.randomUUID(),
    flags_atencao: Array.isArray(row.flags_atencao) ? row.flags_atencao.filter((flag): flag is string => typeof flag === "string") : [],
  }) as FleetVehicle);
}

/** Recalcula as pendências da frota inteira (duplicidade depende de todas as linhas). */
export function reviewVehicles(rows: FleetVehicle[]): FleetVehicle[] {
  const seen = new Map<string, number[]>();
  rows.forEach((row, index) => {
    for (const field of ["item_apolice", "placa", "chassi"] as const) {
      const value = key(row[field]);
      if (value) seen.set(`${field}:${value}`, [...(seen.get(`${field}:${value}`) ?? []), index + 1]);
    }
  });
  const maxYear = new Date().getFullYear() + 1;
  return rows.map((row, index) => {
    const issues: Partial<Record<FleetField, string[]>> = {};
    const add = (field: FleetField, message: string) => { (issues[field] ??= []).push(message); };
    for (const spec of FLEET_COLUMNS) {
      const value = text(row[spec.field]);
      if (!value) {
        if (REQUIRED.has(spec.field)) add(spec.field, "Campo obrigatório vazio.");
        continue;
      }
      if (spec.kind === "integer" && !/^\d+$/.test(value)) { add(spec.field, "Use apenas números inteiros."); continue; }
      if (spec.kind === "money" && !/^\d+(?:\.\d{1,2})?$/.test(value)) { add(spec.field, "Valor monetário inválido."); continue; }
      if (spec.field === "placa" && !/^[A-Z]{3}(?:\d{4}|\d[A-Z]\d{2})$/.test(key(value))) add(spec.field, "Placa fora do padrão (ABC1234 ou ABC1D23).");
      if (spec.field === "chassi" && !/^[A-Z0-9]{17}$/i.test(value)) add(spec.field, `O chassi precisa ter 17 caracteres; tem ${value.length}.`);
      if (spec.field === "classe_bonus" && Number(value) > 10) add(spec.field, "A classe de bônus vai de 0 a 10.");
      if ((spec.field === "ano_fabricacao" || spec.field === "ano_modelo") && (Number(value) < 1960 || Number(value) > maxYear)) add(spec.field, "Ano fora do esperado.");
      if (spec.field === "item_apolice" && Number(value) !== index + 1) add(spec.field, `Item fora de sequência (posição ${index + 1}).`);
    }
    const fab = Number(text(row.ano_fabricacao)), mod = Number(text(row.ano_modelo));
    if (fab && mod && (mod < fab || mod > fab + 1)) add("ano_modelo", "Ano modelo incompatível com o ano de fabricação.");
    for (const field of ["item_apolice", "placa", "chassi"] as const) {
      const lines = seen.get(`${field}:${key(row[field])}`) ?? [];
      if (lines.length > 1) add(field, `Repetido nas linhas ${lines.join(", ")}.`);
    }
    for (const flag of row.flags_atencao) {
      const spec = FLEET_COLUMNS.find(({ field }) => flag === field || flag.startsWith(`${field}_`));
      if (spec && !REQUIRED.has(spec.field)) add(spec.field, "O leitor do PDF marcou este valor para conferência.");
    }
    return { ...row, issues };
  });
}

export const countIssues = (rows: FleetVehicle[]) =>
  rows.reduce((total, row) => total + Object.keys(row.issues ?? {}).length, 0);

export const hasIssues = (row: FleetVehicle) => Object.keys(row.issues ?? {}).length > 0;

const money = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function display(value: FleetValue, kind: ColumnSpec["kind"]) {
  if (value == null || value === "") return "";
  const numeric = Number(value);
  return kind === "money" && Number.isFinite(numeric) ? money.format(numeric) : String(value);
}

/** Texto que aparece no campo quando a célula entra em edição. */
export function draftOf(value: FleetValue, kind: ColumnSpec["kind"]) {
  if (value == null) return "";
  return kind === "money" ? display(value, kind) : String(value);
}

/** Converte o que o funcionário digitou para o valor salvo. Lança erro com mensagem amigável. */
export function parseDraft(raw: string, spec: ColumnSpec): FleetValue {
  const value = raw.trim();
  if (!value) return null;
  if (spec.kind === "text") {
    if (spec.field === "placa") return value.toUpperCase().replace(/[-\s]/g, "");
    if (spec.field === "chassi") return value.toUpperCase().replace(/\s/g, "");
    return value;
  }
  if (spec.kind === "integer") {
    if (!/^\d+$/.test(value)) throw new Error("Use só números inteiros.");
    return Number(value);
  }
  const normalized = /,/.test(value) ? value.replace(/\./g, "").replace(",", ".") : value;
  if (!/^\d+(?:\.\d{1,2})?$/.test(normalized)) throw new Error("Use o formato 1.234,56.");
  const number = Number(normalized);
  if (!Number.isSafeInteger(Math.round(number * 100))) throw new Error("Valor muito alto.");
  return number;
}

export function payload(rows: FleetVehicle[]) {
  return rows.map(({ issues: _issues, ...row }) => row); // eslint-disable-line @typescript-eslint/no-unused-vars
}

export function excelName(name: string) {
  const base = name.replace(/(?:\.xlsx)+$/i, "").replace(/[<>:"/\\|?*\u0000-\u001f]/g, "_").replace(/[.\s]+$/g, "").trim().slice(0, 150);
  return `${base || "frota"}.xlsx`;
}
