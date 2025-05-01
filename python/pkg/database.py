import uuid
from pkg.models import (
    DetailFund,
    Fund,
    Item,
    Recipient,
    Report,
    RequirementCreate,
    ItemBase,
    RequirementWithItems,
    UserAccount,
    Volunteer,
)
from databases import Database as DatabaseCore

from pkg.utils import verify_password


class DatabaseException(Exception): ...


class Database:
    def __init__(self, db_name: str):
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
    Description TEXT,
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
                id=f["ID"],
                name=f["Name"],
                description=f["Description"],
                mono_jar_url=f["MonoJarUrl"],
                status=f["Status"],
                picture=f["Picture"],
            )
            for f in rows
        ]
    return []


async def get_fund_by_id(db: Database, fund_id: str) -> Fund:
    query = """
SELECT Fund.ID, Fund.Name, Fund.Description, Fund.MonoJarUrl, Fund.Status, Fund.Picture
FROM Fund WHERE Fund.ID = :fund_id
"""
    row = await db.connection.fetch_one(query=query, values={"fund_id": fund_id})
    if row:
        return Fund(
            id=row["ID"],
            name=row["Name"],
            description=row["Description"],
            mono_jar_url=row["MonoJarUrl"],
            status=row["Status"],
            picture=row["Picture"],
        )
    raise DatabaseException("Fund not found")


async def get_volunteer_by_fund(db: Database, fund_id: str) -> Volunteer:
    query = """
SELECT Volunteer.ID, Volunteer.Name, Volunteer.Surname, Volunteer.Email, Volunteer.Phone, Volunteer.Age, Volunteer.Available
FROM Volunteer 
JOIN Fund ON Volunteer.ID = Fund.Volunteer
WHERE Fund.ID = :fund_id
"""
    row = await db.connection.fetch_one(query=query, values={"fund_id": fund_id})
    if row:
        return Volunteer(
            id=row["ID"],
            name=row["Name"],
            surname=row["Surname"],
            email=row["Email"],
            phone=row["Phone"],
            age=row["Age"],
            available=row["Available"],
        )
    raise DatabaseException("Volunteer not found")


async def get_requirement_by_fund(db: Database, fund_id: str) -> RequirementWithItems:
    query = """
SELECT Requirement.ID, Requirement.Deadline, Requirement.Name, Requirement.Priority, Requirement.Description
FROM Requirement
JOIN Fund ON Requirement.Fund = Fund.ID
WHERE Fund.ID = :fund_id
"""
    row = await db.connection.fetch_one(query=query, values={"fund_id": fund_id})
    if row:
        items = await get_items_by_requirement(db, row["ID"])
        return RequirementWithItems(
            id=row["ID"],
            name=row["Name"],
            deadline=row["Deadline"],
            priority=row["Priority"],
            description=row["Description"],
            items=items,
        )
    raise DatabaseException("Requirement not found")


async def get_report_by_fund_id(db: Database, fund_id: str) -> Report:
    query = """
SELECT Report.ID, Report.Rating, Report.FinalConclution
FROM Report
JOIN Fund ON Report.ID = Fund.Report
WHERE Fund.ID = :fund_id
"""
    row = await db.connection.fetch_one(query=query, values={"fund_id": fund_id})
    if row:
        return Report(
            id=row["ID"],
            rating=row["Rating"],
            final_conclution=row["FinalConclution"],
        )
    raise DatabaseException("Report not found")


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
                id=f["ID"],
                name=f["Name"],
                description=f["Description"],
                mono_jar_url=f["MonoJarUrl"],
                status=f["Status"],
                picture=f["Picture"],
            )
            for f in rows
        ]

    return []


async def get_requirements(db: Database) -> list[RequirementWithItems]:
    query = " SELECT id, deadlinem, name, priority, description FROM Requirement"
    rows = await db.connection.fetch_all(query=query)
    if rows:
        return [
            RequirementWithItems(
                id=r["ID"],
                name=r["Name"],
                deadline=r["Deadline"],
                priority=r["Priority"],
                description=r["Description"],
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
                id=i["ID"],
                name=i["Name"],
                count=i["Count"],
                category=i["Category"],
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


async def user_login(db: Database, email: str, password: str) -> UserAccount:
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
    raise DatabaseException("Invalid email or password")


async def get_user_info(db: Database, email: str) -> UserAccount:
    query = "SELECT * FROM UserAccount WHERE Email = :email"
    user = await db.connection.fetch_one(query=query, values={"email": email})
    if user:
        return UserAccount(
            id=user["ID"],
            email=user["Email"],
            bio=user["Bio"],
            role=user["Role"],
            last_login=user["LastLogin"],
            profile_pic=user["ProfilePic"],
        )
    raise DatabaseException("User not found")


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
                id=f["ID"],
                name=f["Name"],
                description=f["Description"],
                mono_jar_url=f["MonoJarUrl"],
                status=f["Status"],
                picture=f["Picture"],
            )
            for f in rows
        ]
    return []


