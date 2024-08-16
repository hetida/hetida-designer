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

_true_equiv="@(|true|yes|y|ok|on|1)"

# Run migrations if this is run as backend service.
_is_backend_service="${HD_IS_BACKEND_SERVICE,,}" # to lower case
echo "HD_IS_BACKEND_SERVICE=$HD_IS_BACKEND_SERVICE"
if [[ "$_is_backend_service" == $_true_equiv ]]; then
    retry 10 5 "alembic migrations" alembic upgrade head

    # Run autodeployment if autodeployment is wanted
    _autodeploy="${HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS,,}"        # to lower case
    _preserve_db_entries="${HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY,,}"     # to lower case
    _allow_overwrite_released="${HD_BACKEND_ALLOW_OVERWRITE_RELEASED,,}" # to lower case
    echo "HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS=$HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS"
    if [[ "$_autodeploy" == $_true_equiv ]]; then
        echo "CHECKING NUMBER OF DB ENTRIES"
        nof_db_entries=$(python -c "from hetdesrun.persistence.dbservice.revision import nof_db_entries; print(nof_db_entries())" | tail -1)
        if [[ $nof_db_entries -eq 0 ]]; then
            echo "DB IS EMPTY"
            echo "RUNNING TRANSFORMATION REVISION AUTO DEPLOYMENT"
            python -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/", directly_into_db=True, update_component_code=False);'
        else
            echo "DB CONTAINS $nof_db_entries VALUES"
            echo "HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY=$HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY"
            if [[ "$_preserve_db_entries" == $_true_equiv ]]; then
                echo "SKIPPING TRANSFORMATION REVISION AUTO DEPLOYMENT"
            else
                echo "RUNNING TRANSFORMATION REVISION AUTO DEPLOYMENT POSSIBLY OVERWRITING EXISTING DB ENTRIES"
                if [[ "$_allow_overwrite_released" == $_true_equiv ]]; then
                    echo "INCLUDING RELEASED AND DEPRECATED TRANSFORMATION REVISIONS"
                    python -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/", directly_into_db=True, update_component_code=False);'
                else
                    echo "EXCEPT FOR RELEASED AND DEPRECATED TRANSFORMATION REVISIONS"
                    python -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/", directly_into_db=True, allow_overwrite_released=False, update_component_code=False);'
                fi
            fi
        fi
    else
        echo "SKIPPING TRANSFORMATION REVISION AUTO DEPLOYMENT"
    fi

    # Prepopulation of the virtual structure adapter
    python -c 'from hetdesrun.adapters.virtual_structure_adapter.utils import prepopulate_structure; prepopulate_structure();'

    if [[ -n "$HD_BACKEND_AUTOIMPORT_DIRECTORY" ]]; then
        echo "Trying autoimport from $HD_BACKEND_AUTOIMPORT_DIRECTORY"
        python -c 'from hetdesrun.exportimport.importing import import_importables; from hetdesrun.trafoutils.io.load import get_import_sources, load_import_sources; print(import_importables(load_import_sources(get_import_sources("'"$HD_BACKEND_AUTOIMPORT_DIRECTORY"'"))))'
        if [ "$?" -eq 0 ]; then
            echo "Successfully triggered auto import process. See details above."
        else
            echo "Auto importing failed. See details above."
        fi
    fi

fi
