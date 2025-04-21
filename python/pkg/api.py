from datetime import timedelta
from typing import Annotated
from fastapi import Header, Request
from fastapi.routing import APIRouter

from pkg.utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
)


from .models import *
from pkg.database import (
    create_items,
    create_requirement,
    delete_requirement,
    get_funds,
    get_items_by_requirement,
    get_requirements,
    get_volunteer_funds_for_dash,
    get_volunteer_requirements_for_dash,
    search_funds,
    user_login,
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


@router.post("/profile/login")
async def login_endpoint(user_data: UserLogin, req: Request):
    db = req.app.state.db
    user = await user_login(db, user_data.email, user_data.password)
    if not user:
        return {"message": "User not found"}, 404
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),
    )
    return {"access_token": token, "user": user}


@router.get("/profile")
async def get_profile_endpoint(token: Annotated[str | None, Header()], req: Request):
    db = req.app.state.db
    if not token:
        return {"message": "Token is missing"}, 401
    decoded_token = decode_access_token(token).get("sub")
    if not decoded_token:
        return {"message": "Invalid token"}, 401
    user = await db.get_user_by_email(decoded_token)
    if not user:
        return {"message": "User not found"}, 404


@router.get("/volunteer/dashboard")
async def get_volunteer_dashboard_endpoint(
    token: Annotated[str | None, Header()], req: Request
):
    if not token:
        return {"message": "Token is missing"}, 401
    email = decode_access_token(token).get("sub")
    if not email:
        return {"message": "Invalid token"}, 401
    db = req.app.state.db
    funds = await get_volunteer_funds_for_dash(db, email)
    requirements = await get_volunteer_requirements_for_dash(db, email)
    return {
        "funds": funds,
        "requirements": requirements,
    }
