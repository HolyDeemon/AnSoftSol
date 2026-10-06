import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from fastapi.templating import Jinja2Templates

from elasticsearch import AsyncElasticsearch

from elastic import get_es_client, close_es_client, create_docs_bulk, read_docs_stream, get_docs, delete_doc

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

templates = Jinja2Templates("templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_es_client()  # создаём клиент при старте
    yield
    await close_es_client()  # закрываем при остановке


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), es : AsyncElasticsearch = Depends(get_es_client)):
    text_stream = io.TextIOWrapper(
        file.file,
        encoding="UTF-8",
        newline="",
    )
    docs = list(read_docs_stream(text_stream))
    bulk = await create_docs_bulk(es, docs)
    return {"ok" : True}

@app.get("/search")
async def search(text : str, es : AsyncElasticsearch = Depends(get_es_client)):
    return await get_docs(text, 20, es)

@app.delete("/doc")
async def delete(doc_id : int, es : AsyncElasticsearch = Depends(get_es_client)):
    return await delete_doc(es, doc_id)