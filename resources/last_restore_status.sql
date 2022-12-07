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

SELECT v.db_name, v.lifecycle, v.task_id, substring(v.s3_object_arn, charindex('/migration', v.s3_object_arn),100) as filename, v.pct_complete, v.duration_min, v.last_updated, v.task_type, v.task_info, v.s3_object_arn, v.created_at
FROM @ResultsVar v
WHERE last_updated > dateadd(hh,-1,GETDATE())
and task_id = (select max(task_id) from @ResultsVar where db_name = v.db_name)
order by last_updated desc;

