"use client";

import { useRef, useState } from "react";
import { Camera, Check, Trash2 } from "lucide-react";
import { api, json, type User } from "@/lib/api";
import { useSession } from "./session";
import { Avatar, ErrorNote, Modal } from "./ui";

export function ProfileDialog({ onClose }: { onClose: () => void }) {
  const { user, setUser } = useSession();
  const fileRef = useRef<HTMLInputElement>(null);
  const [photoError, setPhotoError] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function upload(file: File) {
    setPhotoError("");
    const body = new FormData();
    body.append("file", file);
    try { setUser(await api<User>("profile/avatar", { method: "PUT", body })); }
    catch (cause) { setPhotoError(cause instanceof Error ? cause.message : "Não foi possível trocar a foto."); }
  }

  async function removePhoto() {
    try { setUser(await api<User>("profile/avatar/remove", { method: "POST" })); }
    catch (cause) { setPhotoError(cause instanceof Error ? cause.message : "Não foi possível remover a foto."); }
  }

  async function changePassword(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form)) as Record<string, string>;
    setError(""); setDone(false);
    if (data.new !== data.confirm) { setError("A confirmação não é igual à nova senha."); return; }
    setBusy(true);
    try {
      await api("profile/password", json("PUT", { current: data.current, new: data.new }));
      form.reset(); setDone(true);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível trocar a senha."); }
    finally { setBusy(false); }
  }

  return (
    <Modal title="Meu perfil" onClose={onClose} width={460}>
      <div className="flex items-center gap-4">
        <Avatar user={user} size={64} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-[15px] font-semibold">{user.name}</p>
          <p className="truncate text-ink-3">{user.email}</p>
          <div className="mt-2 flex gap-2">
            <button className="btn btn-sm" onClick={() => fileRef.current?.click()}><Camera size={14} /> Trocar foto</button>
            {user.avatar_version && <button className="btn btn-sm btn-ghost" onClick={removePhoto}><Trash2 size={14} /> Remover</button>}
          </div>
          <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" hidden
            onChange={(event) => { const file = event.target.files?.[0]; if (file) upload(file); event.target.value = ""; }} />
        </div>
      </div>
      {photoError && <div className="mt-3"><ErrorNote>{photoError}</ErrorNote></div>}

      <form onSubmit={changePassword} className="mt-6 space-y-3 border-t border-line pt-5">
        <h3 className="font-semibold">Trocar senha</h3>
        <label className="block"><span className="label">Senha atual</span><input className="field" name="current" type="password" autoComplete="current-password" required /></label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block"><span className="label">Nova senha</span><input className="field" name="new" type="password" autoComplete="new-password" minLength={12} required /></label>
          <label className="block"><span className="label">Repita a nova senha</span><input className="field" name="confirm" type="password" autoComplete="new-password" minLength={12} required /></label>
        </div>
        <p className="text-xs text-ink-3">Mínimo de 12 caracteres. As outras sessões abertas serão encerradas.</p>
        <ErrorNote>{error}</ErrorNote>
        <div className="flex items-center justify-end gap-3">
          {done && <span className="flex items-center gap-1 text-ok"><Check size={14} /> Senha alterada</span>}
          <button className="btn btn-primary" disabled={busy}>{busy ? "Salvando…" : "Salvar senha"}</button>
        </div>
      </form>
    </Modal>
  );
}
