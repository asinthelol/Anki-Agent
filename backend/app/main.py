"""FastAPI app entrypoint."""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from .routers import analysis

app = FastAPI(title="Anki Study Agent")

app.include_router(analysis.router)
