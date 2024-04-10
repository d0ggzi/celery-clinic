from pydantic import BaseModel


class Record(BaseModel):
    doctor: str
