from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from . import controllers
from .models import *

router = APIRouter()


@router.get("/fund")
def search_funds(query: str) -> list[Fund]:
    return controllers.search_funds(query)


@router.get("/profile")
def get_profile():
    return {"message": "Fetching user profile"}


@router.post("/profile/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return {"message": f"Logging in user: {form_data.username}"}


@router.get("/requirements")
def list_requirements():
    return controllers.get_requirements()


@router.post("/requirements")
async def create_requirement(req: RequirementCreate):
    print(f"Create requirements: {req}")
    controllers.create_requirement(req)


@router.post("/requirements/{requirement_id}/items")
async def create_items(requirement_id: str, items: list[ItemBase]):
    print(f"Create items for requirement {requirement_id}: {items}")
    controllers.create_items(items, requirement_id)
    return {"message": f"Items created for requirement {requirement_id}"}


@router.get("/requirements/{requirement_id}")
def read_requirement(requirement_id: int):
    return {"message": f"Reading requirement with ID: {requirement_id}"}


# @router.put("/requirements/{requirement_id}")
# def update_requirement(requirement_id: int, requirement: RequirementUpdate):
#     return {
#         "message": f"Updating requirement with ID: {requirement_id} to {requirement}"
#     }


@router.delete("/requirements/{requirement_id}")
def delete_requirement(requirement_id: str):
    print(f"Delete requirement with ID: {requirement_id}")
    controllers.delete_requirement(requirement_id)
    return {"message": f"Requirement with ID: {requirement_id} deleted"}


@router.get("/volunteer/{volunteer_id}/funds")
def get_volunteer_funds(volunteer_id: str):
    print(f"Get funds for volunteer with ID: {volunteer_id}")
    funds = controllers.volunteer_funds(volunteer_id)
    return funds


@router.get("/categories")
def get_categories():
    return {"categories": ["Food", "Medicine", "Equipment", "Other"]}
