"""Lançamento diário: uma folha por dia, com todos os funcionários ativos. Grava tudo ou nada."""
from datetime import date

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from .. import regras
from ..models import AuditoriaModel, FuncionarioModel, RegistroModel
from ..seguranca import login_obrigatorio

bp = Blueprint("folha", __name__)
MAX_OBS = 200
MAX_SUBSTITUTO = 80


@bp.route("/")
@login_obrigatorio
def raiz():
    return redirect(url_for("folha.folha"))


@bp.route("/folha", methods=["GET", "POST"])
@login_obrigatorio
def folha():
    texto = request.values.get("data") or date.today().isoformat()
    try:
        data = date.fromisoformat(texto)
    except ValueError:
        abort(400)

    if request.method == "POST":
        return _salvar(data)
    return _mostrar(data)


def _mostrar(data, valores=None):
    funcionarios = FuncionarioModel.listar(apenas_ativos=True)
    existentes = RegistroModel.do_dia(data.isoformat())
    linhas = []
    for f in funcionarios:
        fid = f["id"]
        if valores is not None:
            sit = valores.get(f"sit_{fid}", "")
            ent = valores.get(f"ent_{fid}", "")
            sai = valores.get(f"sai_{fid}", "")
            sub = valores.get(f"sub_{fid}", "")
            obs = valores.get(f"obs_{fid}", "")
        else:
            reg = existentes.get(fid)
            sit = reg["situacao"] if reg else ""
            ent = reg["entrada"] if reg else ""
            sai = reg["saida"] if reg else ""
            sub = reg["substituto"] if reg else ""
            obs = reg["observacao"] if reg else ""
        linhas.append({"id": fid, "nome": f["nome"], "posto": f["posto"], "escala": f"{f['entrada_escala']} - {f['saida_escala']}",
                       "sit": sit, "ent": ent, "sai": sai, "sub": sub, "obs": obs,
                       "horas": regras.fmt_horas(existentes[fid]["horas_minutos"]) if fid in existentes and valores is None else "—"})
    return render_template("folha.html", data=data, linhas=linhas, situacoes=regras.SITUACOES)


def _salvar(data):
    funcionarios = FuncionarioModel.listar(apenas_ativos=True)
    prazo = current_app.config["PRAZO_SUBSTITUTO_MINUTOS"]
    erros, linhas = [], []

    for f in funcionarios:
        fid = f["id"]
        sit = request.form.get(f"sit_{fid}", "")
        if not sit:
            linhas.append({"funcionario_id": fid, "remover": True})  # "não lançado" apaga o dia dele
            continue
        if sit not in regras.SITUACOES:
            erros.append(f"{f['nome']}: situação inválida.")
            continue

        ent = (request.form.get(f"ent_{fid}") or "").strip()
        sai = (request.form.get(f"sai_{fid}") or "").strip()
        sub = (request.form.get(f"sub_{fid}") or "").strip()[:MAX_SUBSTITUTO]
        obs = (request.form.get(f"obs_{fid}") or "").strip()[:MAX_OBS]

        if sit in regras.SITUACOES_COM_JORNADA:
            if not (regras.valida_hora(ent) and regras.valida_hora(sai)):
                erros.append(f"{f['nome']}: informe entrada e saída no formato HH:MM.")
                continue
            if regras.para_minutos(sai) <= regras.para_minutos(ent):
                erros.append(f"{f['nome']}: a saída precisa ser depois da entrada.")
                continue
        else:
            ent = sai = ""

        if sit == "substituido" and not sub:
            erros.append(f"{f['nome']}: informe o nome do substituto.")
            continue
        if sit != "substituido":
            sub = ""

        calc = regras.calcula_dia(sit, ent, sai, f["almoco_minutos"], f["entrada_escala"], f["saida_escala"], prazo)
        linhas.append({"funcionario_id": fid, "situacao": sit, "entrada": ent, "saida": sai,
                       "substituto": sub, "observacao": obs, "horas_minutos": calc["horas"],
                       "atraso_minutos": calc["atraso"]})

    if erros:
        for e in erros:
            flash(e, "erro")
        return _mostrar(data, valores=request.form), 422

    RegistroModel.salvar_dia(data.isoformat(), g.usuario["id"], linhas)
    lancados = sum(1 for ln in linhas if not ln.get("remover"))
    AuditoriaModel.registrar(g.usuario["login"], "salvar folha", f"{data.isoformat()}: {lancados} lançamento(s)")
    flash(f"Folha de {data.strftime('%d/%m/%Y')} salva: {lancados} lançamento(s).", "sucesso")
    return redirect(url_for("folha.folha", data=data.isoformat()))
