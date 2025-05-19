from typing import Annotated
from uuid import uuid1
from fastapi import File, HTTPException, Header, Request, UploadFile
from fastapi.routing import APIRouter

from pkg.utils import (
    create_access_token,
    decode_access_token,
    save_file,
)

from pkg.models import *
from pkg.database import *


router = APIRouter()

fund_router = APIRouter(prefix="/fund", tags=["api"])


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
        await update_requirement_with_fund(db, fund.requirement_id, fund_id)
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


@fund_router.post("/{fund_id}/report")
async def update_fund_report_endpoint(
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


@fund_router.patch("/{fund_id}/report")
async def upload_pdf_to_report(
    token: Annotated[str | None, Header()],
    report_pdf: UploadFile = File(...),
):
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    if not (decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")
    filename = f"{uuid1()}.pdf"
    save_file(report_pdf.file, filename)


requirement_router = APIRouter(prefix="/requirement", tags=["api"])


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
    requirement: RequirementCreate, req: Request
) -> Message:
    db = req.app.state.db
    await create_requirement(db, requirement)
    return Message(message="Requirement created")


@requirement_router.post("/{requirement_id}/items")
async def create_items_endpoint(
    requirement_id: str, items: list[ItemBase], req: Request
) -> Message:
    db = req.app.state.db
    await create_items(db, items, requirement_id)
    return Message(message="Items created")


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


@requirement_router.get("/categories")
def get_categories() -> dict[str, list[str]]:
    return {"categories": ["Food", "Medicine", "Equipment", "Other"]}


@requirement_router.delete("/{requirement_id}")
async def delete_requirement_endpoint(requirement_id: str, req: Request) -> Message:
    db = req.app.state.db
    await delete_requirement(db, requirement_id)
    return Message(message=f"Requirement with ID {requirement_id} deleted")


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


@router.get("/items")
async def get_items_endpoint(req: Request, query: str = "") -> list[Item]:
    db = req.app.state.db
    try:
        items = await (get_items(db, query) if query != "" else get_items(db))
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return items


@router.get("/profile")
async def get_profile_endpoint(
    token: Annotated[str, Header()], req: Request, user_mail: str = ""
) -> UserAccount:
    db = req.app.state.db
    if user_mail != "":
        try:
            return await get_user(db, user_mail)
        except DatabaseException as e:
            raise HTTPException(status_code=404, detail=str(e))

    decoded_token = decode_access_token(token).get("sub")
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        return await get_user(db, decoded_token)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))


volunteer_router = APIRouter(prefix="/volunteer", tags=["api"])


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
        await update_volunteer(db, decoded_token, volunteer)
        user = await get_user(db, decoded_token)
        user.bio = volunteer_data.bio if volunteer_data.bio else user.bio
        user.profile_pic = (
            volunteer_data.profile_pic
            if volunteer_data.profile_pic
            else user.profile_pic
        )
        if user.bio != None:
            await update_user_bio_by_email(db, decoded_token, user.bio)
        if user.profile_pic != None:
            await update_user_profile_pic_by_email(db, decoded_token, user.profile_pic)
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
    token: Annotated[str | None, Header()], req: Request, id: str = ""
) -> VolunteerWithUserAccount:
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
        user = await get_user(db, decoded_token)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return VolunteerWithUserAccount(
        **volunteer.model_dump(),
        user_account=user,
    )


@volunteer_router.post("/profile/photo")
async def upload_volunteer_photo_endpoint(
    token: Annotated[str | None, Header()],
    req: Request,
    volunteer_photo: UploadFile = File(...),
) -> dict[str, str]:
    db = req.app.state.db

    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    if not (decoded_token := decode_access_token(token).get("sub")):
        raise HTTPException(status_code=401, detail="Invalid token")
    filename = f"{uuid1()}.jpg"
    save_file(volunteer_photo.file, filename)
    try:
        await update_user_profile_pic_by_email(
            db, decoded_token, f"/uploads/{filename}"
        )
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"profile_pic": f"/uploads/{filename}"}


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
        print(e)
        raise HTTPException(status_code=404, detail=str(e))

    return Dashboard(
        funds=detailed_funds,
        requirements=updated_requirements,
    )


recipient_router = APIRouter(prefix="/recipient", tags=["api"])


@recipient_router.get("/{recipient_id}/requirements")
async def get_recipient_requirements_endpoint(recipient_id: str, req: Request) -> list:
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
