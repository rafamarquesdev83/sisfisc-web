
from ..db import get_db
from .usuario import agora


class RegistroModel:
    @staticmethod
    def do_dia(data_iso):
        linhas = get_db().execute("SELECT * FROM registros WHERE data = ?", (data_iso,)).fetchall()
        return {linha["funcionario_id"]: linha for linha in linhas}

    @staticmethod
    def periodo(inicio, fim):
        return get_db().execute(
            "SELECT * FROM registros WHERE data BETWEEN ? AND ?",
            (inicio.isoformat(), fim.isoformat()),
        ).fetchall()

    @staticmethod
    def salvar_dia(data_iso, usuario_id, linhas):
        """Grava o dia numa única transação. Linha com 'remover' apaga o lançamento do funcionário."""
        con = get_db()
        with con:  # commit ao sair sem erro; rollback se algo falhar
            for ln in linhas:
                if ln.get("remover"):
                    con.execute(
                        "DELETE FROM registros WHERE data = ? AND funcionario_id = ?",
                        (data_iso, ln["funcionario_id"]),
                    )
                    continue
                con.execute(
                    """INSERT INTO registros
                       (data, funcionario_id, situacao, entrada, saida, substituto, observacao,
                        horas_minutos, atraso_minutos, lancado_por, atualizado_em)
                       VALUES (:data, :funcionario_id, :situacao, :entrada, :saida, :substituto, :observacao,
                               :horas_minutos, :atraso_minutos, :lancado_por, :atualizado_em)
                       ON CONFLICT (data, funcionario_id) DO UPDATE SET
                           situacao = excluded.situacao, entrada = excluded.entrada, saida = excluded.saida,
                           substituto = excluded.substituto, observacao = excluded.observacao,
                           horas_minutos = excluded.horas_minutos, atraso_minutos = excluded.atraso_minutos,
                           lancado_por = excluded.lancado_por, atualizado_em = excluded.atualizado_em""",
                    {**ln, "data": data_iso, "lancado_por": usuario_id, "atualizado_em": agora()},
                )
