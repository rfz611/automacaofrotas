/** Cliente da API do workspace (FastAPI). Todas as chamadas passam pelo proxy /api/workspace. */

export type User = {
  id: string;
  name: string;
  email: string;
  role: "admin" | "employee";
  active?: number;
  avatar_version?: string | null;
};

export type DocumentState = "PROCESSANDO" | "EM_REVISAO" | "ERRO";

export type DocumentSummary = {
  id: string;
  name: string;
  insurer: string;
  filename: string;
  revision: number;
  state: DocumentState;
  error: string | null;
  created: number;
  updated: number;
  author: string;
  vehicles: number;
  pending: number;
  exports: number;
  last_export: number | null;
};

export type SavedDocument = {
  id: string;
  name: string;
  insurer: string;
  filename: string;
  revision: number;
  state: DocumentState;
  error: string | null;
  created: number;
  updated: number;
  veiculos: Record<string, unknown>[];
};

export type ExportVersion = { id: string; version: number; revision: number; filename: string; created: number; author: string };
export type HistoryEvent = { action: string; details: string | null; created: number; author: string };
export type DocumentHistory = { exports: ExportVersion[]; events: HistoryEvent[] };

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/workspace/${path}`, { ...init, cache: "no-store" });
  } catch {
    throw new ApiError("Sem conexão com o servidor. Confira se o sistema está ligado e tente de novo.", 0);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data.detail === "string" ? data.detail : "Algo deu errado. Tente novamente.";
    if (response.status === 401 && typeof window !== "undefined" && !path.startsWith("auth/")) {
      window.dispatchEvent(new Event("frotas:session-expired"));
    }
    throw new ApiError(detail, response.status);
  }
  return data as T;
}

export const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const fileUrl = (path: string) => `/api/workspace/${path}`;

const dateFormat = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });
export const formatDate = (seconds: number) => dateFormat.format(new Date(seconds * 1000));

export function relativeDate(seconds: number) {
  const diff = Date.now() / 1000 - seconds;
  if (diff < 60) return "agora";
  if (diff < 3600) return `há ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `há ${Math.floor(diff / 3600)} h`;
  if (diff < 7 * 86400) return `há ${Math.floor(diff / 86400)} d`;
  return formatDate(seconds);
}
