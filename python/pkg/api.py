from fastapi import Request
from fastapi.routing import APIRouter

from pkg.controllers import volunteer_funds

from .models import *
from pkg.database import (
    create_items,
    create_requirement,
    delete_requirement,
    get_funds,
    get_items_by_requirement,
    get_requirements,
    search_funds,
)

router = APIRouter()


@router.get("/fund")
async def search_funds_endpoint(query: str, req: Request) -> list[Fund]:
    db = req.app.state.db
    result = await search_funds(db, query)
    return result


@router.get("/requirements")
async def get_requirements_endpoint(req: Request) -> list[RequirementWithItems]:
    db = req.app.state.db
    requirements = await get_requirements(db)
    for requirement in requirements:
        requirement.items = await get_items_by_requirement(db, requirement.id)
    return requirements


@router.post("/requirements")
async def create_requirement_endpoint(requirement: RequirementCreate, req: Request):
    db = req.app.state.db
    await create_requirement(db, requirement)
    return {"message": "Requirement created"}


@router.post("/requirements/{requirement_id}/items")
async def create_items_endpoint(
    requirement_id: str, items: list[ItemBase], req: Request
):
    db = req.app.state.db
    await create_items(db, items, requirement_id)
    return {"message": "Items created"}


@router.delete("/requirements/{requirement_id}")
async def delete_requirement_endpoint(requirement_id: str, req: Request):
    db = req.app.state.db
    await delete_requirement(db, requirement_id)
    return {"message": f"Requirement with ID {requirement_id} deleted"}


@router.get("/volunteer/{volunteer_id}/funds")
async def get_volunteer_funds_endpoint(volunteer_id: str, req: Request) -> list[Fund]:
    db = req.app.state.db
    funds = await get_funds(db, volunteer_id)
    return funds


@router.get("/categories")
def get_categories():
    return {"categories": ["Food", "Medicine", "Equipment", "Other"]}
