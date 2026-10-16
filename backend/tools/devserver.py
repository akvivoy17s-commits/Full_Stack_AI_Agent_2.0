"""Local dev server for browser tests: stdlib static HTTP server on 127.0.0.1 (random free port), serves one directory.
Never serves `.agent` (agent state). Always shut down by the context manager, even on cancel/error."""
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class _Handler(SimpleHTTPRequestHandler):
    def log_message(self, *a):          # quiet
        pass

    def do_GET(self):
        if ".agent" in self.path.split("/"):
            self.send_error(404)
            return
        super().do_GET()


class StaticServer:
    def __init__(self, root: Path):
        self.root = Path(root)
        self._srv: ThreadingHTTPServer | None = None
        self.url = ""

    def __enter__(self) -> "StaticServer":
        h = functools.partial(_Handler, directory=str(self.root))
        self._srv = ThreadingHTTPServer(("127.0.0.1", 0), h)
        self.url = f"http://127.0.0.1:{self._srv.server_address[1]}/"
        threading.Thread(target=self._srv.serve_forever, daemon=True, name="dev-server").start()
        return self

    def __exit__(self, *exc) -> None:
        if self._srv:
            self._srv.shutdown()
            self._srv.server_close()
            self._srv = None
