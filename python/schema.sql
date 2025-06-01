CREATE TABLE UserAccount (
        ID TEXT PRIMARY KEY,
        Email TEXT NOT NULL UNIQUE,
        PasswordHash TEXT NOT NULL,
        Bio TEXT,
        Role TEXT DEFAULT 'Volunteer' CHECK (Role IN ('Admin', 'Volunteer', 'Recipient')),
        LastLogin TIMESTAMP,
        ProfilePic TEXT
    );
CREATE TABLE Specific (
        ID TEXT PRIMARY KEY,
        Name TEXT NOT NULL,
        Description TEXT
    );
CREATE TABLE Volunteer (
        ID TEXT PRIMARY KEY,
        Email TEXT,
        Phone TEXT,
        Name TEXT,
        Surname TEXT,
        Age TEXT,
        Specific INTEGER,
        Available BOOLEAN default true,
        UserAccount TEXT,
        FOREIGN KEY (Specific) REFERENCES Specific(ID),
        FOREIGN KEY (UserAccount) REFERENCES UserAccount(ID)
    );
CREATE TABLE Report (
        ID TEXT PRIMARY KEY,
        Rating INTEGER,
        FinalConclution TEXT
    );
CREATE TABLE Fund (
        ID TEXT PRIMARY KEY,
        Name TEXT,
        Description TEXT,
        MonoJarUrl TEXT,
        Report TEXT,
        Volunteer TEXT,
        Status TEXT CHECK (Status IN ('Active', 'Completed', 'Cancelled')),
        Picture TEXT,
        LongJarID TEXT default '',
        FOREIGN KEY (Report) REFERENCES Report(ID),
        FOREIGN KEY (Volunteer) REFERENCES Volunteer(ID)
    );
CREATE TABLE Requirement (
        ID TEXT PRIMARY KEY,
        Deadline DATE,
        Name TEXT NOT NULL,
        Priority TEXT CHECK (Priority IN ('Default', 'High')),
        Fund TEXT,
        Description TEXT,
        Recipient TEXT,
        FOREIGN KEY (Recipient) REFERENCES Recipient(ID)
    );
CREATE TABLE Item (
        ID TEXT PRIMARY KEY,
        Name TEXT NOT NULL,
        Count INTEGER NOT NULL,
        Requirement TEXT,
        Category TEXT CHECK (Category IN ('Food', 'Medicine', 'Equipment', 'Other')),
        ReservedBy TEXT,
        FOREIGN KEY (Requirement) REFERENCES Requirement(ID)
        FOREIGN KEY (ReservedBy) REFERENCES Fund(ID)
    );
CREATE TABLE Recipient (
        ID TEXT PRIMARY KEY,
        Name TEXT NOT NULL,
        UserAccount TEXT,
        FOREIGN KEY (UserAccount) REFERENCES UserAccount(ID)
    );
