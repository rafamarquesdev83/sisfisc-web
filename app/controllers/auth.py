from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from ..models import AuditoriaModel, TentativasModel, UsuarioModel

bp = Blueprint("auth", __name__)

MENSAGEM_FALHA = "Usuário ou senha inválidos."  # mesma mensagem para usuário inexistente e senha errada


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    login_txt = (request.form.get("login") or "").strip().lower()[:50]
    senha = request.form.get("senha") or ""
    ip = request.remote_addr or ""

    if TentativasModel.contar_recentes(login_txt, current_app.config["BLOQUEIO_MINUTOS"]) >= \
            current_app.config["TENTATIVAS_MAX"]:
        AuditoriaModel.registrar(login_txt or "-", "login bloqueado", f"ip {ip}")
        flash("Muitas tentativas. Aguarde alguns minutos e tente de novo.", "erro")
        return render_template("login.html"), 429

    usuario = UsuarioModel.buscar_por_login(login_txt) if login_txt else None
    if usuario is None or not usuario["ativo"] or not check_password_hash(usuario["senha_hash"], senha):
        TentativasModel.registrar(login_txt, ip)
        AuditoriaModel.registrar(login_txt or "-", "falha de login", f"ip {ip}")
        flash(MENSAGEM_FALHA, "erro")
        return render_template("login.html"), 401

    # Sessão nova a cada login: evita fixação de sessão.
    session.clear()
    session.permanent = True
    session["usuario_id"] = usuario["id"]
    TentativasModel.limpar(login_txt)
    AuditoriaModel.registrar(usuario["login"], "login", f"ip {ip}")
    return redirect(url_for("folha.folha"))


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu do sistema.", "aviso")
    return redirect(url_for("auth.login"))
