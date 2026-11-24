"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, type User } from "@/lib/api";
import { Spinner } from "./ui";

type Session = { user: User; setUser: (user: User) => void; logout: () => Promise<void> };
const SessionContext = createContext<Session | null>(null);

export function useSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession fora do SessionProvider");
  return value;
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let alive = true;
    api<User>("auth/me")
      .then((value) => { if (alive) setUser(value); })
      .catch(() => router.replace(`/entrar?voltar=${encodeURIComponent(pathname)}`));
    const expired = () => router.replace(`/entrar?expirou=1&voltar=${encodeURIComponent(location.pathname)}`);
    window.addEventListener("frotas:session-expired", expired);
    return () => { alive = false; window.removeEventListener("frotas:session-expired", expired); };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- verificação só na montagem
  }, []);

  const logout = useCallback(async () => {
    await api("auth/logout", { method: "POST" }).catch(() => undefined);
    router.replace("/entrar");
  }, [router]);

  if (!user) {
    return <div className="grid h-screen place-items-center text-ink-3"><Spinner label="Abrindo o sistema" /></div>;
  }
  return <SessionContext.Provider value={{ user, setUser, logout }}>{children}</SessionContext.Provider>;
}
