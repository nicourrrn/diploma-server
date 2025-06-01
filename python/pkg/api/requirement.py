from typing import Annotated
from fastapi.routing import APIRouter
from fastapi import HTTPException, Header, Request
from pkg.models import *
from pkg.database import *
from pkg.utils import decode_access_token


requirement_router = APIRouter(prefix="/requirement")


@requirement_router.get("/")
async def get_requirements_endpoint(
    req: Request, query: str = ""
) -> list[RequirementWithItems]:
    db = req.app.state.db
    try:
        requirements = await (
            get_requirements(db, query) if query != "" else get_requirements(db)
        )
        for requirement in requirements:
            requirement.items = await get_untaken_items_by_requirement(
                db, requirement.id
            )
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return requirements


@requirement_router.post("/")
async def create_requirement_endpoint(
    token: Annotated[str, Header()], requirement: RequirementCreate, req: Request
) -> MessageWithId:
    db = req.app.state.db
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    if not (mail := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        recipient = await get_recipient_by_email(db, mail)
    except DatabaseException:
        raise HTTPException(status_code=404, detail="Recipient not found")
    id = await create_requirement(
        db,
        requirement,
        recipient_id=recipient.id,
    )
    return MessageWithId(id=id, message="Requirement created")


@requirement_router.patch("/{requirement_id}")
async def update_requirement_endpoint(
    requirement_id: str,
    requirement: RequirementBase,
    req: Request,
) -> Message:
    db = req.app.state.db
    try:
        await update_requirement_by_id(db, requirement_id, requirement)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Message(message="Requirement updated")


@requirement_router.post("/{requirement_id}/items")
async def create_items_endpoint(
    requirement_id: str, items: list[ItemBase], req: Request
) -> Message:
    db = req.app.state.db
    await create_items(db, items, requirement_id)
    return Message(message="Items created")


@requirement_router.get("/categories")
def get_categories() -> dict[str, list[str]]:
    return {"categories": ["Food", "Medicine", "Equipment", "Other"]}


@requirement_router.get("/{requirement_id}")
async def get_requirement_by_id_endpoint(
    requirement_id: str, req: Request
) -> RequirementWithItemsAndFund:
    db = req.app.state.db
    try:
        requirement = await get_requirement(db, requirement_id)
        requirement.items = await get_items_by_requirement(db, requirement.id)
        print(requirement.items)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))
    result = RequirementWithItemsAndFund(
        **requirement.model_dump(),
    )
    try:
        result.recipient = await get_recipient_by_requirement(db, requirement.id)
        result.fund = await get_funds_by_requirement(db, requirement.id)
    finally:
        return result


@requirement_router.delete("/{requirement_id}")
async def delete_requirement_endpoint(requirement_id: str, req: Request) -> Message:
    db = req.app.state.db
    await delete_requirement(db, requirement_id)
    return Message(message=f"Requirement with ID {requirement_id} deleted")
