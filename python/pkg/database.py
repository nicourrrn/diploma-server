import uuid
from pkg.models import (
    Fund,
    Item,
    RequirementCreate,
    ItemBase,
    RequirementWithItems,
    UserAccount,
)
from databases import Database as DatabaseCore

from pkg.utils import verify_password


class Database:
    def __init__(self, db_name: str) -> None:
        self.connection = DatabaseCore(db_name)

    async def connect(self):
        await self.connection.connect()

    async def create_tables(self):
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS UserAccount (
    ID TEXT PRIMARY KEY,
    Email TEXT NOT NULL UNIQUE,
    PasswordHash TEXT NOT NULL,
    Bio TEXT,
    Role TEXT DEFAULT 'Volunteer' CHECK (Role IN ('Admin', 'Volunteer', 'Recipient')),
    LastLogin TIMESTAMP,
    ProfilePic TEXT
);
            """
        )
        await self.connection.execute(
            """
CREATE TABLE IF NOT EXISTS Specific (
    ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    Description TEXT
); """
        )

        await self.connection.execute(
            """
CREATE TABLE IF NOT EXISTS Volunteer (
    ID TEXT PRIMARY KEY,
    Email TEXT,
    Phone TEXT,
    Name TEXT,
    Surname TEXT,
    Age TEXT,
    Specific INTEGER,
    Available BOOLEAN NOT NULL,
    UserAccount TEXT,
    FOREIGN KEY (Specific) REFERENCES Specific(ID),
    FOREIGN KEY (UserAccount) REFERENCES UserAccount(ID)
); """
        )

        await self.connection.execute(
            """
        CREATE TABLE IF NOT EXISTS Report (
    ID TEXT PRIMARY KEY,
    Rating INTEGER,
    FinalConclution TEXT
); """
        )

        await self.connection.execute(
            """
CREATE TABLE IF NOT EXISTS Fund (
    ID TEXT PRIMARY KEY,
    Name TEXT,
    Description TEXT,
    MonoJarUrl TEXT,
    Report TEXT,
    Volunteer TEXT,
    Status TEXT CHECK (Status IN ('Active', 'Completed', 'Cancelled')),
    Picture TEXT,
    FOREIGN KEY (Report) REFERENCES Report(ID),
    FOREIGN KEY (Volunteer) REFERENCES Volunteer(ID)
); """
        )

        await self.connection.execute(
            """
CREATE TABLE IF NOT EXISTS Requirement (
    ID TEXT PRIMARY KEY,
    Deadline DATE,
    Name TEXT NOT NULL,
    Priority TEXT CHECK (Priority IN ('Default', 'High')),
    Fund TEXT,
    FOREIGN KEY (Fund) REFERENCES Fund(ID)
); """
        )

        await self.connection.execute(
            """
    CREATE TABLE IF NOT EXISTS Item (
    ID TEXT PRIMARY KEY,
    Name TEXT NOT NULL,
    Count INTEGER NOT NULL,
    Requirement TEXT,
    Category TEXT CHECK (Category IN ('Food', 'Medicine', 'Equipment', 'Other')),
    FOREIGN KEY (Requirement) REFERENCES Requirement(ID)
); """
        )

        await self.connection.execute(
            """
CREATE TABLE IF NOT EXISTS Recipient (
    ID TEXT PRIMARY KEY,
    Name TEXT NOT NULL,
    UserAccount TEXT,
    FOREIGN KEY (UserAccount) REFERENCES UserAccount(ID)
); """
        )
        await self.connection.execute(
            """
CREATE TABLE IF NOT EXISTS FundRecipient (
    Fund TEXT,
    Recipient TEXT,
    DeliveredAt TIMESTAMP,
    PRIMARY KEY (Fund, Recipient),
    FOREIGN KEY (Fund) REFERENCES Fund(ID),
    FOREIGN KEY (Recipient) REFERENCES Recipient(ID)
); """
        )

    async def disconnect(self):
        await self.connection.disconnect()


async def get_funds(db: Database, volunteer_id: str) -> list[Fund]:
    query = """
SELECT Fund.ID, Fund.Name, Fund.Description, Fund.MonoJarUrl, Fund.Status, Fund.Picture,
            Volunteer.Name, Volunteer.Surname
FROM Fund
JOIN Volunteer ON Fund.Volunteer = Volunteer.ID
WHERE Fund.Volunteer = :volunteer_id
"""

    rows = await db.connection.fetch_all(
        query=query, values={"volunteer_id": volunteer_id}
    )

    if rows:
        return [
            Fund(
                id=f["id"],
                name=f["name"],
                description=f["description"],
                mono_jar_url=f["mono_jar_url"],
                status=f["status"],
                picture=f["picture"],
            )
            for f in rows
        ]
    return []


async def delete_requirement(db: Database, requirement_id: str):
    query = "DELETE FROM Requirement WHERE ID = :requirement_id"
    await db.connection.execute(query=query, values={"requirement_id": requirement_id})


async def search_funds(db: Database, search_line: str) -> list[Fund]:
    query = """
