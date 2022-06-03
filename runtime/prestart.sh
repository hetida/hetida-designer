#!/usr/bin/env/bash
# retry several times

retry() {
    local max_num_retries=$1
    shift
    local retry_wait_seconds=$1
    shift
    local description=$1
    shift
    command_to_run=("$@")
    # the command must exit with non-zero code on failure.

    # Usage example:
    #     retry 10 5 "alembic migrations" alembic upgrade head

    for ((i = 1; i <= $max_num_retries; i += 1)); do
        if [[ i -gt 1 ]]; then echo "RETRY ${i} ..."; fi
        echo "RUNNING $description ..."
        "${command_to_run[@]}" && echo "RUNNING $description SUCCESS" && break ||
            (
                echo "FAILED TO RUN $description ON ATTEMPT $i"
                if (($i == $max_num_retries)); then
                    echo >&2 "ERROR: FINALLY FAILED TO RUN $description."
                    exit 1
                else
                    echo "WAITING $retry_wait_seconds SECONDS BEFORE RETRYING $description"
                    sleep $retry_wait_seconds
                fi
            )
    done
}

# Run migrations if this is run as backend service.
_is_backend_service="${HD_IS_BACKEND_SERVICE,,}" # to lower case
if [[ "$_is_backend_service" != "false" && "$_is_backend_service" != "yes" && "$_is_backend_service" != "y" && "$_is_backend_service" != "ok" && "$_is_backend_service" != "1" ]]; then
    retry 10 5 "alembic migrations" alembic upgrade head
    
    # Run autodeployment if autodeployment is wanted
    _autodeploy="${HETIDA_DESIGNER_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS,,}" # to lower case
    _overwrite="${HETIDA_DESIGNER_BACKEND_OVERWRITE_ON_AUTODEPLOY,,}" # to lower case
    if [[ "$_autodeploy" != "false" && "$_autodeploy" != "yes" && "$_autodeploy" != "y" && "$_autodeploy" != "ok" && "$_autodeploy" != "1" ]]; then
        echo "HETIDA_DESIGNER_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS=$HETIDA_DESIGNER_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS"
        echo "CHECK NUMBER OF DB ENTRIES"
        nof_db_entries=$( python -c "from hetdesrun.persistence.dbservice.revision import nof_db_entries; print(nof_db_entries())" | tail -1 )
        if [[ $nof_db_entries -eq 0 ]]; then
            echo "DB IS EMPTY"
            echo "RUNNING TRANSFORMATION REVISION DEPLOYMENT"
            python -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/", directly_into_db=True, update_component_code=False);'
        else
            echo "DB CONTAINS $nof_db_entries VALUES"
            echo "HETIDA_DESIGNER_BACKEND_OVERWRITE_ON_AUTODEPLOY=$HETIDA_DESIGNER_BACKEND_OVERWRITE_ON_AUTODEPLOY"
            if [[ "$_overwrite" != "false" && "$_overwrite" != "yes" && "$_overwrite" != "y" && "$_overwrite" != "ok" && "$_overwrite" != "1" ]]; then
                echo "RUNNING TRANSFORMATION REVISION DEPLOYMENT POSSIBLY OVERWRITING EXISTING DB ENTRIES"
                python -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/", directly_into_db=True, update_component_code=False);'
            else
                echo "OMITTING TRANSFORMATION REVISION DEPLOYMENT"
            fi
        fi
    fi
fi
