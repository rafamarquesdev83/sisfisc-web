from datetime import datetime, timedelta

from ..db import get_db


def agora():
    return datetime.now().isoformat(timespec="seconds")


class UsuarioModel:
    @staticmethod
    def buscar_por_id(uid):
        return get_db().execute("SELECT * FROM usuarios WHERE id = ?", (uid,)).fetchone()

    @staticmethod
    def buscar_por_login(login):
        return get_db().execute("SELECT * FROM usuarios WHERE login = ?", (login,)).fetchone()

    @staticmethod
    def listar():
        return get_db().execute("SELECT * FROM usuarios ORDER BY nome").fetchall()

    @staticmethod
    def criar(login, nome, senha_hash, perfil):
        con = get_db()
        cur = con.execute(
            "INSERT INTO usuarios (login, nome, senha_hash, perfil, ativo, criado_em) VALUES (?, ?, ?, ?, 1, ?)",
            (login, nome, senha_hash, perfil, agora()),
        )
        con.commit()
        return cur.lastrowid

    @staticmethod
    def definir_ativo(uid, ativo):
        con = get_db()
        con.execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (1 if ativo else 0, uid))
        con.commit()

    @staticmethod
    def definir_senha(uid, senha_hash):
        con = get_db()
        con.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (senha_hash, uid))
        con.commit()

    @staticmethod
    def contar_admins_ativos():
        linha = get_db().execute(
            "SELECT COUNT(*) AS n FROM usuarios WHERE perfil = 'admin' AND ativo = 1"
        ).fetchone()
        return linha["n"]


class TentativasModel:
    """Registra falhas de login para bloquear tentativas repetidas."""

    @staticmethod
    def registrar(login, ip):
        con = get_db()
        con.execute("INSERT INTO tentativas_login (login, quando, ip) VALUES (?, ?, ?)", (login, agora(), ip))
        con.commit()

    @staticmethod
    def contar_recentes(login, minutos):
        corte = (datetime.now() - timedelta(minutes=minutos)).isoformat(timespec="seconds")
        linha = get_db().execute(
            "SELECT COUNT(*) AS n FROM tentativas_login WHERE login = ? AND quando >= ?", (login, corte)
        ).fetchone()
        return linha["n"]

    @staticmethod
    def limpar(login):
        con = get_db()
        con.execute("DELETE FROM tentativas_login WHERE login = ?", (login,))
        con.commit()
