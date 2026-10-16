from .config import cfg
from .main import create_app

if __name__ == "__main__":
    if cfg.env == "development":
        # Flask's own server with auto-reload. Never use it in production.
        create_app().run(host=cfg.host, port=cfg.port, use_reloader=True, debug=False)
    else:
        from waitress import serve
        serve(create_app(), host=cfg.host, port=cfg.port)
