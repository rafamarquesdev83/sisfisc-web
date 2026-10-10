"""Configuração da aplicação. Segredos vêm de variáveis de ambiente, nunca do código."""
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    # Chave para assinar a sessão. Obrigatória (32+ caracteres). Ex.: python -c "import secrets; print(secrets.token_urlsafe(48))"
    SECRET_KEY = os.environ.get("SISFISC_SECRET_KEY", "")
    DATABASE = os.environ.get("SISFISC_DB", os.path.join(BASE_DIR, "instance", "sisfisc.db"))

    # Sessão: cookie não acessível por JavaScript, enviado só em navegação do próprio site,
    # expira após 30 min sem uso e só trafega por HTTPS quando SISFISC_HTTPS=1.
    SESSION_COOKIE_NAME = "sisfisc_sessao"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SISFISC_HTTPS", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_REFRESH_EACH_REQUEST = True

    # Limita o tamanho de qualquer formulário enviado (evita abuso por corpo gigante).
    MAX_CONTENT_LENGTH = 64 * 1024

    # Proteção contra força bruta: bloqueia o login após N falhas dentro da janela.
    TENTATIVAS_MAX = 5
    BLOQUEIO_MINUTOS = 15

    # Regras de negócio (padrões; cada funcionário pode ter a sua escala).
    PRAZO_SUBSTITUTO_MINUTOS = 120

    TESTING = False


class ConfigTeste(Config):
    TESTING = True
    SECRET_KEY = "teste-" + "x" * 48
    SESSION_COOKIE_SECURE = False
