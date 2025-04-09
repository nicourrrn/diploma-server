from abc import ABC
from sqlite3 import connect as sqlite_connect

import uuid
from pkg.models import RequirementCreate, ItemBase


class Repository(ABC):
    def __call__(self, query: str, *args):
        raise NotImplementedError

    def init_database(self):
        raise NotImplementedError

    def get_requirements(self) -> list:
        raise NotImplementedError

    def create_requirement(self, requirement: RequirementCreate):
        raise NotImplementedError

    def create_items(self, items: list[ItemBase], requirement_id: str):
        raise NotImplementedError

    def get_items_by_requirement(self, requirement_id: str) -> list:
        raise NotImplementedError

    def delete_requirement(self, requirement_id: str):
        raise NotImplementedError

    def search_funds(self, query: str) -> list:
        raise NotImplementedError

    def volunteer_funds(self, volunteer_id: str) -> list:
        raise NotImplementedError


class SqliteRepository(Repository):
    def __init__(self, db_path: str):
        self.connection = sqlite_connect(db_path)
        self.cursor = self.connection.cursor()

    def __call__(self, query: str, *args):
        self.cursor.execute(query, args)
        self.connection.commit()
        return self.cursor.fetchall()

    def volunteer_funds(self, volunteer_id: str) -> list:
        self.cursor.execute(
            """
SELECT Fund.ID, Fund.Name, Fund.Description, Fund.MonoJarUrl, Fund.Status, Fund.Picture,
         Volunteer.Name, Volunteer.Surname
FROM Fund
JOIN Volunteer ON Fund.Volunteer = Volunteer.ID
WHERE Fund.Volunteer = ?
""",
            (volunteer_id,),
        )
        result = self.cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "mono_jar_url": row[3],
                "status": row[4],
                "picture": row[5],
                "volunteer_name": row[6],
                "volunteer_surname": row[7],
            }
            for row in result
        ]

    def delete_requirement(self, requirement_id: str):
        self.cursor.execute(
            "DELETE FROM Requirement WHERE ID = ?",
            (requirement_id,),
        )
        self.connection.commit()

    def search_funds(self, query: str) -> list:
        self.cursor.execute(
            """
SELECT Fund.ID, Fund.Name, Fund.Description, Fund.MonoJarUrl, Fund.Status, Fund.Picture,
         Volunteer.Name, Volunteer.Surname
FROM Fund
JOIN Volunteer ON Fund.Volunteer = Volunteer.ID
WHERE Fund.Name LIKE ? OR Volunteer.Name LIKE ? OR Volunteer.Surname LIKE ? 
""",
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        )
        result = self.cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "mono_jar_url": row[3],
                "status": row[4],
                "picture": row[5],
                "volunteer_name": row[6],
                "volunteer_surname": row[7],
            }
            for row in result
        ]

    def get_requirements(self) -> list:
        self.cursor.execute("SELECT id, deadline, name, priority FROM Requirement")
        result = self.cursor.fetchall()
        return [
            {
                "id": row[0],
                "deadline": row[1],
                "name": row[2],
                "priority": row[3],
            }
            for row in result
        ]

    def get_items_by_requirement(self, requirement_id: str) -> list:
        self.cursor.execute(
            "SELECT id, name, count, category FROM ItemCreate WHERE requirement = ?",
            (requirement_id,),
        )
        result = self.cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "count": row[2],
                "category": row[3],
            }
            for row in result
        ]

    def create_requirement(self, requirement: RequirementCreate):
        requirement_id = str(uuid.uuid4())

        self.cursor.execute(
            """
INSERT INTO Requirement (ID, Deadline, Name, Priority, Fund)
VALUES (?, ?, ?, ?, ?)
""",
            (
                requirement_id,
                requirement.deadline,
                requirement.name,
                requirement.priority,
                requirement.fund_id,
            ),
        )
        self.connection.commit()

    def create_items(self, items: list[ItemBase], requirement_id: str):
        for item in items:
            item_id = str(uuid.uuid4())
            self.cursor.execute(
                """
INSERT INTO Item (ID, Name, Count, Requirement, Category)
VALUES (?, ?, ?, ?, ?)
""",
                (
                    item_id,
                    item.name,
                    item.count,
                    requirement_id,
                    item.category,
                ),
            )
            self.connection.commit()

    def init_database(self):
        self.cursor.executescript(
            """
    -- UserAccount table
    CREATE TABLE IF NOT EXISTS UserAccount (
        ID TEXT PRIMARY KEY,
        Email TEXT NOT NULL UNIQUE,
        PasswordHash TEXT NOT NULL,
        Bio TEXT,
        Role TEXT DEFAULT 'Volunteer' CHECK (Role IN ('Admin', 'Volunteer', 'Recipient')),
        LastLogin TIMESTAMP,
        ProfilePic TEXT
    );

    -- Specific table
    CREATE TABLE IF NOT EXISTS Specific (
        ID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Description TEXT
    );

    -- Volunteer table
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
    );

    -- Report table
    CREATE TABLE IF NOT EXISTS Report (
        ID TEXT PRIMARY KEY,
        Rating INTEGER,
        FinalConclution TEXT
    );

    -- Fund table
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
    );

    -- Requirement table
    CREATE TABLE IF NOT EXISTS Requirement (
        ID TEXT PRIMARY KEY,
        Deadline DATE,
        Name TEXT NOT NULL,
        Priority TEXT CHECK (Priority IN ('Default', 'High')),
        Fund TEXT,
        FOREIGN KEY (Fund) REFERENCES Fund(ID)
    );

    -- Item table
    CREATE TABLE IF NOT EXISTS Item (
        ID TEXT PRIMARY KEY,
        Name TEXT NOT NULL,
        Count INTEGER NOT NULL,
        Requirement TEXT,
        Category TEXT CHECK (Category IN ('Food', 'Medicine', 'Equipment', 'Other')),
        FOREIGN KEY (Requirement) REFERENCES Requirement(ID)
    );

    -- Recipient table
    CREATE TABLE IF NOT EXISTS Recipient (
        ID TEXT PRIMARY KEY,
        Name TEXT NOT NULL,
        UserAccount TEXT,
        FOREIGN KEY (UserAccount) REFERENCES UserAccount(ID)
    ); -- FundRecipient table
    CREATE TABLE IF NOT EXISTS FundRecipient (
        Fund TEXT,
        Recipient TEXT,
        DeliveredAt TIMESTAMP,
        PRIMARY KEY (Fund, Recipient),
        FOREIGN KEY (Fund) REFERENCES Fund(ID),
        FOREIGN KEY (Recipient) REFERENCES Recipient(ID)
    );

    -- ==== INSERT initial data ====

    -- Users
    INSERT OR IGNORE INTO UserAccount (ID, Email, PasswordHash, Role) VALUES
        ('u1', 'admin@example.com', 'hashed_admin_pw', 'Admin'),
        ('u2', 'volunteer@example.com', 'hashed_vol_pw', 'Volunteer'),
        ('u3', 'recipient@example.com', 'hashed_rec_pw', 'Recipient');

    -- Specific skills
    INSERT OR IGNORE INTO Specific (ID, Name, Description) VALUES
        (1, 'First Aid', 'Basic first aid and CPR certification'),
        (2, 'Logistics', 'Experience with managing aid deliveries'),
        (3, 'Translation', 'Fluent in multiple languages');

    -- Volunteer
    INSERT OR IGNORE INTO Volunteer (ID, Email, Phone, Name, Surname, Age, Specific, Available, UserAccount) VALUES
        ('v1', 'volunteer@example.com', '+380123456789', 'Ivan', 'Petrenko', '25', 1, 1, 'u2');

    -- Report
    INSERT OR IGNORE INTO Report (ID, Rating, FinalConclution) VALUES
        ('r1', 5, 'Excellent collaboration and results.');

    -- Fund
    INSERT OR IGNORE INTO Fund (ID, Name, Description, MonoJarUrl, Report, Volunteer, Status, Picture) VALUES
        ('f1', 'Support Kharkiv', 'Help with basic supplies in Kharkiv', 'https://monobank.ua/jar/abc123', 'r1', 'v1', 'Active', 'fund_pic.png');

    -- Requirement
    INSERT OR IGNORE INTO Requirement (ID, Deadline, Name, Priority, Fund) VALUES
        ('req1', '2025-04-30', 'Medical Supplies', 'High', 'f1');

    -- Item
    INSERT OR IGNORE INTO Item (ID, Name, Count, Requirement, Category) VALUES
        ('item1', 'Bandages', 100, 'req1', 'Medicine'),
        ('item2', 'Painkillers', 200, 'req1', 'Medicine');

    -- Recipient
    INSERT OR IGNORE INTO Recipient (ID, Name, UserAccount) VALUES
        ('rec1', 'Olena Danylchenko', 'u3');

    -- FundRecipient (delivery)
    INSERT OR IGNORE INTO FundRecipient (Fund, Recipient, DeliveredAt) VALUES
        ('f1', 'rec1', CURRENT_TIMESTAMP);
    """
        )
        self.connection.commit()

    def __del__(self):
        self.connection.close()