async def get_volunteer_requirements_for_dash(
    db: Database, volunteer_mail: str
) -> list[RequirementWithItems]:
    query = """
SELECT Requirement.ID, Requirement.Deadline, Requirement.Name, Requirement.priority, Requirement.Description
FROM Requirement
JOIN Fund ON Requirement.Fund = Fund.ID
JOIN Volunteer ON Fund.Volunteer = Volunteer.ID
WHERE Volunteer.Email = :volunteer_mail limit 5
"""
    rows = await db.connection.fetch_all(
        query=query, values={"volunteer_mail": volunteer_mail}
    )

    if rows:
        items = await get_items_by_requirement(db, rows[0]["ID"])
        return [
            RequirementWithItems(
                id=r["ID"],
                name=r["Name"],
                deadline=r["Deadline"],
                priority=r["Priority"],
                description=r["Description"],
                items=items,
            )
            for r in rows
        ]
    return []


async def get_fund_details(
    db: Database, fund_id: str
) -> tuple[Report, Volunteer, RequirementWithItems]:
    report = await get_report_by_fund_id(db, fund_id)
    volunteer = await get_volunteer_by_fund(db, fund_id)
    requirement = await get_requirement_by_fund(db, fund_id)
    requirement.recipient = await get_recipient_by_requirement(db, requirement.id)

    return (
        report,
        volunteer,
        requirement,
    )


async def get_recipient_by_requirement(db: Database, requirement_id: str) -> Recipient:
    query = """
SELECT Recipient.ID, Recipient.Name
FROM Recipient
JOIN FundRecipient ON Recipient.ID = FundRecipient.Recipient
JOIN Fund ON FundRecipient.Fund = Fund.ID
JOIN Requirement ON Fund.ID = Requirement.Fund
WHERE Requirement.ID = :requirement_id
"""
    row = await db.connection.fetch_one(
        query=query, values={"requirement_id": requirement_id}
    )
    if row:
        return Recipient(
            id=row["ID"],
            name=row["Name"],
        )
    raise DatabaseException("Recipient not found")


async def get_volunteer_by_email(db: Database, email: str) -> Volunteer:
    query = """
SELECT Volunteer.ID, Volunteer.Name, Volunteer.Surname, Volunteer.Email, Volunteer.Phone, Volunteer.Age, Volunteer.Available
FROM Volunteer
JOIN UserAccount ON Volunteer.UserAccount = UserAccount.ID
WHERE UserAccount.Email = :email
"""
    row = await db.connection.fetch_one(query=query, values={"email": email})
    if row:
        return Volunteer(
            id=row["ID"],
            name=row["Name"],
            surname=row["Surname"],
            email=row["Email"],
            phone=row["Phone"],
            age=row["Age"],
            available=row["Available"],
        )
    raise DatabaseException("Volunteer not found")


async def get_requirements_by_recipient(
    db: Database, recipient_id: str
) -> list[RequirementWithItems]:
    query = """
SELECT Requirement.ID, Requirement.Deadline, Requirement.Name, Requirement.Priority, Requirement.Description
FROM Requirement
JOIN Fund ON Requirement.Fund = Fund.ID
JOIN FundRecipient ON Fund.ID = FundRecipient.Fund
JOIN Recipient ON FundRecipient.Recipient = Recipient.ID
WHERE Recipient.ID = :recipient_id
"""
    rows = await db.connection.fetch_all(
        query=query, values={"recipient_id": recipient_id}
    )
    if rows:
        return [
            RequirementWithItems(
                id=r["ID"],
                name=r["Name"],
                deadline=r["Deadline"],
                priority=r["Priority"],
                description=r["Description"],
            )
            for r in rows
        ]
    return []


async def get_recipient_by_email(db: Database, email: str) -> Recipient:
    query = """
SELECT Recipient.ID, Recipient.Name
FROM Recipient
JOIN UserAccount ON Recipient.UserAccount = UserAccount.ID
WHERE UserAccount.Email = :email
"""
    row = await db.connection.fetch_one(query=query, values={"email": email})
    if row:
        return Recipient(
            id=row["ID"],
            name=row["Name"],
        )
    raise DatabaseException("Recipient not found")


async def get_five_last_funds(db: Database) -> list[DetailFund]:
    query = """
SELECT Fund.ID, Fund.Name, Fund.Description, Fund.MonoJarUrl, Fund.Status, Fund.Picture
FROM Fund
ORDER BY Fund.ID DESC
LIMIT 5
"""
    rows = await db.connection.fetch_all(query=query)
    result = []
    if rows:
        for f in rows:
            report, volunteer, requirement = await get_fund_details(db, f["ID"])
            result.append(
                DetailFund(
                    id=f["ID"],
                    name=f["Name"],
                    description=f["Description"],
                    mono_jar_url=f["MonoJarUrl"],
                    status=f["Status"],
                    picture=f["Picture"],
                    requirement=requirement,
                    report=report,
                    volunteer=volunteer,
                )
            )
    return result
