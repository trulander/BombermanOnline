from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import typer
import subprocess

from .config import settings

app = typer.Typer()


@app.command()
def migrate():
    subprocess.run(["alembic", "upgrade", "head"])
    print("Migration successful")

@app.command()
def makemigrations(name: str = "new migration"):
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", name])



if __name__ == '__main__':
    fast_app = FastAPI(
        title=settings.APP_TITLE,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Set all CORS enabled origins
    if settings.CORS_ORIGINS:
        fast_app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app()

