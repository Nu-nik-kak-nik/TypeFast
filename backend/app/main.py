import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response

from backend.app.db.dependencies import init_models
from backend.app.api.routes import router
from backend.app.core.config import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_languages,
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


@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(settings.html_index_path, "r") as f:
        html_content = f.read()
    await init_models()
    return html_content


@app.get("/favicon.svg")
async def favicon():
    svg_content = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <text y=".9em" font-size="90">⚡</text>
    </svg>
    """
    return Response(content=svg_content, media_type="image/svg+xml")


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
