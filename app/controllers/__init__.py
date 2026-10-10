"""Controladores: recebem a requisição, validam, chamam modelos e regras, escolhem a visão."""
from flask import render_template

from . import auth, folha, funcionarios, fechamento, usuarios, conta


def registra_controladores(app):
    app.register_blueprint(auth.bp)
    app.register_blueprint(folha.bp)
    app.register_blueprint(funcionarios.bp)
    app.register_blueprint(fechamento.bp)
    app.register_blueprint(usuarios.bp)
    app.register_blueprint(conta.bp)

    @app.errorhandler(400)
    def _erro_400(_e):
        return render_template("erro.html", titulo="Requisição inválida",
                               mensagem="O formulário expirou ou está incompleto. Tente novamente."), 400

    @app.errorhandler(403)
    def _erro_403(_e):
        return render_template("erro.html", titulo="Acesso negado",
                               mensagem="Seu perfil não permite esta ação."), 403

    @app.errorhandler(404)
    def _erro_404(_e):
        return render_template("erro.html", titulo="Página não encontrada", mensagem="Verifique o endereço."), 404

    @app.errorhandler(500)
    def _erro_500(_e):
        # Mensagem genérica: detalhes do erro ficam só no log do servidor.
        return render_template("erro.html", titulo="Erro interno",
                               mensagem="Algo deu errado. Tente novamente ou avise a administração."), 500
