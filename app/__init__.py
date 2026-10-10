"""Fábrica da aplicação (padrão application factory)."""
from flask import Flask

from . import db
from .config import Config
from .controllers import registra_controladores
from .seguranca import registra_seguranca


def create_app(config_obj=Config):
    app = Flask(__name__, template_folder="views/templates", static_folder="static")
    app.config.from_object(config_obj)

    if not app.config.get("TESTING") and len(app.config.get("SECRET_KEY") or "") < 32:
        raise RuntimeError(
            "Defina a variável SISFISC_SECRET_KEY com pelo menos 32 caracteres antes de iniciar."
        )

    db.init_app(app)
    registra_seguranca(app)
    registra_controladores(app)

    with app.app_context():
        db.criar_schema()

    return app
