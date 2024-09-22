CREATE TABLE driver
(
    firstName VARCHAR(20),
    middleName VARCHAR(20),
    lastName VARCHAR(20),
    user VARCHAR(20),
    driverID   INT,
    sponsorID  INT,
    points       INT,
    address     VARCHAR(40),
    phone       INT,
    email       VARCHAR(20),
    pwd         VARCHAR(255),
    image       BLOB,
    dateJoin   DATE,
    dateLeave  DATE
)