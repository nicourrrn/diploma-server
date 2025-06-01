from typing import Annotated
from fastapi import HTTPException, Header, Request
from fastapi.routing import APIRouter

from pkg.utils import (
    decode_access_token,
)

from pkg.models import *
from pkg.database import *


volunteer_router = APIRouter(prefix="/volunteer")


@volunteer_router.patch("/")
async def update_volunteer_endpoint(
    token: Annotated[str, Header()], volunteer_data: VolunteerUpdate, req: Request
):

    if not (decoded_token := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")

    db = req.app.state.db
    try:
        volunteer = await get_volunteer_by_email(db, decoded_token)
        volunteer.email = (
            volunteer_data.email if volunteer_data.email else volunteer.email
        )
        volunteer.phone = (
            volunteer_data.phone if volunteer_data.phone else volunteer.phone
        )
        volunteer.name = volunteer_data.name if volunteer_data.name else volunteer.name
        volunteer.surname = (
            volunteer_data.surname if volunteer_data.surname else volunteer.surname
        )
        volunteer.age = volunteer_data.age if volunteer_data.age else volunteer.age
        volunteer.profile_pic = (
            volunteer_data.profile_pic
            if volunteer_data.profile_pic
            else volunteer.profile_pic
        )
        await update_volunteer(db, decoded_token, volunteer)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))


@volunteer_router.get("/{volunteer_id}/funds")
async def get_volunteer_funds_endpoint(
    volunteer_id: str, req: Request
) -> list[DetailFund]:
    db = req.app.state.db
    funds = await get_funds_by_volunteer(db, volunteer_id)
    if not funds:
        raise HTTPException(status_code=404, detail="No funds found")
    detailed_funds = []
    for fund in funds:
        report = await get_report_by_fund(db, fund.id)
        volunteer = await get_volunteer_by_fund(db, fund.id)
        requirements = None
        try:
            requirements = await get_requirement_by_fund(db, fund.id)
            requirements.recipient = await get_recipient_by_requirement(
                db, requirements.id
            )
        except DatabaseException:
            requirement = None

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
    token: Annotated[str | None, Header()], req: Request, id: str = ""
) -> Volunteer:
    db = req.app.state.db

    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    if not (decoded_token := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        volunteer = await (
            get_volunteer_by_email(db, decoded_token)
            if id == ""
            else get_volunteer_by_id(db, id)
        )
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return volunteer


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

    # TODO: Fix searching by email while using id

    volunteer = await get_volunteer_by_email(db, email)  # Ensure volunteer exists
    try:
        funds = await get_volunteer_funds_for_dash(db, volunteer.id)
        for fund in funds:
            report = await get_report_by_fund(db, fund.id)
            volunteer = await get_volunteer_by_fund(db, fund.id)
            requirement = None
            try:
                requirement = await get_requirement_by_fund(db, fund.id)
                requirement.recipient = await get_recipient_by_requirement(
                    db, requirement.id
                )
            except DatabaseException:
                requirement = None
            detailed_funds.append(
                DetailFund(
                    **fund.model_dump(),
                    report=report,
                    volunteer=volunteer,
                    requirement=requirement,
                )
            )
        requirements = await get_volunteer_requirements_for_dash(db, email)
        for requirement in requirements:
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
