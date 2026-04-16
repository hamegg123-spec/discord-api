from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

class PostData(BaseModel):
    channelId: str
    message: str

@app.get("/")
def root():
    return {"status": "ok"}
