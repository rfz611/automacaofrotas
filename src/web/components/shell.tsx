"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronsLeft, ChevronsRight, FileStack, LogOut, Monitor, Moon, Sun, UserRound, Users } from "lucide-react";
import { useTheme, type ThemePreference } from "@/lib/theme";
import { DEMO } from "@/lib/brand";
import { useSession } from "./session";
import { Avatar, Logo } from "./ui";
import { ProfileDialog } from "./profile";

const THEMES: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Claro", icon: Sun },
  { value: "dark", label: "Escuro", icon: Moon },
  { value: "system", label: "Sistema", icon: Monitor },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useSession();
  const pathname = usePathname();
  const theme = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [menu, setMenu] = useState(false);
  const [profile, setProfile] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try { setCollapsed(localStorage.getItem("frotas-menu") === "recolhido"); } catch {} // eslint-disable-line react-hooks/set-state-in-effect
  }, []);
  useEffect(() => {
    if (!menu) return;
    const close = (event: MouseEvent) => { if (!menuRef.current?.contains(event.target as Node)) setMenu(false); };
    const esc = (event: KeyboardEvent) => { if (event.key === "Escape") setMenu(false); };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", close); document.removeEventListener("keydown", esc); };
  }, [menu]);

  function toggle() {
    setCollapsed((value) => {
      try { localStorage.setItem("frotas-menu", value ? "aberto" : "recolhido"); } catch {}
      return !value;
    });
  }

  const nav = [
    { href: "/", label: "Apólices", icon: FileStack, active: pathname === "/" || pathname.startsWith("/apolices") },
    ...(user.role === "admin" ? [{ href: "/acessos", label: "Acessos", icon: Users, active: pathname.startsWith("/acessos") }] : []),
  ];

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className={`flex shrink-0 flex-col border-r border-line bg-surface transition-[width] duration-150 ${collapsed ? "w-[56px]" : "w-[224px]"}`}>
        <div className={`flex h-14 items-center border-b border-line ${collapsed ? "justify-center" : "px-4"}`}>
          <Link href="/" aria-label="Início"><Logo compact={collapsed} /></Link>
        </div>
        <nav className="flex-1 space-y-0.5 p-2" aria-label="Principal">
          {nav.map(({ href, label, icon: Icon, active }) => (
            <Link key={href} href={href} title={collapsed ? label : undefined} aria-current={active ? "page" : undefined}
              className={`flex h-8 items-center gap-2.5 rounded-md text-[13px] font-medium transition-colors ${collapsed ? "justify-center" : "px-2.5"} ${active ? "bg-brand-soft text-brand-ink" : "text-ink-2 hover:bg-surface-2 hover:text-ink"}`}>
              <Icon size={16} aria-hidden="true" />
              {!collapsed && label}
            </Link>
          ))}
        </nav>
        {DEMO && !collapsed && <p className="mx-3 mb-2 rounded-md bg-warn-soft px-2.5 py-1.5 text-[11px] text-warn">Modo demonstração: dados fictícios.</p>}
        <div className="border-t border-line p-2">
          <button className={`flex h-8 w-full items-center gap-2.5 rounded-md text-ink-3 hover:bg-surface-2 hover:text-ink ${collapsed ? "justify-center" : "px-2.5"}`} onClick={toggle} aria-label={collapsed ? "Expandir menu" : "Recolher menu"}>
            {collapsed ? <ChevronsRight size={16} /> : <><ChevronsLeft size={16} /> <span className="text-xs">Recolher</span></>}
          </button>
          <div className="relative mt-1" ref={menuRef}>
            <button onClick={() => setMenu((value) => !value)} aria-expanded={menu} aria-haspopup="menu"
              className={`flex w-full items-center gap-2.5 rounded-md p-1.5 text-left hover:bg-surface-2 ${collapsed ? "justify-center" : ""}`}>
              <Avatar user={user} />
              {!collapsed && (
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[13px] font-medium">{user.name}</span>
                  <span className="block truncate text-[11px] text-ink-3">{user.role === "admin" ? "Administrador" : "Funcionário"}</span>
                </span>
              )}
            </button>
            {menu && (
              <div role="menu" className="rise card absolute bottom-full left-0 z-40 mb-2 w-60 p-1 shadow-[var(--shadow)]">
                <div className="px-2.5 py-2">
                  <p className="truncate font-medium">{user.name}</p>
                  <p className="truncate text-xs text-ink-3">{user.email}</p>
                </div>
                <div className="my-1 border-t border-line" />
                <button role="menuitem" className="flex h-8 w-full items-center gap-2 rounded px-2.5 hover:bg-surface-2" onClick={() => { setMenu(false); setProfile(true); }}>
                  <UserRound size={15} /> Meu perfil
                </button>
                <div className="px-2.5 pb-1 pt-2 text-[11px] font-medium text-ink-3">Tema</div>
                <div className="mx-1.5 mb-1 grid grid-cols-3 gap-1 rounded-md bg-surface-2 p-0.5">
                  {THEMES.map(({ value, label, icon: Icon }) => (
                    <button key={value} role="menuitemradio" aria-checked={theme.preference === value} onClick={() => theme.change(value)}
                      className={`flex h-7 items-center justify-center gap-1 rounded text-xs ${theme.preference === value ? "bg-surface font-medium shadow-sm" : "text-ink-2 hover:text-ink"}`}>
                      <Icon size={13} /> {label}
                    </button>
                  ))}
                </div>
                <div className="my-1 border-t border-line" />
                <button role="menuitem" className="flex h-8 w-full items-center gap-2 rounded px-2.5 text-danger hover:bg-danger-soft" onClick={logout}>
                  <LogOut size={15} /> Sair
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
      {profile && <ProfileDialog onClose={() => setProfile(false)} />}
    </div>
  );
}
