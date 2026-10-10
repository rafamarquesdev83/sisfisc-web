"""Cria o primeiro administrador. Não existe senha padrão: quem roda o script define a senha."""
import getpass
import sys

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import UsuarioModel
from app.seguranca import senha_fraca


def main():
    app = create_app()
    with app.app_context():
        login = input("Login do administrador (letras e números): ").strip().lower()
        if not login.isalnum() or not 3 <= len(login) <= 30:
            sys.exit("Login inválido: use de 3 a 30 letras ou números.")
        if UsuarioModel.buscar_por_login(login):
            sys.exit("Já existe um usuário com este login.")

        nome = input("Nome completo: ").strip()
        if not 3 <= len(nome) <= 80:
            sys.exit("Nome inválido: use de 3 a 80 caracteres.")

        while True:
            senha = getpass.getpass("Senha (mín. 12 caracteres, letras e números): ")
            if senha != getpass.getpass("Confirme a senha: "):
                print("As senhas não conferem. Tente de novo.")
                continue
            motivo = senha_fraca(senha, login)
            if motivo:
                print(motivo)
                continue
            break

        UsuarioModel.criar(login, nome, generate_password_hash(senha), "admin")
        print(f"Administrador '{login}' criado.")


if __name__ == "__main__":
    main()
