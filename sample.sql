-- Reference:
-- https://www.mysqltutorial.org/mysql-cursor/
-- maxCompute SQL 不能使用 Cursor
SET @subject := 'math';
SELECT @name := `name` FROM user WHERE subject = @subject;
SELECT @name := group_concat(Distinct `name` SEPARATOR ',') FROM user WHERE subject = @subject;
SELECT * FROM user WHERE `name` = @name;
SELECT * FROM user WHERE find_in_set(name, @name);

-- in-memory employee table to hold distinct employee_id
DECLARE @i int
DECLARE @employee_id int
DECLARE @employee_table TABLE (
    idx smallint Primary Key IDENTITY(1,1)
    , employee_id int
)


-- populate employee table
INSERT @employee_table
SELECT distinct employee_id FROM SomeTable


-- enumerate the table
SET @i = 1
SET @numrows = (SELECT COUNT(*) FROM @employee_table)
IF @numrows > 0
    WHILE (@i <= (SELECT MAX(idx) FROM @employee_table))
    BEGIN


        -- get the next employee primary key
        SET @employee_id = (SELECT employee_id FROM @employee_table WHERE idx = @i)


    --
        -- do something with this employee
    --
    

        -- increment counter for next employee
        SET @i = @i + 1
    END


DELIMITER $$
DROP PROCEDURE IF EXISTS get_operator_indicators $$

CREATE PROCEDURE get_operator_indicators () 
    BEGIN
        DECLARE crs INT DEFAULT 0;

        WHILE crs < 10 DO
            INSERT INTO `continent`(`name`) VALUES ('cont'+crs);
            SET crs = crs + 1;
        END WHILE;
    END $$

DELIMITER ;

CREATE TEMPORARY TABLE MyList (Value CHAR(255));
INSERT myList(Value) SELECT DISTINCT name from user;
-- DECLARE @MyList TABLE (Value CHAR(255));

DECLARE @value VARCHAR(50)
BEGIN
DECLARE db_cursor CURSOR FOR SELECT Value FROM myList;
END
OPEN db_cursor   
FETCH NEXT FROM db_cursor INTO @value   

WHILE @@FETCH_STATUS = 0   
BEGIN   
       PRINT @value

       -- PUT YOUR LOGIC HERE
       -- MAKE USE OR VARIABLE @value wich is Data1, Data2, etc...

       FETCH NEXT FROM db_cursor INTO @value   
END   

CLOSE db_cursor   
DEALLOCATE db_cursor




DELIMITER $$
DROP PROCEDURE IF EXISTS get_operator_indicators $$
CREATE PROCEDURE get_operator_indicators (
    INOUT emailList varchar(4000)
)
BEGIN
    -- DECLARE finished INTEGER DEFAULT 0;
    -- DECLARE emailAddress varchar(100) DEFAULT "";

    -- -- declare cursor for employee email
    -- DEClARE curEmail 
    --     CURSOR FOR 
    --         SELECT email FROM employees;

    -- -- declare NOT FOUND handler
    -- DECLARE CONTINUE HANDLER 
    --     FOR NOT FOUND SET finished = 1;

    -- OPEN curEmail;

    -- getEmail: LOOP
    --     FETCH curEmail INTO emailAddress;
    --     IF finished = 1 THEN 
    --         LEAVE getEmail;
    --     END IF;
    --     -- build email list
    --     SET emailList = CONCAT(emailAddress,";",emailList);
    -- END LOOP getEmail;
    -- CLOSE curEmail;

END$$
DELIMITER ;