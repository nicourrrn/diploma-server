from abc import ABC
from sqlite3 import connect as sqlite_connect

import uuid
from pkg.models import RequirementCreate, ItemBase


class Repository(ABC):
    def __call__(self, query: str, *args):
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

    def __del__(self):
        self.connection.close()
