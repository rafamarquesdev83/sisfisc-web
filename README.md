# SISFISC Web — Controle de horas de equipes terceirizadas

Aplicação web em **Python + Flask** para lançamento diário da folha de presença, cadastro de
funcionários e fechamento mensal de horas, com autenticação por usuário e senha.

> Projeto de portfólio. Todos os nomes, matrículas e dados de exemplo são fictícios.
> Nenhum dado real de pessoas ou órgãos faz parte do repositório.

## Funcionalidades

- **Folha diária**: uma tela por dia com todos os funcionários ativos. Situação, entrada, saída,
  substituto e observação. Grava tudo de uma vez ou nada (transação).
- **Cálculo automático**: horas líquidas (permanência menos almoço), atraso em relação à escala
  do funcionário e regra de substituto (a espera até 2 h é abonada e a jornada é completada até 8 h).
- **Efetivo**: cadastro com escala, almoço e carga diária. Inativar preserva o histórico.
- **Fechamento mensal**: horas trabalhadas × previstas (dias úteis × carga), faltas, substituições
  e atrasos, com exportação em CSV compatível com o Excel.
- **Usuários e perfis**: *administrador* (acesso total) e *operador* (lança a folha e cadastra).
- **Auditoria**: registro de quem fez o quê e quando. Senhas nunca são gravadas.

## Stack e arquitetura (MVC)

| Camada | Onde fica | Papel |
|---|---|---|
| Modelo | `app/models/`, `app/schema.py`, `app/db.py` | Acesso ao SQLite com SQL parametrizado |
| Regras | `app/regras.py` | Cálculo de horas, atrasos e totais, sem Flask nem banco (fácil de testar) |
| Controlador | `app/controllers/` | Blueprints Flask: recebe a requisição, valida, chama modelo e regra |
| Visão | `app/views/templates/` | Templates Jinja2 com escape automático |
| Segurança | `app/seguranca.py` | CSRF, login obrigatório, perfis, cabeçalhos HTTP, política de senha |
| Configuração | `app/config.py` | Segredos e parâmetros via variáveis de ambiente |

Stack: Python 3.13, Flask 3, Waitress (servidor de produção), SQLite (modo WAL), Werkzeug (hash de senha).

## Segurança

| Ameaça | Como é tratada |
|---|---|
| Acesso sem login | Toda rota, exceto `/login`, exige sessão válida; a sessão é conferida a cada requisição |
| Força bruta | Bloqueio do login após 5 falhas em 15 min para o mesmo usuário |
| Enumeração de usuários | Mesma mensagem para usuário inexistente e senha errada |
| Fixação de sessão | A sessão é recriada a cada login |
| Sessão roubada | Cookie `HttpOnly`, `SameSite=Lax`, `Secure` (com `SISFISC_HTTPS=1`), expira em 30 min |
| CSRF | Token em todo formulário POST, comparado com `hmac.compare_digest` |
| Injeção de SQL | Somente consultas com parâmetros (`?` / `:nome`) |
| XSS | Escape automático do Jinja2 e política de conteúdo (CSP) sem scripts ou estilos inline |
| Clickjacking | `X-Frame-Options: DENY` e `frame-ancestors 'none'` |
| Senhas | Hash com Werkzeug (scrypt/pbkdf2); política de 12+ caracteres, letras e números, sem o login |
| Privilégio | Perfis verificados no servidor; operador não acessa usuários, auditoria nem exclusão |
| Integridade | Último administrador não pode ser desativado; administrador não desativa a si mesmo |
| Vazamento de erro | Páginas de erro genéricas; detalhes ficam só no log do servidor |
| Cache | `Cache-Control: no-store` para não guardar folhas em cache do navegador |
| Abuso por corpo grande | Limite de 64 KB por requisição |
| Segredos | `SECRET_KEY` e demais configurações vêm do ambiente (`.env` fora do Git) |

## Como rodar

Requisitos: Python 3.13 (ou 3.11+).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt

# 1) defina a chave secreta (veja .env.example)
set SISFISC_SECRET_KEY=<chave-com-32+-caracteres>     # Windows
# export SISFISC_SECRET_KEY=<chave>                   # Linux / macOS

# 2) crie o primeiro administrador (sem senha padrão)
python criar_admin.py

# 3) inicie o servidor
python run.py
```

Acesse `http://127.0.0.1:8080`. Para acesso pela rede local, defina `SISFISC_HOST=0.0.0.0`
e libere a porta no firewall, preferencialmente atrás de HTTPS (`SISFISC_HTTPS=1`).

## Testes

```bash
python -m unittest tests.test_sistema -v
```

Os testes usam um banco temporário e cobrem: regras de cálculo, política de senha, bloqueio de
login, CSRF, injeção de SQL, XSS, perfis e permissões, cabeçalhos de segurança, duplicidade de
lançamento, validação de horários e exportação CSV.

## Estrutura

```
sisfisc-web/
├── app/
│   ├── __init__.py        # fábrica da aplicação (create_app)
│   ├── config.py          # configuração via ambiente
│   ├── db.py / schema.py  # conexão e esquema SQLite
│   ├── regras.py          # regras de negócio puras
│   ├── seguranca.py       # CSRF, login, perfis, cabeçalhos, senha
│   ├── models/            # acesso a dados
│   ├── controllers/       # rotas (blueprints)
│   ├── views/templates/   # telas Jinja2
│   └── static/css/        # folha de estilo
├── tests/test_sistema.py
├── run.py                 # servidor de produção
├── criar_admin.py         # cria o primeiro administrador
├── requirements.txt
└── .env.example
```

## Próximos passos (ideias)

- Troca obrigatória de senha no primeiro acesso.
- Registro de feriados para o cálculo de dias previstos.
- Testes de navegador (Playwright) para os fluxos de tela.
- Migrações versionadas (Alembic) em vez de `CREATE IF NOT EXISTS`.
