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
