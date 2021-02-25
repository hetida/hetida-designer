ALTER TABLE inputwiring RENAME COLUMN sourceId TO refId;
ALTER TABLE outputwiring RENAME COLUMN sinkId TO refId;

Alter TABLE inputwiring ADD COLUMN refIdType VARCHAR(255);
Alter TABLE inputwiring ADD COLUMN refKey VARCHAR(255);
Alter TABLE inputwiring ADD COLUMN type VARCHAR(255);

Alter TABLE outputwiring ADD COLUMN refIdType VARCHAR(255);
Alter TABLE outputwiring ADD COLUMN refKey VARCHAR(255);
Alter TABLE outputwiring ADD COLUMN type VARCHAR(255);
