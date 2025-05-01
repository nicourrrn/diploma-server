from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class IdMixin(BaseModel):
    id: str

    class Config:
        from_attributes = True


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


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserAccountBase(BaseModel):
    email: EmailStr
    bio: Optional[str] = None
    role: RoleEnum = RoleEnum.volunteer
    last_login: Optional[datetime] = None
    profile_pic: Optional[str] = None


class UserAccountCreate(UserAccountBase):
    password: str


class UserAccount(UserAccountBase, IdMixin): ...


# # Specific Schema
# class SpecificBase(BaseModel):
#     name: str
#     description: str
#
#
# class Specific(SpecificBase, IdMixin): ...


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


class Volunteer(VolunteerBase, IdMixin):
    rating: Optional[float] = None
    total_reports: Optional[int] = None


# Report Schema
class ReportBase(BaseModel):
    rating: int
    final_conclution: str


class Report(ReportBase, IdMixin): ...


# Item Schema
class ItemBase(BaseModel):
    name: str
    count: int
    category: CategoryEnum


class Item(ItemBase, IdMixin):
    items_taken: Optional[int] = None


# Requirement Schema
class RequirementBase(BaseModel):
    name: str
    deadline: Optional[date] = None
    priority: PriorityEnum
    description: str | None


class RequirementCreate(RequirementBase):
    fund_id: str


class Requirement(RequirementBase, IdMixin): ...


# Fund Schema
class FundBase(BaseModel):
    name: str
    description: str
    mono_jar_url: str
    status: StatusEnum
    picture: str | None


class FundCreate(FundBase):
    report_id: Optional[str] = None
    requirement_id: str
    volunteer_id: str


class Fund(FundBase, IdMixin): ...


class FundRepresentative(Fund):
    volunteer_name: str
    volunteer_surname: str


# Recipient Schema
class RecipientBase(BaseModel):
    name: str


class RecipientCreate(RecipientBase):
    user_account_id: str


class Recipient(RecipientBase, IdMixin): ...


class RequirementWithItems(Requirement):
    items: list[Item] = []
    recipient: Recipient | None = None


class DetailFund(FundBase, IdMixin):
    requirement: RequirementWithItems | None = None
    report: Report | None = None
    volunteer: Volunteer | None = None


class Dashboard(BaseModel):
    funds: list[DetailFund]
    requirements: list[RequirementWithItems]


class LoginResponse(BaseModel):
    access_token: str
    user_account: UserAccount


class VolunteerWithUserAccount(Volunteer):
    user_account: UserAccount
