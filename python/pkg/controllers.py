from os import getenv
from typing import Callable

import dotenv

from .database import Repository, SqliteRepository
from .models import *

dotenv.load_dotenv()
database: Callable[[], Repository]
match getenv("DATABASE", "sqlite"):
    case "sqlite":
        database = lambda: SqliteRepository(getenv("DB_PATH", "db.sqlite"))
        database().init_database()
    case _:
        raise ValueError("Database not supported")


def search_funds(query: str) -> list[Fund]:
    result = database().search_funds(query)
    return [Fund(**row) for row in result]


def register_fund(fund: FundBase):
    pass


def get_requirements() -> list[RequirementWithItems]:
    db = database()
    data = db.get_requirements()
    for item in data:
        item["items"] = db.get_items_by_requirement(item["id"])
    return [RequirementWithItems(**item) for item in data]


def create_requirement(requirement: RequirementCreate):
    db = database()
    db.create_requirement(requirement)


def create_items(items: list[ItemBase], requirement_id: str):
    db = database()
    db.create_items(items, requirement_id)


def delete_requirement(requirement_id: str):
    db = database()
    db.delete_requirement(requirement_id)


def volunteer_funds(volunteer_id: str) -> list[FundRepresentative]:
    db = database()
    result = db.volunteer_funds(volunteer_id)
    return [FundRepresentative(**row) for row in result]
