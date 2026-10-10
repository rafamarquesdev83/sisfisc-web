"""Troca da própria senha. Exige a senha atual."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..models import AuditoriaModel, UsuarioModel
from ..seguranca import login_obrigatorio, senha_fraca

bp = Blueprint("conta", __name__, url_prefix="/conta")


@bp.route("/senha", methods=["GET", "POST"])
@login_obrigatorio
def senha():
    if request.method == "POST":
        atual = request.form.get("atual") or ""
        nova = request.form.get("nova") or ""
        confirma = request.form.get("confirma") or ""
        if not check_password_hash(g.usuario["senha_hash"], atual):
            flash("A senha atual não confere.", "erro")
            return render_template("senha_form.html"), 422
        if nova != confirma:
            flash("A confirmação não confere com a nova senha.", "erro")
            return render_template("senha_form.html"), 422
        motivo = senha_fraca(nova, g.usuario["login"])
        if motivo:
            flash(motivo, "erro")
            return render_template("senha_form.html"), 422
        UsuarioModel.definir_senha(g.usuario["id"], generate_password_hash(nova))
        AuditoriaModel.registrar(g.usuario["login"], "trocar própria senha")
        flash("Senha alterada.", "sucesso")
        return redirect(url_for("folha.folha"))
    return render_template("senha_form.html")
