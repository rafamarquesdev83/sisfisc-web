"""Conexão com o banco. Uma conexão por requisição, fechada ao final."""
import os
import sqlite3

from flask import current_app, g

from .schema import SCHEMA


def conectar(caminho):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")   # integridade referencial ligada
    con.execute("PRAGMA journal_mode = WAL")  # escrita mais segura e leitura sem bloquear
    return con


def get_db():
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def _fechar(_erro=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def criar_schema():
    con = get_db()
    con.executescript(SCHEMA)
    con.commit()


def init_app(app):
    app.teardown_appcontext(_fechar)
