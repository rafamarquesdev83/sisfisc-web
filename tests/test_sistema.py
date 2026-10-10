"""Testes: regras de negócio, segurança e fluxos principais. Usam banco temporário."""
import csv
import io
import os
import re
import shutil
import tempfile
import unittest
from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app
from app.config import ConfigTeste
from app import regras
from app.models import FuncionarioModel, RegistroModel, UsuarioModel
from app.seguranca import senha_fraca

SENHA_ADMIN = "Admin-Teste-2026"
SENHA_OPERADOR = "Operador-Teste-2026"


class ConfigDeTeste(ConfigTeste):
    DATABASE = None  # definido em cada teste


def _funcionario(nome="Maria Exemplo", entrada="06:00", saida="16:00"):
    return {"nome": nome, "matricula": "EX-001", "funcao": "Auxiliar", "posto": "Bloco A",
            "entrada_escala": entrada, "saida_escala": saida, "almoco_minutos": 60,
            "carga_diaria_horas": 8}


class BaseTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        cfg = type("Cfg", (ConfigDeTeste,), {"DATABASE": os.path.join(self.pasta, "teste.db")})
        self.app = create_app(cfg)
        self.client = self.app.test_client()
        with self.app.app_context():
            UsuarioModel.criar("admin", "Administrador Teste", generate_password_hash(SENHA_ADMIN), "admin")
            UsuarioModel.criar("operador", "Operador Teste", generate_password_hash(SENHA_OPERADOR), "operador")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def token(self, caminho):
        html = self.client.get(caminho).get_data(as_text=True)
        achado = re.search(r'name="_csrf" value="([^"]+)"', html)
        self.assertIsNotNone(achado, f"sem token CSRF em {caminho}")
        return achado.group(1)

    def entrar(self, login, senha):
        token = self.token("/login")
        return self.client.post("/login", data={"login": login, "senha": senha, "_csrf": token})

    def logar_admin(self):
        self.entrar("admin", SENHA_ADMIN)

    def logar_operador(self):
        self.entrar("operador", SENHA_OPERADOR)

    def novo_funcionario(self, **kw):
        with self.app.app_context():
            return FuncionarioModel.criar({**_funcionario(**kw)})


# ----- regras de negócio (puras) -----

class RegrasTeste(unittest.TestCase):
    def test_horas_liquidas_descontam_almoco(self):
        # 10 h de permanência - 1 h de almoço = 9 h líquidas
        r = regras.calcula_dia("presente", "06:00", "16:00", 60, "06:00", "16:00")
        self.assertEqual(r["horas"], 540)
        self.assertEqual(r["atraso"], 0)

    def test_atraso_conta_entrada_tardia_e_saida_antecipada(self):
        r = regras.calcula_dia("presente", "06:30", "15:45", 60, "06:00", "16:00")
        self.assertEqual(r["atraso"], 30 + 15)

    def test_substituto_completa_jornada_ate_8h(self):
        # 8 h de permanência - 1 h de almoço = 7 h; o substituto cobre a 1 h que falta
        r = regras.calcula_dia("substituido", "06:00", "14:00", 60, "06:00", "16:00", 120)
        self.assertEqual(r["horas"], 480)
        self.assertEqual(r["abono"], 60)

    def test_falta_nao_tem_horas(self):
        r = regras.calcula_dia("falta", "", "", 60, "06:00", "16:00")
        self.assertEqual(r, {"horas": 0, "atraso": 0, "abono": 0})

    def test_dias_uteis_pula_fim_de_semana(self):
        self.assertEqual(regras.dias_uteis(date(2026, 10, 5), date(2026, 10, 11)), 5)

    def test_valida_hora(self):
        self.assertTrue(regras.valida_hora("06:00"))
        self.assertFalse(regras.valida_hora("25:00"))
        self.assertFalse(regras.valida_hora("6:00"))
        self.assertFalse(regras.valida_hora(""))

    def test_fmt_horas(self):
        self.assertEqual(regras.fmt_horas(510), "8:30")
        self.assertEqual(regras.fmt_horas(0), "0:00")

    def test_politica_de_senha(self):
        self.assertIsNotNone(senha_fraca("curta1"))
        self.assertIsNotNone(senha_fraca("somenteletras"))
        self.assertIsNotNone(senha_fraca("joao-silva-2026", login="joao-silva"))
        self.assertIsNone(senha_fraca("Senha-Forte-2026"))


# ----- autenticação e autorização -----

