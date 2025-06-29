USE sample;
DROP TABLE IF EXISTS your_table_name;

CREATE TABLE your_table_name (
    Name VARCHAR(100),
    Age INT,
    Email VARCHAR(100),
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
