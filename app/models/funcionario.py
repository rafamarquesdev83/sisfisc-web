from ..db import get_db


class FuncionarioModel:
    @staticmethod
    def listar(apenas_ativos=False):
        sql = "SELECT * FROM funcionarios"
        if apenas_ativos:
            sql += " WHERE ativo = 1"
        return get_db().execute(sql + " ORDER BY nome").fetchall()

    @staticmethod
    def buscar(fid):
        return get_db().execute("SELECT * FROM funcionarios WHERE id = ?", (fid,)).fetchone()

    @staticmethod
    def criar(dados):
        con = get_db()
        cur = con.execute(
            """INSERT INTO funcionarios
               (nome, matricula, funcao, posto, entrada_escala, saida_escala, almoco_minutos, carga_diaria_horas, ativo)
               VALUES (:nome, :matricula, :funcao, :posto, :entrada_escala, :saida_escala, :almoco_minutos,
                       :carga_diaria_horas, 1)""",
            dados,
        )
        con.commit()
        return cur.lastrowid

    @staticmethod
    def atualizar(fid, dados):
        con = get_db()
        con.execute(
            """UPDATE funcionarios SET nome = :nome, matricula = :matricula, funcao = :funcao, posto = :posto,
               entrada_escala = :entrada_escala, saida_escala = :saida_escala,
               almoco_minutos = :almoco_minutos, carga_diaria_horas = :carga_diaria_horas
               WHERE id = :id""",
            {**dados, "id": fid},
        )
        con.commit()

    @staticmethod
    def definir_ativo(fid, ativo):
        con = get_db()
        con.execute("UPDATE funcionarios SET ativo = ? WHERE id = ?", (1 if ativo else 0, fid))
        con.commit()

    @staticmethod
    def possui_registros(fid):
        linha = get_db().execute("SELECT COUNT(*) AS n FROM registros WHERE funcionario_id = ?", (fid,)).fetchone()
        return linha["n"] > 0

    @staticmethod
    def excluir(fid):
        con = get_db()
        con.execute("DELETE FROM funcionarios WHERE id = ?", (fid,))
        con.commit()
