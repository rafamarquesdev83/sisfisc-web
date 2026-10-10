"""Gestão de usuários e trilha de auditoria. Restrito ao administrador."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from ..models import AuditoriaModel, UsuarioModel
from ..seguranca import perfil_exigido, senha_fraca

bp = Blueprint("usuarios", __name__)
PERFIS = ("admin", "operador")


@bp.route("/usuarios")
@perfil_exigido("admin")
def listar():
    return render_template("usuarios.html", usuarios=UsuarioModel.listar())


@bp.route("/usuarios/novo", methods=["GET", "POST"])
@perfil_exigido("admin")
def novo():
    if request.method == "POST":
        login = (request.form.get("login") or "").strip().lower()
        nome = (request.form.get("nome") or "").strip()
        perfil = request.form.get("perfil") or ""
        senha = request.form.get("senha") or ""
        erros = []
        if not login.isalnum() or not 3 <= len(login) <= 30:
            erros.append("Login: 3 a 30 letras ou números, sem espaços.")
        if UsuarioModel.buscar_por_login(login):
            erros.append("Já existe um usuário com este login.")
        if not 3 <= len(nome) <= 80:
            erros.append("Nome: informe entre 3 e 80 caracteres.")
        if perfil not in PERFIS:
            erros.append("Perfil inválido.")
        motivo = senha_fraca(senha, login)
        if motivo:
            erros.append(motivo)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("usuario_form.html", dados=request.form), 422
        UsuarioModel.criar(login, nome, generate_password_hash(senha), perfil)
        AuditoriaModel.registrar(g.usuario["login"], "criar usuário", f"{login} ({perfil})")
        flash("Usuário criado.", "sucesso")
        return redirect(url_for("usuarios.listar"))
    return render_template("usuario_form.html", dados=None)


@bp.route("/usuarios/<int:uid>/ativo", methods=["POST"])
@perfil_exigido("admin")
def ativo(uid):
    alvo = UsuarioModel.buscar_por_id(uid)
    if alvo is None:
        abort(404)
    if alvo["id"] == g.usuario["id"]:
        flash("Você não pode desativar o próprio usuário.", "erro")
        return redirect(url_for("usuarios.listar"))
    novo_estado = not alvo["ativo"]
    if not novo_estado and alvo["perfil"] == "admin" and UsuarioModel.contar_admins_ativos() <= 1:
        flash("Não é possível desativar o último administrador.", "erro")
        return redirect(url_for("usuarios.listar"))
    UsuarioModel.definir_ativo(uid, novo_estado)
    AuditoriaModel.registrar(g.usuario["login"], "ativar usuário" if novo_estado else "desativar usuário",
                             alvo["login"])
    flash("Usuário ativado." if novo_estado else "Usuário desativado.", "sucesso")
    return redirect(url_for("usuarios.listar"))


@bp.route("/usuarios/<int:uid>/senha", methods=["POST"])
@perfil_exigido("admin")
def redefinir_senha(uid):
    alvo = UsuarioModel.buscar_por_id(uid)
    if alvo is None:
        abort(404)
    senha = request.form.get("senha") or ""
    motivo = senha_fraca(senha, alvo["login"])
    if motivo:
        flash(motivo, "erro")
        return redirect(url_for("usuarios.listar"))
    UsuarioModel.definir_senha(uid, generate_password_hash(senha))
    AuditoriaModel.registrar(g.usuario["login"], "redefinir senha", alvo["login"])
    flash("Senha redefinida.", "sucesso")
    return redirect(url_for("usuarios.listar"))


@bp.route("/auditoria")
@perfil_exigido("admin")
def auditoria():
    return render_template("auditoria.html", registros=AuditoriaModel.ultimos())
