drivers = ["sqlite3"]
message = f"Choose a driver: {', '.join(drivers)}\n"
if input(message) == "sqlite3":
    from pkg.database import SqliteRepository

    sqlite = SqliteRepository("db.sqlite")
    script = open("migrations/sqlite/0.0.1.sql", "r").read()
    cursor = sqlite.connection.cursor()
    cursor.executescript(script)
    sqlite.connection.commit()
