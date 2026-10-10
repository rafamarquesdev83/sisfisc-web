"""Modelos: acesso ao banco. Só SQL com parâmetros, nunca texto montado com dados do usuário."""
from .usuario import UsuarioModel, TentativasModel
from .funcionario import FuncionarioModel
from .registro import RegistroModel
from .auditoria import AuditoriaModel

__all__ = ["UsuarioModel", "TentativasModel", "FuncionarioModel", "RegistroModel", "AuditoriaModel"]
