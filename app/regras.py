"""Regras de negócio puras: sem Flask e sem banco, por isso fáceis de testar.

Espelham o cálculo da versão em JavaScript (SISFISC-LIMPEZA):
- horas líquidas = (saída - entrada) - almoço;
- atraso = atraso na entrada + saída antecipada, em relação à escala do funcionário;
- substituto: a espera até 2 h é abonada e a jornada é completada até 8 h.
"""
import re
from datetime import timedelta

SITUACOES = {
    "presente": "Presente",
    "substituido": "Falta c/ Substituto",
    "falta": "Falta s/ Substituto",
    "atestado": "Atestado / Licença",
    "folga": "Folga de Escala",
    "feriado": "Feriado / Dispensa",
}
SITUACOES_COM_JORNADA = ("presente", "substituido")
JORNADA_REFERENCIA_MIN = 480  # 8 h

_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def valida_hora(texto):
    return bool(texto) and _HORA.match(texto) is not None


def para_minutos(hora):
    h, m = hora.split(":")
    return int(h) * 60 + int(m)


def fmt_horas(minutos):
    """Minutos -> 'H:MM' (ex.: 510 -> '8:30')."""
    minutos = max(0, int(minutos or 0))
    return f"{minutos // 60}:{minutos % 60:02d}"


def calcula_dia(situacao, entrada, saida, almoco, escala_entrada, escala_saida, prazo_substituto=120):
    """Devolve {'horas', 'atraso', 'abono'} em minutos para um dia de um funcionário."""
    if situacao not in SITUACOES_COM_JORNADA:
        return {"horas": 0, "atraso": 0, "abono": 0}

    ent = para_minutos(entrada)
    sai = para_minutos(saida)
    esc_ent = para_minutos(escala_entrada)
    esc_sai = para_minutos(escala_saida)

    atraso = max(0, ent - esc_ent) + max(0, esc_sai - sai)
    liquido = max(0, (sai - ent) - almoco)
    abono = 0

    if situacao == "substituido":
        espera = ent - esc_ent if ent > esc_ent else max(0, JORNADA_REFERENCIA_MIN - liquido)
        abono = min(prazo_substituto, espera)
        liquido = min(JORNADA_REFERENCIA_MIN, liquido + abono)
        atraso = 0  # a espera do substituto é coberta pelo acordo, não conta como atraso

    return {"horas": liquido, "atraso": atraso, "abono": abono}


def dias_uteis(inicio, fim):
    """Conta de segunda a sexta entre duas datas (inclusive). Feriados não são descontados."""
    total = 0
    dia = inicio
    while dia <= fim:
        if dia.weekday() < 5:
            total += 1
        dia += timedelta(days=1)
    return total


def resumo(funcionarios, registros, inicio, fim):
    """Totais por funcionário no período. Recebe linhas (dict-like) já filtradas pelo período."""
    uteis = dias_uteis(inicio, fim)
    linhas = {}
    for f in funcionarios:
        linhas[f["id"]] = {
            "id": f["id"],
            "nome": f["nome"],
            "matricula": f["matricula"],
            "posto": f["posto"],
            "dias": 0,
            "horas": 0,
            "previstas": round(uteis * f["carga_diaria_horas"] * 60),
            "faltas_sem": 0,
            "substituicoes": 0,
            "atraso": 0,
        }
    for r in registros:
        linha = linhas.get(r["funcionario_id"])
        if linha is None:
            continue
        if r["situacao"] in SITUACOES_COM_JORNADA:
            linha["dias"] += 1
        if r["situacao"] == "falta":
            linha["faltas_sem"] += 1
        if r["situacao"] == "substituido":
            linha["substituicoes"] += 1
        linha["horas"] += r["horas_minutos"]
        linha["atraso"] += r["atraso_minutos"]
    return list(linhas.values())
