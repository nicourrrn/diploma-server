from typing import Annotated
from fastapi import HTTPException, Header, Request
from fastapi.routing import APIRouter

from pkg.utils import (
    create_access_token,
    decode_access_token,
)

from pkg.models import *
from pkg.database import *


router = APIRouter()


@router.get("/fund")
async def search_funds_endpoint(query: str, req: Request) -> list[Fund]:
    db = req.app.state.db
    result = await search_funds(db, query)
    return result


@router.get("/fund/{fund_id}")
async def get_fund_by_id_endpoint(fund_id: str, req: Request) -> DetailFund:
    db = req.app.state.db

    try:
        fund = await get_fund_by_id(db, fund_id)
        report = await get_report_by_fund_id(db, fund_id)
        volunteer = await get_volunteer_by_fund(db, fund.id)
        requirement = await get_requirement_by_fund(db, fund.id)
        requirement.recipient = await get_recipient_by_requirement(db, requirement.id)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return DetailFund(
        **fund.model_dump(),
        requirement=requirement,
        report=report,
        volunteer=volunteer,
    )


requirement_router = APIRouter(prefix="/requirement", tags=["api"])


@requirement_router.get("/")
async def get_requirements_endpoint(req: Request) -> list[RequirementWithItems]:
    db = req.app.state.db
    try:
        requirements = await get_requirements(db)
        for requirement in requirements:
            requirement.items = await get_items_by_requirement(db, requirement.id)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return requirements


@requirement_router.post("/")
async def create_requirement_endpoint(
    requirement: RequirementCreate, req: Request
) -> dict[str, str]:
    db = req.app.state.db
    await create_requirement(db, requirement)
    return {"message": "Requirement created"}


@requirement_router.post("/{requirement_id}/items")
async def create_items_endpoint(
    requirement_id: str, items: list[ItemBase], req: Request
) -> dict[str, str]:
    db = req.app.state.db
    await create_items(db, items, requirement_id)
    return {"message": "Items created"}


@requirement_router.delete("/{requirement_id}")
async def delete_requirement_endpoint(
    requirement_id: str, req: Request
) -> dict[str, str]:
    db = req.app.state.db
    await delete_requirement(db, requirement_id)
    return {"message": f"Requirement with ID {requirement_id} deleted"}


@router.get("/categories")
def get_categories() -> dict[str, list[str]]:
    return {"categories": ["Food", "Medicine", "Equipment", "Other"]}


@router.post("/profile/login")
async def login_endpoint(user_data: UserLogin, req: Request) -> LoginResponse:
    db = req.app.state.db

    if not (user := await user_login(db, user_data.email, user_data.password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": user.email},
    )

    return LoginResponse(
        access_token=token,
        user_account=user,
    )


@router.get("/profile")
async def get_profile_endpoint(
    token: Annotated[str | None, Header()], req: Request
) -> UserAccount:

    db = req.app.state.db
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    decoded_token = decode_access_token(token).get("sub")
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    # user = await get_user_by_email(decoded_token)
    user = None
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


volunteer_router = APIRouter(prefix="/volunteer", tags=["api"])


@volunteer_router.get("/{volunteer_id}/funds")
async def get_volunteer_funds_endpoint(
    volunteer_id: str, req: Request
) -> list[DetailFund]:
    db = req.app.state.db
    funds = await get_funds(db, volunteer_id)
    if not funds:
        raise HTTPException(status_code=404, detail="No funds found")
    report, volunteer, requirements = await get_fund_details(db, funds[0].id)
    detailed_funds = []
    for fund in funds:
        report, volunteer, requirements = await get_fund_details(db, fund.id)
        detailed_funds.append(
            DetailFund(
                **fund.model_dump(),
                report=report,
                volunteer=volunteer,
                requirement=requirements,
            )
        )

    return detailed_funds


@volunteer_router.get("/profile")
async def get_volunteer_profile_endpoint(
    token: Annotated[str | None, Header()], req: Request
) -> VolunteerWithUserAccount:
    db = req.app.state.db

    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    if not (decoded_token := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        volunteer = await get_volunteer_by_email(db, decoded_token)
        user = await get_user_info(db, decoded_token)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return VolunteerWithUserAccount(
        **volunteer.model_dump(),
        user_account=user,
    )


@volunteer_router.get("/dashboard")
async def get_volunteer_dashboard_endpoint(
    token: Annotated[str | None, Header()], req: Request
) -> Dashboard:

    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    if not (email := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")

    db = req.app.state.db
    detailed_funds = []
    updated_requirements = []

    try:
        funds = await get_volunteer_funds_for_dash(db, email)
        for fund in funds:
            report, volunteer, requirements = await get_fund_details(db, fund.id)
            detailed_funds.append(
                DetailFund(
                    **fund.model_dump(),
                    report=report,
                    volunteer=volunteer,
                    requirement=requirements,
                )
            )

        requirements = await get_volunteer_requirements_for_dash(db, email)
        for requirement in requirements:
            requirement.items = await get_items_by_requirement(db, requirement.id)
            requirement.recipient = await get_recipient_by_requirement(
                db, requirement.id
            )
            updated_requirements.append(requirement)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Dashboard(
        funds=detailed_funds,
        requirements=updated_requirements,
    )


recipient_router = APIRouter(prefix="/recipient", tags=["api"])


@recipient_router.get("/{recipient_id}/requirements")
async def get_recipient_funds_endpoint(recipient_id: str, req: Request) -> list:
    db = req.app.state.db
    try:
        return await get_requirements_by_recipient(db, recipient_id)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))


@recipient_router.get("/profile")
async def get_recipient_profile_endpoint(
    token: Annotated[str | None, Header()], req: Request
) -> Recipient:
    db = req.app.state.db
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    if not (decoded_token := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        return await get_recipient_by_email(db, decoded_token)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))


@recipient_router.get("/dashboard")
async def get_recipient_dashboard_endpoint(
    token: Annotated[str | None, Header()], req: Request
) -> Dashboard:
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    if not (email := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")

    db = req.app.state.db

    try:
        recipient = await get_recipient_by_email(db, email)
        requirements = await get_requirements_by_recipient(db, recipient.id)
        funds = await get_five_last_funds(db)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Dashboard(
        funds=funds,
        requirements=requirements,
    )
