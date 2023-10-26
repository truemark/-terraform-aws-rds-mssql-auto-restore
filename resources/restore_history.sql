

select c.dbname, b.name as backupset_name, c.max_restore_date, b.first_lsn, b.last_lsn, b.checkpoint_lsn, b.backup_start_date, b.backup_finish_date, b.type, c.restore_history_id
from msdb..backupset b ,
    (select *
    from
        (SELECT y.destination_database_name as dbname, max(y.restore_date) as max_restore_date
        FROM msdb..restorehistory y
        group by y.destination_database_name)z,
        msdb..restorehistory a
    where 1=1
        and a.destination_database_name = z.dbname
        and z.max_restore_date = a.restore_date) c
where c.backup_set_id = b.backup_set_id
order by 1;