SELECT Fund.ID, Fund.Name, Fund.Description, Fund.MonoJarUrl, Fund.Status, Fund.Picture,
            Volunteer.Name, Volunteer.Surname
FROM Fund
JOIN Volunteer ON Fund.Volunteer = Volunteer.ID
WHERE Fund.Name LIKE :search_line OR Volunteer.Name LIKE :search_line OR Volunteer.Surname LIKE :search_line
"""
    rows = await db.connection.fetch_all(
        query=query, values={"search_line": f"%{search_line}%"}
    )
    if rows:
        return [
            Fund(
                id=f["id"],
                name=f["name"],
                description=f["description"],
                mono_jar_url=f["mono_jar_url"],
                status=f["status"],
                picture=f["picture"],
            )
            for f in rows
        ]

    return []


async def get_requirements(db: Database) -> list[RequirementWithItems]:
    query = " SELECT id, deadlinem, name, priority FROM Requirement"
    rows = await db.connection.fetch_all(query=query)
    if rows:
        return [
            RequirementWithItems(
                id=r["id"],
                name=r["name"],
                deadline=r["deadline"],
                priority=r["priority"],
            )
            for r in rows
        ]
    return []


async def get_items_by_requirement(db: Database, requirement_id: str) -> list[Item]:
    query = (
        "SELECT id, name, count, category FROM Item WHERE requirement = :requirement_id"
    )
    rows = await db.connection.fetch_all(
        query=query, values={"requirement_id": requirement_id}
    )
    if rows:
        return [
            Item(
                id=i["id"],
                name=i["name"],
                count=i["count"],
                category=i["category"],
            )
            for i in rows
        ]
    return []


async def create_requirement(db: Database, requirement: RequirementCreate):
    requirement_id = str(uuid.uuid4())

    query = """
INSERT INTO Requirement (ID, Deadline, Name, Priority, Fund)
VALUES (:id, :deadline, :name, :priority, :fund)
"""
    await db.connection.execute(
        query=query,
        values={
            "id": requirement_id,
            "deadline": requirement.deadline,
            "name": requirement.name,
            "priority": requirement.priority,
            "fund": requirement.fund_id,
        },
    )


async def create_items(db: Database, items: list[ItemBase], requirement_id: str):
    for item in items:
        item_id = str(uuid.uuid4())
        query = """
INSERT INTO Item (ID, Name, Count, Requirement, Category)
VALUES (:id, :name, :count, :requirement_id, :category)
"""
        await db.connection.execute(
            query=query,
            values={
                "id": item_id,
                "name": item.name,
                "count": item.count,
                "requirement_id": requirement_id,
                "category": item.category,
            },
        )


async def user_login(db: Database, email: str, password: str) -> UserAccount | None:
    query = "SELECT * FROM UserAccount WHERE Email = :email"
    user = await db.connection.fetch_one(query=query, values={"email": email})
    if user and verify_password(password, user["PasswordHash"]):
        return UserAccount(
            id=user["ID"],
            email=user["Email"],
            bio=user["Bio"],
            role=user["Role"],
            last_login=user["LastLogin"],
            profile_pic=user["ProfilePic"],
        )


async def get_volunteer_funds_for_dash(db: Database, volunteer_mail: str) -> list[Fund]:
    query = """
SELECT Fund.ID, Fund.Name, Fund.Description, Fund.MonoJarUrl, Fund.Status, Fund.Picture
    FROM Fund
JOIN Volunteer ON Fund.Volunteer = Volunteer.ID
WHERE Volunteer.Email = :volunteer_mail
"""
    rows = await db.connection.fetch_all(
        query=query, values={"volunteer_mail": volunteer_mail}
    )

    if rows:
        return [
            Fund(
                id=f["id"],
                name=f["name"],
                description=f["description"],
                mono_jar_url=f["mono_jar_url"],
                status=f["status"],
                picture=f["picture"],
            )
            for f in rows
        ]
    return []


async def get_volunteer_requirements_for_dash(
    db: Database, volunteer_mail: str
) -> list[RequirementWithItems]:
    query = """
SELECT Requirement.ID, Requirement.Deadline, Requirement.Name, Requirement.priority
FROM Requirement
JOIN Fund ON Requirement.Fund = Fund.ID
JOIN Volunteer ON Fund.Volunteer = Volunteer.ID
WHERE Volunteer.Email = :volunteer_mail limit 5
"""
    rows = await db.connection.fetch_all(
        query=query, values={"volunteer_mail": volunteer_mail}
    )

    if rows:
        items = await get_items_by_requirement(db, rows[0]["id"])
        return [
            RequirementWithItems(
                id=r["id"],
                name=r["name"],
                deadline=r["deadline"],
                priority=r["priority"],
                items=items,
            )
            for r in rows
        ]
    return []
