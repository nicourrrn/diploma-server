from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users_db: dict[str, dict] = {}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(email: str, password: str):
    user = fake_users_db.get(email)
    if not user or not verify_password(password, user["password_hash"]):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = fake_users_db.get(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user


class StatusEnum(str, Enum):
    active = "Active"
    completed = "Completed"
    cancelled = "Cancelled"


class PriorityEnum(str, Enum):
    default = "Default"
    high = "High"


class CategoryEnum(str, Enum):
    food = "Food"
    medicine = "Medicine"
    equipment = "Equipment"
    other = "Other"


class RoleEnum(str, Enum):
    admin = "Admin"
    volunteer = "Volunteer"
    recipient = "Recipient"


# UserAccount Schema
class UserAccountBase(BaseModel):
    email: EmailStr
    bio: Optional[str] = None
    role: RoleEnum = RoleEnum.volunteer
    last_login: Optional[datetime] = None
    profile_pic: Optional[str] = None


class UserAccountCreate(UserAccountBase):
    password: str


class UserAccount(UserAccountBase):
    id: str

    class Config:
        from_attributes = True


# Specific Schema
class SpecificBase(BaseModel):
    name: str
    description: str


class Specific(SpecificBase):
    id: int

    class Config:
        from_attributes = True


# Volunteer Schema
class VolunteerBase(BaseModel):
    email: EmailStr
    phone: str
    name: str
    surname: str
    age: str
    available: bool


class VolunteerCreate(VolunteerBase):
    specific_id: int
    user_account_id: str


class Volunteer(VolunteerBase):
    id: str
    rating: Optional[float] = None
    total_reports: Optional[int] = None

    class Config:
        from_attributes = True


# Report Schema
class ReportBase(BaseModel):
    rating: int
    final_conclusion: str


class Report(ReportBase):
    id: str

    class Config:
        from_attributes = True


# Requirement Schema
class RequirementBase(BaseModel):
    name: str
    deadline: Optional[date] = None
    priority: PriorityEnum


class Requirement(RequirementBase):
    id: str

    class Config:
        from_attributes = True


# Item Schema
class ItemBase(BaseModel):
    name: str
    count: int
    category: CategoryEnum


class Item(ItemBase):
    id: str
    items_taken: Optional[int] = None

    class Config:
        from_attributes = True


# Fund Schema
class FundBase(BaseModel):
    name: str
    description: str
    mono_jar_url: str
    status: StatusEnum
    picture: str


class FundCreate(FundBase):
    report_id: Optional[str] = None
    requirement_id: str
    volunteer_id: str


class Fund(FundBase):
    id: str

    class Config:
        from_attributes = True


fake_funds_db: dict[str, FundCreate] = {
    "1": FundCreate(
        name="Fund 1",
        description="Description 1",
        mono_jar_url="https://www.google.com",
        status=StatusEnum.active,
        picture="https://www.google.com",
        requirement_id="1",
        volunteer_id="1",
    ),
    "2": FundCreate(
        name="Fund 2",
        description="Description 2",
        mono_jar_url="https://www.google.com",
        status=StatusEnum.active,
        picture="https://www.google.com",
        requirement_id="2",
        volunteer_id="2",
    ),
}


async def search_fund(query: str) -> list[FundBase]:
    funds = fake_funds_db.values()
    return list([f for f in funds if query in f.name])


# Recipient Schema
class RecipientBase(BaseModel):
    name: str


class RecipientCreate(RecipientBase):
    user_account_id: str


class Recipient(RecipientBase):
    id: str

    class Config:
        from_attributes = True


# FundRecipient Schema
class FundRecipientBase(BaseModel):
    fund_id: str
    recipient_id: str
    delivered_at: datetime


class FundRecipient(FundRecipientBase):
    class Config:
        from_attributes = True


# Volunteer Stats Schema
class VolunteerStats(BaseModel):
    id: str
    name: str
    surname: str
    total_reports: int
    average_rating: float
    completed_funds: int

    class Config:
        from_attributes = True


app = FastAPI()


@app.post("/register", response_model=Token)
def register_user(user: UserAccountCreate):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.email] = {
        "email": user.email,
        "password_hash": hashed_password,
        "bio": user.bio,
        "role": user.role,
        "last_login": None,
        "profile_pic": user.profile_pic,
    }
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/search", response_model=list[FundBase])
async def search(query: str) -> list[FundBase]:
    return await search_fund(query)
