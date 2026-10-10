"""Inicia o servidor de produção (Waitress). Por padrão escuta só na própria máquina."""
import os

from waitress import serve

from app import create_app


def main():
    app = create_app()
    host = os.environ.get("SISFISC_HOST", "127.0.0.1")
    port = int(os.environ.get("SISFISC_PORT", "8080"))
    print(f"SISFISC em execução: http://{host}:{port}  (Ctrl+C para parar)")
    serve(app, host=host, port=port, threads=4)


if __name__ == "__main__":
    main()