class SegurancaTeste(BaseTeste):
    def test_rota_protegida_redireciona_para_login(self):
        resp = self.client.get("/folha")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_post_sem_token_csrf_e_recusado(self):
        resp = self.client.post("/login", data={"login": "admin", "senha": SENHA_ADMIN})
        self.assertEqual(resp.status_code, 400)

    def test_senha_errada_nao_revela_se_usuario_existe(self):
        r1 = self.entrar("admin", "errada-errada-1")
        r2 = self.entrar("ninguem-aqui", "errada-errada-1")
        self.assertEqual(r1.status_code, 401)
        self.assertEqual(r2.status_code, 401)
        for resp in (r1, r2):
            self.assertIn("Usuário ou senha inválidos.", resp.get_data(as_text=True))

    def test_login_bloqueia_apos_tentativas_falhas(self):
        for _ in range(5):
            self.entrar("admin", "errada-errada-1")
        resp = self.entrar("admin", SENHA_ADMIN)  # mesmo a senha certa fica bloqueada
        self.assertEqual(resp.status_code, 429)

    def test_injecao_sql_no_login_nao_funciona(self):
        resp = self.entrar("admin' OR '1'='1", "qualquer")
        self.assertEqual(resp.status_code, 401)

    def test_operador_nao_acessa_usuarios(self):
        self.logar_operador()
        self.assertEqual(self.client.get("/usuarios").status_code, 403)
        self.assertEqual(self.client.get("/auditoria").status_code, 403)

    def test_operador_nao_exclui_funcionario(self):
        fid = self.novo_funcionario()
        self.logar_operador()
        token = self.token("/funcionarios/")
        resp = self.client.post(f"/funcionarios/{fid}/excluir", data={"_csrf": token})
        self.assertEqual(resp.status_code, 403)

    def test_cabecalhos_de_seguranca_presentes(self):
        resp = self.client.get("/login")
        self.assertIn("default-src 'self'", resp.headers["Content-Security-Policy"])
        self.assertEqual(resp.headers["X-Frame-Options"], "DENY")
        self.assertEqual(resp.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resp.headers["Cache-Control"], "no-store")

    def test_login_registra_auditoria_sem_senha(self):
        self.logar_admin()
        with self.app.app_context():
            from app.models import AuditoriaModel
            texto = " ".join(" ".join(str(c) for c in linha) for linha in AuditoriaModel.ultimos())
        self.assertIn("login", texto)
        self.assertNotIn(SENHA_ADMIN, texto)

    def test_admin_nao_pode_desativar_a_si_mesmo(self):
        self.logar_admin()
        with self.app.app_context():
            admin_id = UsuarioModel.buscar_por_login("admin")["id"]
        token = self.token("/usuarios")
        resp = self.client.post(f"/usuarios/{admin_id}/ativo", data={"_csrf": token}, follow_redirects=True)
        self.assertIn("Você não pode desativar o próprio usuário.", resp.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(UsuarioModel.buscar_por_id(admin_id)["ativo"], 1)


# ----- fluxos e proteção contra injeção -----

class FluxosTeste(BaseTeste):
    def test_xss_em_nome_de_funcionario_e_escapado(self):
        self.novo_funcionario(nome="<script>alert(1)</script>")
        self.logar_admin()
        html = self.client.get("/folha?data=2026-10-05").get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_lancamento_diario_nao_duplica_o_dia(self):
        fid = self.novo_funcionario()
        self.logar_admin()
        for _ in range(2):
            token = self.token("/folha?data=2026-10-05")
            self.client.post("/folha", data={
                "_csrf": token, "data": "2026-10-05",
                f"sit_{fid}": "presente", f"ent_{fid}": "06:00", f"sai_{fid}": "16:00",
            })
        with self.app.app_context():
            total = len(RegistroModel.do_dia("2026-10-05"))
            horas = RegistroModel.do_dia("2026-10-05")[fid]["horas_minutos"]
        self.assertEqual(total, 1)
        self.assertEqual(horas, 540)

    def test_substituido_sem_nome_do_substituto_e_recusado(self):
        fid = self.novo_funcionario()
        self.logar_admin()
        token = self.token("/folha?data=2026-10-05")
        resp = self.client.post("/folha", data={
            "_csrf": token, "data": "2026-10-05",
            f"sit_{fid}": "substituido", f"ent_{fid}": "06:00", f"sai_{fid}": "14:00", f"sub_{fid}": "",
        })
        self.assertEqual(resp.status_code, 422)

    def test_horario_invalido_e_recusado(self):
        fid = self.novo_funcionario()
        self.logar_admin()
        token = self.token("/folha?data=2026-10-05")
        resp = self.client.post("/folha", data={
            "_csrf": token, "data": "2026-10-05",
            f"sit_{fid}": "presente", f"ent_{fid}": "16:00", f"sai_{fid}": "06:00",
        })
        self.assertEqual(resp.status_code, 422)

    def test_data_invalida_na_url_retorna_400(self):
        self.logar_admin()
        self.assertEqual(self.client.get("/folha?data=2026-13-40").status_code, 400)

    def test_exportacao_csv_com_bom_e_cabecalho(self):
        fid = self.novo_funcionario()
        self.logar_admin()
        token = self.token("/folha?data=2026-10-05")
        self.client.post("/folha", data={
            "_csrf": token, "data": "2026-10-05",
            f"sit_{fid}": "presente", f"ent_{fid}": "06:00", f"sai_{fid}": "16:00",
        })
        resp = self.client.get("/fechamento/csv?mes=2026-10")
        self.assertEqual(resp.status_code, 200)
        texto = resp.get_data(as_text=True)
        self.assertTrue(texto.startswith("﻿"))
        linhas = list(csv.reader(io.StringIO(texto.lstrip("﻿")), delimiter=";"))
        self.assertEqual(linhas[0][0], "Funcionário")
        self.assertEqual(linhas[1][0], "Maria Exemplo")

    def test_mes_invalido_no_fechamento_retorna_400(self):
        self.logar_admin()
        self.assertEqual(self.client.get("/fechamento/?mes=abc").status_code, 400)

    def test_troca_de_senha_exige_senha_atual(self):
        self.logar_operador()
        token = self.token("/conta/senha")
        resp = self.client.post("/conta/senha", data={
            "_csrf": token, "atual": "errada-errada-1",
            "nova": "Nova-Senha-2026", "confirma": "Nova-Senha-2026",
        })
        self.assertEqual(resp.status_code, 422)

    def test_criar_usuario_com_senha_fraca_e_recusado(self):
        self.logar_admin()
        token = self.token("/usuarios/novo")
        resp = self.client.post("/usuarios/novo", data={
            "_csrf": token, "login": "novato", "nome": "Novato Teste",
            "perfil": "operador", "senha": "123456",
        })
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
