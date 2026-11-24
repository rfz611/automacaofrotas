"""Redefine a senha de uma conta do Automação de Frotas (uso local)."""
import getpass, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from workspace.store import database, password_hash

with database() as db:
    users = db.execute("SELECT id, name, email FROM users ORDER BY created").fetchall()
    if not users:
        print("Nenhuma conta encontrada. Abra o sistema e crie o administrador."); sys.exit(1)
    print("\nContas cadastradas:")
    for i, u in enumerate(users, 1):
        print(f"  {i}. {u['name']} <{u['email']}>")
    choice = input("\nNúmero da conta (Enter = 1): ").strip() or "1"
    if not choice.isdigit() or not 1 <= int(choice) <= len(users):
        print("Opção inválida."); sys.exit(1)
    user = users[int(choice) - 1]
    print(f"\nNova senha para {user['email']} (mínimo 12 caracteres; não aparece enquanto digita).")
    while True:
        first = getpass.getpass("Nova senha: ")
        if len(first) < 12:
            print("Muito curta. Use pelo menos 12 caracteres."); continue
        if getpass.getpass("Repita a senha: ") != first:
            print("As senhas não conferem. Tente de novo."); continue
        break
    db.execute("UPDATE users SET password = ?, active = 1 WHERE id = ?", (password_hash(first), user["id"]))
    db.execute("DELETE FROM login_attempts WHERE email = ?", (user["email"],))
    db.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
    print(f"\nSenha redefinida. Entre com {user['email']} e a senha nova.")
