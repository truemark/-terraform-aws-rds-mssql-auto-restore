-- This script displays MSSQL recovery status in RDS
-- by first placing the result set in a temporary table
-- that disappears at the end of the transaction.
--
-- It formats the result set and allows SQL operations 
-- (sort, flexible conditions). Without this wrapper,
-- logic around the sp call is very limited.

DECLARE @ResultsVar TABLE
("task_id" INT,
    "task_type" VARCHAR(100),
    "db_name" VARCHAR(50),
    "pct_complete" VARCHAR(10),
    "duration_min" INT,
    "lifecycle" VARCHAR(100),
    "task_info" VARCHAR(5000),
    "last_updated" DATETIME,
    "created_at" DATETIME,
    "S3_object_arn" VARCHAR(500),
    "overwrite_S3_backup_file" INT,
    "KMS_master_key_arn" VARCHAR(100),
    "filepath" VARCHAR(5),
    "overwrite_file" INT
);

INSERT  @ResultsVar
EXEC msdb.dbo.rds_task_status;

SELECT task_id, pct_complete, duration_min, s3_object_arn, last_updated, lifecycle, task_type, db_name, created_at
FROM @ResultsVar
WHERE lifecycle not in ('ERROR','CANCELLED')
order by last_updated desc;

