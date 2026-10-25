"""Authenticated single-user FastAPI adapter for the Python archive service.

Static assets are vanilla HTML/CSS/JS. A per-server bearer token protects every
archive/settings/model operation; credentials and arbitrary files are not served.
"""
from __future__ import annotations
import asyncio
import hmac
import os
import re
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from aletheia_core.config import data_home
from aletheia_core.service import Service
from aletheia_core.model import validate_gguf

STATIC = Path(__file__).parent / "static"


def create_app(home: Path | None = None, *, token=None, service_factory=Service):
    access_token = token or os.environ.get("ALETHEIA_ACCESS_TOKEN") or secrets.token_urlsafe(32)
    @asynccontextmanager
    async def lifespan(app):
        service = service_factory(home or data_home("AletheiaAgora"))
        app.state.service = service
        initialization = asyncio.create_task(service.initialize())
        try:
            yield
        finally:
            initialization.cancel()
            await asyncio.gather(initialization, return_exceptions=True)
            await service.close()

    app = FastAPI(title="Aletheia Agora", version="0.1.1", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    # The launcher needs the token to construct its local browser URL. It never
    # appears in HTML, API state, logs, or a query string sent to the server.
    app.state.access_token = access_token

    @app.middleware("http")
    async def authenticate(request: Request, next_handler):
        if request.url.path.startswith("/api/"):
            supplied = request.headers.get("authorization", "").removeprefix("Bearer ")
            if not hmac.compare_digest(supplied.encode(), access_token.encode()):
                return JSONResponse(dict(ok=False, error="Enter this server's access token to open the library."), status_code=401)
            if request.method == "POST" and request.url.path != "/api/model/upload":
                length = request.headers.get("content-length", "0")
                if not length.isdigit() or int(length) > 32 * 1024 * 1024:
                    return JSONResponse(dict(ok=False, error="Import at most 32 MiB per request."), status_code=413)
        response = await next_handler(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/state")
    async def state():
        return dict(ok=True, value=app.state.service.snapshot())

    @app.post("/api/actions/{name}")
    async def action(name: str, request: Request):
        try:
            # Check actual bytes too: clients need not supply Content-Length.
            raw = await request.body()
            if len(raw) > 32 * 1024 * 1024:
                raise ValueError("Import at most 32 MiB per request.")
            import json
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("Invalid application request.")
            result = await app.state.service.execute(name, value.get("args", []))
            return dict(ok=True, value=result)
        except asyncio.CancelledError:
            return JSONResponse(dict(ok=False, error="Stopped."), status_code=409)
        except Exception as error:
            return JSONResponse(dict(ok=False, error=str(error)), status_code=400)

    @app.post("/api/model/upload")
    async def upload_model(request: Request):
        service = app.state.service
        async def upload():
            # Stream the large file once, without multipart spooling or retaining
            # it in RAM. Ignore client paths and never overwrite an existing file.
            from urllib.parse import unquote
            original = unquote(request.headers.get("x-model-filename", "model.gguf"))
            name = re.sub(r"[^a-zA-Z0-9._-]", "_", re.split(r"[/\\]", original)[-1])[-180:]
            if not name.lower().endswith(".gguf"):
                raise ValueError("Upload a GGUF model file.")
            directory = service.home / "models"
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / (secrets.token_hex(6) + "-" + name)
            temporary = destination.with_suffix(".upload")
            received, total = 0, int(request.headers.get("content-length", "0"))
            maximum = 128 * 1024**3
            if total > maximum:
                raise ValueError("The uploaded model exceeds 128 GiB. Select a server-side file path instead.")
            try:
                with temporary.open("xb") as stream:
                    async for chunk in request.stream():
                        received += len(chunk)
                        if received > maximum:
                            raise ValueError("The uploaded model exceeds 128 GiB.")
                        await asyncio.to_thread(stream.write, chunk)
                        service.progress = dict(phase="downloading", message="Uploading your GGUF model...", received=received, total=total)
                # Header validation expects the final .gguf extension. Keep the
                # final file only after checking bytes and version explicitly.
                with temporary.open("rb") as stream:
                    import struct
                    header = stream.read(24)
                if len(header) != 24 or header[:4] != b"GGUF" or struct.unpack_from("<I", header, 4)[0] not in (2, 3):
                    raise ValueError("This upload is not a supported GGUF container.")
                os.replace(temporary, destination)
                await service.model.stop()
                service.config.save({**service.config.value, "provider": "embedded", "modelPath": str(destination)})
                await service.model.start()
                return service.snapshot()
            finally:
                temporary.unlink(missing_ok=True)
        try:
            return dict(ok=True, value=await service.exclusive(upload))
        except asyncio.CancelledError:
            return JSONResponse(dict(ok=False, error="Upload stopped."), status_code=409)
        except Exception as error:
            return JSONResponse(dict(ok=False, error=str(error)), status_code=400)

    @app.get("/")
    async def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
