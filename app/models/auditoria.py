from ..db import get_db
from .usuario import agora


class AuditoriaModel:
    """Trilha de auditoria: quem fez o quê e quando. Nunca grava senhas."""

    @staticmethod
    def registrar(usuario, acao, detalhe=""):
        con = get_db()
        con.execute(
            "INSERT INTO auditoria (quando, usuario, acao, detalhe) VALUES (?, ?, ?, ?)",
            (agora(), usuario, acao[:80], detalhe[:300]),
        )
        con.commit()

    @staticmethod
    def ultimos(limite=200):
        return get_db().execute(
            "SELECT * FROM auditoria ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
