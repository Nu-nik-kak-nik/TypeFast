import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.core.config import settings
from backend.app.db.dependencies import init_models

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    settings.mount_css,
    StaticFiles(directory=settings.static_dir),
    name=settings.static_dir,
)
app.mount(
    settings.mount_js,
    StaticFiles(directory=settings.static_js_dir),
    name=settings.static_js_dir,
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_index():
    with open(settings.html_index_path, "r") as f:
        html_content = f.read()
    await init_models()
    return html_content


@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    return FileResponse(
        settings.frontend_dir / "favicon.svg",
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    return FileResponse(
        settings.frontend_dir / "favicon.svg",
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@app.get("/statistics/{user_id}", response_class=HTMLResponse)
async def read_statistics_page(user_id: str):
    with open(settings.html_statistics_path, "r") as f:
        html_content = f.read()
    return html_content


app.include_router(router, prefix=settings.api_prefix)

if __name__ == "__main__":
    uvicorn.run(
        settings.app_module,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )
