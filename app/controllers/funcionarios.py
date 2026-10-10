"""Cadastro do efetivo. Operador pode incluir, editar e inativar; só o administrador exclui."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .. import regras
from ..models import AuditoriaModel, FuncionarioModel
from ..seguranca import login_obrigatorio, perfil_exigido

bp = Blueprint("funcionarios", __name__, url_prefix="/funcionarios")


def ler_formulario(form):
    """Valida o formulário do funcionário. Devolve (dados, erros)."""
    erros = []
    nome = (form.get("nome") or "").strip()
    if not 3 <= len(nome) <= 80:
        erros.append("Nome: informe entre 3 e 80 caracteres.")
    entrada = (form.get("entrada_escala") or "").strip()
    saida = (form.get("saida_escala") or "").strip()
    if not regras.valida_hora(entrada) or not regras.valida_hora(saida):
        erros.append("Escala: horários no formato HH:MM.")
    elif regras.para_minutos(saida) <= regras.para_minutos(entrada):
        erros.append("Escala: a saída precisa ser depois da entrada.")
    try:
        almoco = int(form.get("almoco_minutos") or 60)
        if not 0 <= almoco <= 240:
            raise ValueError
    except ValueError:
        almoco = None
        erros.append("Almoço: informe de 0 a 240 minutos.")
    try:
        carga = float((form.get("carga_diaria_horas") or "8").replace(",", "."))
        if not 1 <= carga <= 12:
            raise ValueError
    except ValueError:
        carga = None
        erros.append("Carga diária: informe de 1 a 12 horas.")
    dados = {
        "nome": nome,
        "matricula": (form.get("matricula") or "").strip()[:20],
        "funcao": (form.get("funcao") or "").strip()[:40],
        "posto": (form.get("posto") or "").strip()[:80],
        "entrada_escala": entrada,
        "saida_escala": saida,
        "almoco_minutos": almoco,
        "carga_diaria_horas": carga,
    }
    return dados, erros


@bp.route("/")
@login_obrigatorio
def listar():
    return render_template("funcionarios.html", funcionarios=FuncionarioModel.listar())


@bp.route("/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo():
    if request.method == "POST":
        dados, erros = ler_formulario(request.form)
        if not erros:
            fid = FuncionarioModel.criar(dados)
            AuditoriaModel.registrar(g.usuario["login"], "incluir funcionário", f"id {fid}")
            flash("Funcionário incluído.", "sucesso")
            return redirect(url_for("funcionarios.listar"))
        for e in erros:
            flash(e, "erro")
        return render_template("funcionario_form.html", funcionario=request.form, titulo="Novo funcionário"), 422
    return render_template("funcionario_form.html", funcionario=None, titulo="Novo funcionário")


@bp.route("/<int:fid>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(fid):
    funcionario = FuncionarioModel.buscar(fid)
    if funcionario is None:
        abort(404)
    if request.method == "POST":
        dados, erros = ler_formulario(request.form)
        if not erros:
            FuncionarioModel.atualizar(fid, dados)
            AuditoriaModel.registrar(g.usuario["login"], "editar funcionário", f"id {fid}")
            flash("Dados atualizados.", "sucesso")
            return redirect(url_for("funcionarios.listar"))
        for e in erros:
            flash(e, "erro")
        return render_template("funcionario_form.html", funcionario=request.form, titulo="Editar funcionário",
                               fid=fid), 422
    return render_template("funcionario_form.html", funcionario=funcionario, titulo="Editar funcionário", fid=fid)


@bp.route("/<int:fid>/situacao", methods=["POST"])
@login_obrigatorio
def situacao(fid):
    funcionario = FuncionarioModel.buscar(fid)
    if funcionario is None:
        abort(404)
    ativo = not funcionario["ativo"]
    FuncionarioModel.definir_ativo(fid, ativo)
    AuditoriaModel.registrar(g.usuario["login"], "ativar" if ativo else "inativar funcionário", f"id {fid}")
    flash("Funcionário ativado." if ativo else "Funcionário inativado e removido da folha diária.", "sucesso")
    return redirect(url_for("funcionarios.listar"))


@bp.route("/<int:fid>/excluir", methods=["POST"])
@perfil_exigido("admin")
def excluir(fid):
    funcionario = FuncionarioModel.buscar(fid)
    if funcionario is None:
        abort(404)
    if FuncionarioModel.possui_registros(fid):
        flash("Este funcionário tem lançamentos. Inative em vez de excluir, para preservar o histórico.", "erro")
        return redirect(url_for("funcionarios.listar"))
    FuncionarioModel.excluir(fid)
    AuditoriaModel.registrar(g.usuario["login"], "excluir funcionário", f"id {fid}")
    flash("Funcionário excluído.", "sucesso")
    return redirect(url_for("funcionarios.listar"))
