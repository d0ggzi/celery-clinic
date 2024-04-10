import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.homework.tasks import create_record
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.homework.schemas import Record
from celery.result import AsyncResult
from src.homework.celery import celery
from src.homework.db import db

app = FastAPI()

app.mount("/static", StaticFiles(directory="./src/homework/static"), name="static")
templates = Jinja2Templates(directory="./src/homework/templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", context={"request": request})


@app.post("/records")
def run_task(record: Record):
    task = create_record.delay(record.doctor)
    return JSONResponse({"record_id": task.id})


@app.get("/records/{record_id}")
def get_record(record_id: str):
    task_result = AsyncResult(record_id, app=celery)

    result = {
        "record_id": record_id,
        "doctor": task_result.info,
        "record_status": task_result.status
    }
    return JSONResponse(result)


@app.get("/allRecords")
def get_record(request: Request):
    res = []
    for el in db.get_all():
        data = el[1].decode().replace("'", '"')
        res.append(json.loads(data))
    res.sort(key=lambda x: x['date'])

    return templates.TemplateResponse(
        request=request, name="records.html", context={"records": res}
    )
