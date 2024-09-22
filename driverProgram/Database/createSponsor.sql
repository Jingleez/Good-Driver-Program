CREATE TABLE sponsor 
(
    title       VARCHAR(20),
    USER        VARCHAR(20),
    sponsorID  INT,
    address     VARCHAR(40),
    phone       INT,
    email       VARCHAR(20),
    password    VARCHAR(255),
    image       BLOB,
    dateJoin   DATE,
    dateLeave  DATE
)