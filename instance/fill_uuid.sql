-- Create a temporary table to store the generated UUIDs
CREATE TEMPORARY TABLE uuid_temp (id INTEGER PRIMARY KEY, uuid TEXT);

-- Insert rows into the temporary table with UUID values
INSERT INTO uuid_temp (id, uuid)
SELECT id, lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)), 2) || '-a' || substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)))
FROM myBudj where 1=1
and id_bank like "%****%";

--and id_bank = "" or id_bank = "0";


delete from uuid_temp;

-- Update the target column in your_table with the UUID values from the temporary table
UPDATE myBudj
SET id_bank = (SELECT uuid FROM uuid_temp WHERE myBudj.id = uuid_temp.id)
where id_bank = "" or id_bank = "0";

update myBudj
set mydesc = 
case when mydesc !="" then mydesc||'; '||id_bank
else id_bank
end
where id_bank like "%****%";


select uuid from uuid_temp a inner join myBudj b on a.id=b.id where uuid is null or uuid = "";

--where id_bank = "" or id_bank = "0";

-- Drop the temporary table
DROP TABLE uuid_temp;
