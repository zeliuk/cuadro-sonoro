from pydantic import BaseModel, Field


class Search(BaseModel):
    artist: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=160)


class Import(BaseModel):
    slot: int = Field(ge=0, le=2)
    source_id: str = Field(pattern=r'^[A-Za-z0-9_-]{11}$')
    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)


class Station(BaseModel):
    slot: int = Field(ge=0, le=2)
    title: str = Field(min_length=1, max_length=100)
    url: str = Field(max_length=1000)
