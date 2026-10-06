import os
import csv
from typing import Iterator, TextIO

from elasticsearch import AsyncElasticsearch, helpers, NotFoundError
from fastapi import HTTPException
from pydantic import ValidationError

from schemas import SDocs

INDEX_NAME="contents"

es_client: AsyncElasticsearch | None = None


async def get_es_client() -> AsyncElasticsearch:
    global es_client
    if es_client is None:
        es_client = AsyncElasticsearch(
            hosts=[os.getenv("ES_HOST", "http://localhost:9200")],
        )
    return es_client

async def close_es_client():
    global es_client
    if es_client is not None:
        await es_client.close()
        es_client = None

async def create_docs_bulk(es : AsyncElasticsearch, docs: list[SDocs]):
    operations = []
    for i in range(len(docs)):
        operations.append({
            "index": {"_index": INDEX_NAME, "_id": i}
        })
        operations.append({
            "text": docs[i].text,
            "created_date": docs[i].created_date,
            "rubrics": docs[i].rubrics
        })
    return await es.bulk(operations=operations)

async def get_docs(text : str, size: int, es: AsyncElasticsearch):
    return await es.search(
        index=INDEX_NAME,
        query={
            "match": {
                "text": {
                    "query": text,
                    "operator": "and",
                }
            }
        },
        size=size
    )

def read_docs_stream(f: TextIO, delimiter: str = ",") -> Iterator[SDocs]:
    reader = csv.DictReader(f, delimiter=delimiter)
    for i, row in enumerate(reader, start=2):
        row = {k.strip(): (v.strip() if isinstance(v, str) else v)
               for k, v in row.items()}
        try:
            yield SDocs(**row)
        except ValidationError as e:
            raise ValueError(f"Ошибка в строке {i}: {e}") from e


async def delete_doc(es: AsyncElasticsearch, doc_id):
    try:
        response = await es.delete(index="contents", id=doc_id)
        if response["result"] == "deleted":
            return {"status": "success", "id": doc_id}
        elif response["result"] == "not_found":
            return {"status": "not_found", "id": doc_id}

    except NotFoundError:
        raise HTTPException(status_code=404, detail="Документ не найден")