"use client";

import { useEffect, useRef } from "react";
import { Loader2, X } from "lucide-react";
import type { User } from "@/lib/api";

export function Spinner({ label, size = 16 }: { label?: string; size?: number }) {
  return (
    <span className="inline-flex items-center gap-2" role="status">
      <Loader2 size={size} className="spin" aria-hidden="true" />
      {label ? <span>{label}</span> : <span className="sr-only">Carregando</span>}
    </span>
  );
}

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="flex items-center gap-2.5" aria-label="Automação de Frotas">
      <span aria-hidden="true" className="block h-7 w-[39px] shrink-0 bg-brand-ink" style={{ mask: "url(/brand/frotas-mark.svg) center / contain no-repeat", WebkitMask: "url(/brand/frotas-mark.svg) center / contain no-repeat" }} />
      {!compact && (
        <span className="leading-none">
          <span className="block text-[15px] font-bold tracking-[0.06em] text-ink-2">FROTAS</span>
          <span className="block text-[10px] text-ink-3">Automação de Frotas</span>
        </span>
      )}
    </span>
  );
}

export function Avatar({ user, size = 28 }: { user: Pick<User, "name" | "avatar_version">; size?: number }) {
  const parts = user.name.trim().split(/\s+/).filter(Boolean);
  const initials = ((parts[0]?.[0] ?? "") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
  return (
    <span className="grid shrink-0 place-items-center overflow-hidden rounded-full bg-brand-soft text-[11px] font-semibold text-brand-ink" style={{ width: size, height: size }}>
      {user.avatar_version
        // eslint-disable-next-line @next/next/no-img-element -- foto privada servida pela API com o cookie da sessão
        ? <img src={`/api/workspace/profile/avatar?v=${encodeURIComponent(user.avatar_version)}`} alt="" width={size} height={size} className="h-full w-full object-cover" />
        : initials}
    </span>
  );
}

export function Modal({ title, description, onClose, children, width = 480, footer }: {
  title: string; description?: React.ReactNode; onClose: () => void; children?: React.ReactNode; width?: number; footer?: React.ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const first = ref.current?.querySelector<HTMLElement>("input, select, textarea, button:not([data-close])");
    first?.focus();
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("keydown", onKey); previous?.focus(); };
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div ref={ref} role="dialog" aria-modal="true" aria-label={title} className="rise card flex max-h-[90vh] w-full flex-col shadow-[var(--shadow)]" style={{ maxWidth: width }}>
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div>
            <h2 className="text-[15px] font-semibold">{title}</h2>
            {description && <p className="mt-0.5 text-ink-2">{description}</p>}
          </div>
          <button data-close className="btn btn-ghost btn-icon -mr-2 -mt-1" onClick={onClose} aria-label="Fechar"><X size={16} /></button>
        </div>
        {children && <div className="overflow-auto px-5 py-4">{children}</div>}
        {footer && <div className="flex justify-end gap-2 border-t border-line px-5 py-3">{footer}</div>}
      </div>
    </div>
  );
}

export function ErrorNote({ children }: { children: React.ReactNode }) {
  if (!children) return null;
  return <p role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-danger">{children}</p>;
}

export function PageHeader({ title, description, actions }: { title: string; description?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 border-b border-line bg-surface px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-0.5 text-ink-2">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}
