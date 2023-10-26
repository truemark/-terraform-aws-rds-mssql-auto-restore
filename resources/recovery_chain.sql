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

SELECT db_name, lifecycle, task_id, substring(s3_object_arn, charindex('/migration', s3_object_arn),100) as filename, pct_complete, duration_min, last_updated, task_type, task_info, s3_object_arn, created_at
FROM @ResultsVar
WHERE 1=1 
-- and last_updated > dateadd(hh,-24,GETDATE())
-- and db_name = 'LTReporting_1_UTC_A' 
-- and db_name = 'LTReporting_2_Mountain_A' 
-- and db_name = 'LTReporting_3_Pacific_A' 
-- and db_name = 'LTReporting_0_Eastern_A' 
-- and db_name = 'Administration' 
and db_name = 'Click_0_0_MarJunSepDec'
-- and db_name = 'Click_0_1_JanAprJulOct'
-- and db_name = 'Click_0_2_FebMayAugNov'
-- and db_name = 'LTPaging_0'
-- and db_name = 'LTPaging_1'
-- and db_name = 'Versioning'
-- and lifecycle <> 'ERROR'
-- and lifecycle = 'SUCCESS'
-- and lifecycle IN ( 'CREATED' , 'IN_PROGRESS','SUCCESS','CANCEL_REQUESTED')
-- and (lifecycle = 'IN_PROGRESS'
-- or lifecycle = 'CANCEL_REQUESTED')
-- ORDER BY task_id DESC;
-- ORDER BY filename DESC;
-- and lifecycle = 'CREATED'
order by last_updated desc;
-- ORDER BY filename desc, lifecycle;

