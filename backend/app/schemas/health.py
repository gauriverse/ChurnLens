from pydantic import BaseModel

class Health(BaseModel):
    status: str

class DatabaseHealth(Health):
    database: str