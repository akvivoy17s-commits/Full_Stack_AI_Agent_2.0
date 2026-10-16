import uvicorn

from .config import cfg

if __name__ == "__main__":
    uvicorn.run("app.main:create_app", factory=True, host=cfg.host, port=cfg.port, reload=cfg.env == "development")
