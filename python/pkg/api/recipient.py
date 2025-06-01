from typing import Annotated
from fastapi import HTTPException, Header, Request
from fastapi.routing import APIRouter

from pkg.utils import decode_access_token

from pkg.models import *
from pkg.database import *


recipient_router = APIRouter(prefix="/recipient")


@recipient_router.get("/{recipient_id}/requirements")
async def get_recipient_requirements_endpoint(recipient_id: str, req: Request) -> list:
    db = req.app.state.db
    try:
        requirement = await get_requirements_by_recipient(db, recipient_id)
        if not requirement:
            raise HTTPException(
                status_code=404, detail="No requirements found for this recipient"
            )
        for i, _ in enumerate(requirement):
            requirement[i].recipient = await get_recipient_by_requirement(
                db, requirement[i].id
            )
        return requirement
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
        for i, _ in enumerate(requirements):
            requirements[i].recipient = recipient
        funds = await get_funds_by_recipient(db, recipient.id)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Dashboard(
        funds=funds,
        requirements=requirements,
    )


@recipient_router.get("{recipient_id}/funds")
async def get_recipient_funds_endpoint(
    recipient_id: str, req: Request
) -> list[DetailFund]:
    db = req.app.state.db
    funds = await get_funds_by_recipient(db, recipient_id)
    if len(funds) == 0:
        raise HTTPException(status_code=404, detail="No funds found")
    detailed_funds = []
    for fund in funds:
        report = await get_report_by_fund(db, fund.id)
        volunteer = await get_volunteer_by_fund(db, fund.id)
        requirements = await get_requirement_by_fund(db, fund.id)
        requirements.recipient = await get_recipient_by_requirement(db, requirements.id)

        detailed_funds.append(
            DetailFund(
                **fund.model_dump(),
                report=report,
                volunteer=volunteer,
                requirement=requirements,
            )
        )

    return detailed_funds
