"""Segurança transversal: CSRF, login obrigatório, perfis, cabeçalhos HTTP e política de senha."""
import hmac
import re
import secrets
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from .models import UsuarioModel

SENHA_MIN = 12
SENHA_MAX = 128  # limite também evita abuso com senhas gigantes no hash


# ----- CSRF: todo POST precisa do token da sessão -----

def token_csrf():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def _verificar_csrf():
    if request.method != "POST":
        return None
    esperado = session.get("_csrf", "")
    enviado = request.form.get("_csrf", "") or request.headers.get("X-CSRF-Token", "")
    if not esperado or not enviado or not hmac.compare_digest(esperado, enviado):
        abort(400)
    return None


# ----- autenticação e autorização -----

def login_obrigatorio(view):
    @wraps(view)
    def envolvido(*args, **kwargs):
        uid = session.get("usuario_id")
        usuario = UsuarioModel.buscar_por_id(uid) if uid else None
        # Confere a cada requisição: usuário desativado perde o acesso na hora.
        if usuario is None or not usuario["ativo"]:
            session.clear()
            flash("Entre para continuar.", "aviso")
            return redirect(url_for("auth.login"))
        g.usuario = usuario
        return view(*args, **kwargs)
    return envolvido


def perfil_exigido(*perfis):
    def decorador(view):
        @wraps(view)
        @login_obrigatorio
        def envolvido(*args, **kwargs):
            if g.usuario["perfil"] not in perfis:
                abort(403)
            return view(*args, **kwargs)
        return envolvido
    return decorador


# ----- cabeçalhos HTTP de proteção -----

def _cabecalhos(resposta):
    resposta.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Referrer-Policy"] = "same-origin"
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


# ----- política de senha -----

def senha_fraca(senha, login=""):
    """Devolve a mensagem do motivo, ou None se a senha atende à política."""
    if len(senha) < SENHA_MIN:
        return f"A senha precisa ter pelo menos {SENHA_MIN} caracteres."
    if len(senha) > SENHA_MAX:
        return f"A senha pode ter no máximo {SENHA_MAX} caracteres."
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        return "A senha precisa ter letras e números."
    if login and login.lower() in senha.lower():
        return "A senha não pode conter o login."
    return None


def registra_seguranca(app):
    app.before_request(_verificar_csrf)
    app.after_request(_cabecalhos)
    app.jinja_env.globals["csrf_token"] = token_csrf
