from pydantic import BaseModel, Field


class Search(BaseModel):
    artist: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=160)


class StationSearch(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str | None = Field(default=None, max_length=100)


class Import(BaseModel):
    slot: int = Field(ge=0, le=2)
    source_id: str = Field(pattern=r'^[A-Za-z0-9_-]{11}$')
    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)


class Station(BaseModel):
    slot: int = Field(ge=0, le=2)
    title: str = Field(min_length=1, max_length=100)
    url: str = Field(max_length=1000)
    stationuuid: str | None = Field(default=None, max_length=64)
    country: str | None = Field(default=None, max_length=100)
    homepage: str | None = Field(default=None, max_length=1000)
    favicon: str | None = Field(default=None, max_length=1000)
    codec: str | None = Field(default=None, max_length=40)
    bitrate: int | None = Field(default=None, ge=0, le=100000)
