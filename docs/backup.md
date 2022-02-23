# Backup and Restore

All components and workflows, their current wirings and documentation reside in the Postgres database of your hetida designer installation. So usually you want to backup this database.

For the default, local docker-compose setup this is a Postgres instance running as service **hetida-designer-db** in a Docker container.

The following commands run a simple postgres backup / restore for this setup using the pg_dump and pg_restore tools.

## Backup

This command writes a backup file named `<TIMESTAMP>-hd-backup.tar` into the current directory:

```
docker run --rm \
    -e "PGPASSWORD=hetida_designer_dbpasswd" \
    --name hd_postgres_backup \
    -v $(pwd):/backup_dir \
    --network hetida-designer_default \
    postgres:13 \
    bash -c \
    "pg_dump -h hetida-designer-db -p 5432 -U hetida_designer_dbuser -Fc hetida_designer_db > /backup_dir/$(date --iso-8601=seconds)-hd-backup.tar"
```

## Restore

Assuming the backup file to be imported is located in the current directory with name `hd-backup.tar` then a restore can be done via:

```
docker run --rm \
    -e "PGPASSWORD=hetida_designer_dbpasswd" \
    --name hd_postgres_backup \
    -v $(pwd):/backup_dir \
    --network hetida-designer_default \
    postgres:13 \
    bash -c \
    "pg_restore --clean --exit-on-error -v -h hetida-designer-db -p 5432 -U hetida_designer_dbuser -d hetida_designer_db < /backup_dir/hd-backup.tar"

```

