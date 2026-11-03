#! /usr/bin/env bash
# from https://github.com/tiangolo/uvicorn-gunicorn-docker/blob/master/docker-images/start.sh
set -e

_true_equiv="@(|true|yes|y|ok|on|1)"

if [ -f /app/app/main.py ]; then
    DEFAULT_MODULE_NAME=app.main
elif [ -f /app/main.py ]; then
    DEFAULT_MODULE_NAME=main
elif [ -f ./main.py ]; then
    DEFAULT_MODULE_NAME=main    
fi
MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

if [ -f /app/gunicorn_conf.py ]; then
    DEFAULT_GUNICORN_CONF=/app/gunicorn_conf.py
elif [ -f /app/app/gunicorn_conf.py ]; then
    DEFAULT_GUNICORN_CONF=/app/app/gunicorn_conf.py
else
    DEFAULT_GUNICORN_CONF=/gunicorn_conf.py
fi
export GUNICORN_CONF=${GUNICORN_CONF:-$DEFAULT_GUNICORN_CONF}
export WORKER_CLASS=${WORKER_CLASS:-"uvicorn.workers.UvicornWorker"}

# If there's a custom prestart.sh script in the /app directory or other path specified, run it
# before starting. The backend prepares the db itself, see main.py.
PRE_START_PATH=${PRE_START_PATH:-/app/prestart.sh}
if [ -f $PRE_START_PATH ]; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
fi

_is_pure_uvicorn="${HETIDA_DESIGNER_PURE_UVICORN,,}" # to lower case

if [[ -n "$HETIDA_DESIGNER_KAFKA_CONSUMPTION_MODE" ]]; then
    exec python main.py --container
else
    if [[ "$_is_pure_uvicorn" == $_true_equiv ]]; then
        # Pure uvicorn mode
        echo "Starting in pure uvicorn mode!"
        exec python main.py --container
    else
        # Start Gunicorn
        echo "WARNING: Gunicorn mode is deprecated and will be removed in a future version"
        echo "Starting in (deprecated!) gunicorn mode!"
        # gunicorn does not run main.py as main module, which prepares the db otherwise
        python -c 'from hetdesrun.persistence.db_preparation import prepare_db_before_gunicorn; prepare_db_before_gunicorn()'
        exec gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" "$APP_MODULE"
    fi

fi
