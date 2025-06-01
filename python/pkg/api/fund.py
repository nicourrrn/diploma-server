from typing import Annotated
from uuid import uuid1
from fastapi import File, HTTPException, Header, Request, UploadFile
from fastapi.routing import APIRouter

from pkg.utils import (
    decode_access_token,
    save_file,
)

from pkg.models import *
from pkg.database import *


fund_router = APIRouter(prefix="/fund")


@fund_router.get("/")
async def search_funds_endpoint(req: Request, query: str = "") -> list[Fund]:
    db = req.app.state.db
    result = await get_funds(db, query)
    return result


@fund_router.get("/{fund_id}")
async def get_fund_by_id_endpoint(fund_id: str, req: Request) -> DetailFund:
    db = req.app.state.db

    try:
        fund = await get_fund_by_id(db, fund_id)
        report = await get_report_by_fund(db, fund_id)
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


@fund_router.post("/photo")
async def upload_fund_photo_endpoint(
    token: Annotated[str | None, Header()],
    req: Request,
    fund_id: str,
    fund_photo: UploadFile = File(...),
) -> dict[str, str]:
    db = req.app.state.db

    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    if not (decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")
    filename = f"{uuid1()}.jpg"
    save_file(fund_photo.file, filename)
    try:
        await update_fund_picture(db, fund_id, f"/uploads/{filename}")
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"profile_pic": f"/uploads/{filename}"}


@fund_router.post("/")
async def create_fund_endpoint(
    token: Annotated[str | None, Header()],
    req: Request,
    fund: FundCreate,
) -> MessageWithId:
    db = req.app.state.db
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    if not (volunteer_id := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        fund_id = await create_fund(db, fund, volunteer_id)
        await update_items_with_fund(db, fund.items, fund_id)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return MessageWithId(
        message="Fund created",
        id=fund_id,
    )


@fund_router.put("/{fund_id}")
async def update_fund_endpoint(
    token: Annotated[str | None, Header()],
    req: Request,
    fund_id: str,
    fund: FundCreate,
) -> Message:
    db = req.app.state.db
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    if not (decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        await update_fund_by_id(db, fund_id, fund)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Message(message="Fund updated")


@fund_router.get("/statuses")
async def get_fund_statuses_endpoint() -> list[StatusEnum]:
    return [status for status in StatusEnum]


@fund_router.post("/{fund_id}/report")
async def add_fund_report_endpoint(
    token: Annotated[str | None, Header()],
    req: Request,
    fund_id: str,
    report: ReportBase,
) -> Message:
    db = req.app.state.db
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    if not (decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        await add_report_by_fund_id(db, fund_id, report)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Message(message="Report added")


@fund_router.post("/{fund_id}/report/pdf")
async def upload_pdf_to_report(
    token: Annotated[str | None, Header()],
    fund_id: str,
    report_pdf: UploadFile = File(...),
) -> Message:
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    if not (decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")
    filename = f"{fund_id}.pdf"
    save_file(report_pdf.file, filename)
    return Message(
        message=f"Report PDF uploaded successfully: {filename}",
    )
