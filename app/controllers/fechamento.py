"""Fechamento mensal por funcionário, em tela e em CSV para o Excel."""
import calendar
import csv
import io
from datetime import date

from flask import Blueprint, Response, abort, render_template, request

from .. import regras
from ..models import FuncionarioModel, RegistroModel
from ..seguranca import login_obrigatorio

bp = Blueprint("fechamento", __name__, url_prefix="/fechamento")


def _periodo(texto):
    try:
        ano, mes = (int(p) for p in texto.split("-"))
        ultimo = calendar.monthrange(ano, mes)[1]
        return date(ano, mes, 1), date(ano, mes, ultimo), f"{mes:02d}/{ano}"
    except (ValueError, AttributeError):
        abort(400)


def _resumo(mes_texto):
    inicio, fim, rotulo = _periodo(mes_texto)
    funcionarios = FuncionarioModel.listar()
    registros = RegistroModel.periodo(inicio, fim)
    linhas = regras.resumo(funcionarios, registros, inicio, fim)
    return linhas, rotulo, inicio


@bp.route("/")
@login_obrigatorio
def mensal():
    mes = request.args.get("mes") or date.today().strftime("%Y-%m")
    linhas, rotulo, _ = _resumo(mes)
    return render_template("fechamento.html", linhas=linhas, rotulo=rotulo, mes=mes, fmt=regras.fmt_horas)


@bp.route("/csv")
@login_obrigatorio
def exportar_csv():
    mes = request.args.get("mes") or date.today().strftime("%Y-%m")
    linhas, rotulo, _ = _resumo(mes)
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["Funcionário", "Matrícula", "Posto", "Dias trabalhados", "Horas trabalhadas",
                       "Horas previstas", "Faltas s/ substituto", "Substituições", "Atraso (min)"])
    for l in linhas:
        escritor.writerow([l["nome"], l["matricula"], l["posto"], l["dias"], regras.fmt_horas(l["horas"]),
                           regras.fmt_horas(l["previstas"]), l["faltas_sem"], l["substituicoes"], l["atraso"]])
    conteudo = "﻿" + saida.getvalue()  # BOM para o Excel reconhecer acentos
    return Response(conteudo, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="fechamento_{mes}.csv"'})
