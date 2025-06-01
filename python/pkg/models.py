from datetime import date
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
    none = "None"


class PriorityEnum(str, Enum):
    default = "Default"
    high = "High"
    none = "None"


class CategoryEnum(str, Enum):
    food = "Food"
    medicine = "Medicine"
    military_equipment = "Military Equipment"
    tactical_gear = "Tactical Gear"
    clothing = "Clothing"
    hygiene = "Hygiene"
    electronics_and_optics = "Electronics and Optics"
    power_supply = "Power Supply"
    vehicles = "Vehicles"
    fuel = "Fuel"
    construction = "Construction"
    communications = "Communications"
    tools = "Tools"
    drones = "Drones"
    winter_equipment = "Winter Equipment"
    animal_support = "Animal Support"
    other = "Other"


class RoleEnum(str, Enum):
    admin = "Admin"
    volunteer = "Volunteer"
    recipient = "Recipient"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Volunteer Schema
class VolunteerBase(BaseModel):
    email: EmailStr
    profile_pic: Optional[str] = None
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
    reserved_by: str | None = None


class Item(ItemBase, IdMixin):
    items_taken: Optional[int] = None


# Requirement Schema
class RequirementBase(BaseModel):
    name: str | None = None
    deadline: Optional[date] = None
    priority: PriorityEnum | None = None
    description: str | None = None


class RequirementCreate(RequirementBase):
    fund_id: str | None = None


class Requirement(RequirementBase, IdMixin): ...


# Fund Schema
class FundBase(BaseModel):
    name: str | None = None
    description: str | None = None
    mono_jar_url: str | None = None
    long_jar_id: str | None = None
    status: StatusEnum = StatusEnum.none
    picture: str | None = None


class FundCreate(FundBase):
    report_id: Optional[str] = None
    items: list[str] = []


class Fund(FundBase, IdMixin): ...


class FundRepresentative(Fund):
    volunteer_name: str
    volunteer_surname: str


# Recipient Schema
class RecipientBase(BaseModel):
    name: str
    email: EmailStr
    profile_pic: Optional[str] = None


class RecipientCreate(RecipientBase):
    user_account_id: str


class Recipient(RecipientBase, IdMixin): ...


class RequirementWithItems(Requirement):
    items: list[Item] = []
    recipient: Recipient | None = None


class RequirementWithItemsAndFund(RequirementWithItems):
    fund: list[Fund] = []


class DetailFund(FundBase, IdMixin):
    requirement: RequirementWithItems | None = None
    report: Report | None = None
    volunteer: Volunteer | None = None


class Dashboard(BaseModel):
    funds: list[DetailFund]
    requirements: list[RequirementWithItems]


class LoginResponse(BaseModel):
    access_token: str
    role: RoleEnum
    user: Volunteer | Recipient


class VolunteerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    age: Optional[str] = None
    available: Optional[bool] = None
    bio: Optional[str] = None
    profile_pic: Optional[str] = None


class RequirementWithVolonteer(Requirement):
    volunteer: Volunteer | None = None
    items: list[Item] = []
    recipient: Recipient | None = None


class Message(BaseModel):
    message: str


class MessageWithId(Message, IdMixin): ...
