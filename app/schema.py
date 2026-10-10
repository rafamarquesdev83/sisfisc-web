"""Esquema do banco SQLite. Todas as tabelas usam CREATE IF NOT EXISTS, então pode rodar sem medo."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    login       TEXT    NOT NULL UNIQUE,
    nome        TEXT    NOT NULL,
    senha_hash  TEXT    NOT NULL,
    perfil      TEXT    NOT NULL CHECK (perfil IN ('admin', 'operador')),
    ativo       INTEGER NOT NULL DEFAULT 1,
    criado_em   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS funcionarios (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    nome               TEXT    NOT NULL,
    matricula          TEXT    NOT NULL DEFAULT '',
    funcao             TEXT    NOT NULL DEFAULT '',
    posto              TEXT    NOT NULL DEFAULT '',
    entrada_escala     TEXT    NOT NULL DEFAULT '06:00',
    saida_escala       TEXT    NOT NULL DEFAULT '16:00',
    almoco_minutos     INTEGER NOT NULL DEFAULT 60,
    carga_diaria_horas REAL    NOT NULL DEFAULT 8,
    ativo              INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS registros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    data            TEXT    NOT NULL,
    funcionario_id  INTEGER NOT NULL REFERENCES funcionarios(id),
    situacao        TEXT    NOT NULL CHECK (situacao IN
                       ('presente', 'substituido', 'falta', 'atestado', 'folga', 'feriado')),
    entrada         TEXT    NOT NULL DEFAULT '',
    saida           TEXT    NOT NULL DEFAULT '',
    substituto      TEXT    NOT NULL DEFAULT '',
    observacao      TEXT    NOT NULL DEFAULT '',
    horas_minutos   INTEGER NOT NULL DEFAULT 0,
    atraso_minutos  INTEGER NOT NULL DEFAULT 0,
    lancado_por     INTEGER REFERENCES usuarios(id),
    atualizado_em   TEXT    NOT NULL,
    UNIQUE (data, funcionario_id)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    quando   TEXT NOT NULL,
    usuario  TEXT NOT NULL,
    acao     TEXT NOT NULL,
    detalhe  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tentativas_login (
    login  TEXT NOT NULL,
    quando TEXT NOT NULL,
    ip     TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS ix_tentativas_login ON tentativas_login (login, quando);
CREATE INDEX IF NOT EXISTS ix_registros_data ON registros (data);
"""
