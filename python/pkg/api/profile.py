from typing import Annotated
from fastapi import HTTPException, Header, Request, UploadFile, File
from fastapi.routing import APIRouter
from pkg.utils import save_file

from pkg.utils import (
    create_access_token,
    decode_access_token,
)

from pkg.models import *
from pkg.database import *


profile_router = APIRouter(prefix="/profile")


@profile_router.post("/login")
async def login_endpoint(user_data: UserLogin, req: Request) -> LoginResponse:
    db = req.app.state.db
    try:
        user = await user_login(db, user_data.email, user_data.password)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    role: RoleEnum
    match user:
        case Volunteer():
            role = RoleEnum.volunteer
        case Recipient():
            role = RoleEnum.recipient
    token = create_access_token(
        data={"sub": user.email, "id": user.id},
    )

    return LoginResponse(
        access_token=token,
        role=role,
        user=user,
    )


@profile_router.get("/")
async def get_profile_endpoint(
    token: Annotated[str, Header()], req: Request, user_mail: str = ""
) -> Volunteer | Recipient:
    db = req.app.state.db
    decoded_token = decode_access_token(token).get("sub")
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        return await get_user(db, decoded_token if user_mail == "" else user_mail)
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))


@profile_router.post("/photo")
async def upload_profile_photo_endpoint(
    token: Annotated[str | None, Header()],
    req: Request,
    user_photo: UploadFile = File(...),
) -> Message:
    db = req.app.state.db

    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    decoded_token = decode_access_token(token)
    if not decoded_token.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")

    filename = f"{decoded_token['id']}.jpg"
    save_file(user_photo.file, filename)

    try:
        await update_user_profile_pic_by_email(
            db, decoded_token["sub"], f"/uploads/{filename}"
        )
    except DatabaseException as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Message(
        message=f"{filename} uploaded successfully",
    )
