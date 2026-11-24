"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { UserPlus } from "lucide-react";
import { api, json, type User } from "@/lib/api";
import { useSession } from "@/components/session";
import { Avatar, ErrorNote, Modal, PageHeader, Spinner } from "@/components/ui";

export default function Acessos() {
  const { user } = useSession();
  const router = useRouter();
  const [users, setUsers] = useState<User[] | null>(null);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [confirm, setConfirm] = useState<User | null>(null);

  const load = useCallback(async () => {
    try { setUsers(await api<User[]>("users")); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível carregar a equipe."); }
  }, []);
  useEffect(() => {
    if (user.role !== "admin") { router.replace("/"); return; }
    load(); // eslint-disable-line react-hooks/set-state-in-effect
  }, [user.role, router, load]);

  async function setActive(member: User, active: boolean) {
    setError("");
    try { await api(`users/${member.id}`, json("PUT", { active })); setConfirm(null); load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível alterar o acesso."); }
  }

  return (
    <>
      <PageHeader title="Acessos" description="Quem pode entrar no sistema. Só administradores veem esta tela."
        actions={<button className="btn btn-primary" onClick={() => setAdding(true)}><UserPlus size={15} /> Cadastrar funcionário</button>} />
      <div className="space-y-3 overflow-auto p-6">
        <ErrorNote>{error}</ErrorNote>
        <div className="card overflow-hidden">
          {!users ? <div className="grid h-32 place-items-center text-ink-3"><Spinner label="Carregando" /></div> : (
            <table className="w-full text-left">
              <thead className="bg-surface-2 text-xs text-ink-2">
                <tr className="[&>th]:border-b [&>th]:border-line [&>th]:px-4 [&>th]:py-2 [&>th]:font-medium"><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Situação</th><th /></tr>
              </thead>
              <tbody>
                {users.map((member) => (
                  <tr key={member.id} className={`border-b border-line last:border-0 [&>td]:px-4 [&>td]:py-2.5 ${member.active ? "" : "text-ink-3"}`}>
                    <td><span className="flex items-center gap-2.5"><Avatar user={member} size={26} /> <span className="font-medium">{member.name}</span>{member.id === user.id && <span className="badge badge-neutral">você</span>}</span></td>
                    <td className="text-ink-2">{member.email}</td>
                    <td>{member.role === "admin" ? "Administrador" : "Funcionário"}</td>
                    <td><span className={`badge ${member.active ? "badge-ok" : "badge-neutral"}`}>{member.active ? "Ativo" : "Desativado"}</span></td>
                    <td className="text-right">
                      {member.id !== user.id && (member.active
                        ? <button className="btn btn-sm" onClick={() => setConfirm(member)}>Desativar</button>
                        : <button className="btn btn-sm" onClick={() => setActive(member, true)}>Reativar</button>)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {adding && <AddUser onClose={() => setAdding(false)} onDone={() => { setAdding(false); load(); }} />}
      {confirm && (
        <Modal title={`Desativar ${confirm.name}?`} description="A pessoa sai do sistema na hora e não consegue mais entrar. O trabalho dela continua no histórico. Você pode reativar depois." onClose={() => setConfirm(null)}
          footer={<><button className="btn" onClick={() => setConfirm(null)}>Cancelar</button><button className="btn btn-danger" onClick={() => setActive(confirm, false)}>Desativar</button></>} />
      )}
    </>
  );
}

function AddUser({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    setBusy(true); setError("");
    try { await api("users", json("POST", data)); onDone(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível cadastrar."); setBusy(false); }
  }
  return (
    <Modal title="Cadastrar funcionário" description="Passe a senha inicial para a pessoa. Ela pode trocar depois em Meu perfil." onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <label className="block"><span className="label">Nome</span><input className="field" name="name" minLength={2} maxLength={100} required /></label>
        <label className="block"><span className="label">E-mail</span><input className="field" name="email" type="email" required /></label>
        <label className="block"><span className="label">Senha inicial</span><input className="field" name="password" type="text" minLength={12} required autoComplete="off" /></label>
        <p className="text-xs text-ink-3">Mínimo de 12 caracteres.</p>
        <ErrorNote>{error}</ErrorNote>
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" className="btn" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? "Cadastrando…" : "Cadastrar"}</button>
        </div>
      </form>
    </Modal>
  );
}
