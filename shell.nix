####################################################################################################
#                                                                                                  #
#              Nix Shell / Overmind - based local development environment script                   #
#                                                                                                  #
####################################################################################################
#
# This nix script provides an isolated and reproducible environment for local development
# with live reload / restart functionality enabling fast-paced development without docker.
# This includes the main hetida designer application submodules (frontend, backend, runtime) and
# a postgres database. It uses overmind to orchestrate/manage the services instead of
# docker-compose.
#
# Prerequisites:
#     * Linux OS with a proper Bash. MacOS may work but has not been tested so far.
#     * Install Nix (https://nixos.org/guides/install-nix.html) Multi-user installation is
#       recommended — you should be able to run commands like `nix-shell` with your user account
#
# Usage instructions:
#     Run
#
#         nix-shell --pure
#
#     to get into the development environment shell. This may take a long time on first invocation
#     since it downloads and installs all programming languages and the necessary development tools
#     (including overmind) and configures them. Subsequent evocations will be much faster.
#
#     After that run
#
#         overmind start
#
#     to start the database and projects' submodules in development mode. It may take some minutes
#     for all services being available but finally you should be able to reach them at
#     the following urls:
#       frontend: http://localhost:4200
#       backend: http://localhost:8080/api/swagger-ui.html
#       runtime: http://localhost:8090/docs
#
#     You can now edit source code: Changes of frontend or runtime code should automatically restart
#     the corresponding service. For the Java backend you need to invoke
#         mvn compile
#     in the ./backend subdirectory to trigger a restart. We recommend to setup your Java IDE
#     accordingly.
#
# Notes:
#     * Occasionally you may need to stop everything and re-enter the development environment. To do
#       so press Ctrl+c to stop overmind and Ctrl-d to leave the nix-shell environment. After that
#       restart everything as described above.
#     * You should run this in a proper bash terminal. You may experience difficulties for example
#       in VSCode terminal due to high logging volume.


# fix nixpkgs commit:
with import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/f4a8d6d5324c327dcc2d863eb7f3cc06ad630df4.tar.gz")
{
  config = {
    permittedInsecurePackages = [
      "nodejs-14.21.3"
      # "openssl-1.1.1u"
    ];
  };
};
# 5b7cd5c39befee629be284970415b6eb3b0ff000
# 23.05: 4ecab3273592f27479a583fb6d975d4aba3486fe

let
  nixpkgs_for_nodejs14 = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/5b7cd5c39befee629be284970415b6eb3b0ff000.tar.gz") { };
  pythonPackages = python312Packages; # Fix Python version from the used nixpkgs commit
  projectDir = toString ./.;
  venvDirRuntime = toString ./runtime/nix_venv_hd_dev_runtime;
  venvDirPythonDemoAdapter = toString ./runtime/nix_venv_hd_dev_python_demo_adapter;
  runtimeDir = toString ./runtime;
  pythonDemoAdapterDir = toString ./demo-adapter-python;
  backendDir = toString ./backend;
  frontendDir = toString ./frontend;
  JUPYTER_CONFIG_DIR = toString ./.jupyter;

  waitfor = stdenv.mkDerivation {
    name = "waitfor";
    propagatedBuildInputs = [ pkgs.netcat pkgs.wget pkgs.cacert ];
    src = fetchurl {
      url = "https://raw.githubusercontent.com/eficode/wait-for/019516781dcca428cb0ee372e008e251e333f1ac/wait-for";
      # Hashes must be specified so that the build is purely functional
      # Simplest method to get the hash: add a false hash, try it out, copy the right one
      # from the error message and insert it.
      sha256 = "1gwysdigrcmbq3rj59h10w20cipl75g8jdf8bhvkncssl9lz0i54";
    };
    unpackPhase = ''
      echo "UNPACKING OVERRIDDEN"
    '';
    installPhase = ''
      mkdir -p $out/bin
      cp $src $out/bin/waitfor
      chmod +x $out/bin/waitfor
    '';
  };

  library_join = pkgs.symlinkJoin {
    name = "system_libraries_symlinked";
    paths = [ pkgs.zlib pkgs.glibc ];
    postBuild = "echo 'links added'; ls .";
  };

  symlinks_to_libs = runCommand "symlinks_to_some_libs" { } ''
    # Gather explicit symlinks to certain library pathes.
    # This is a simple workaround for Python imports not finding necessary libraries.
    # It allows to add the lib path of the result explicitely
    # to LD_LIBRARY_PATH in nix shell environments etc.
    #
    # Usage in nix shell / scripts:
    #      # (Remove double ' in following line)
    #      export LD_LIBRARY_PATH=''${lib.makeLibraryPath [stdenv.cc.cc (toString "''${symlinks_to_libs}") ]}
    # where "symlinks_to_libs is the result of this build.

    set -e

    mkdir -p $out/lib

    ln -s "${postgresql.lib}"/lib/libpq.so.5 "$out"/lib/libpq.so.5
    ln -s "${zlib}"/lib/libz.so.1 "$out"/lib/libz.so.1
    ln -s "${glibc}"/lib/libc-2.33.so "$out"/lib/libc-2.33.so
    ln -s "${glibc}"/lib/libc-2.33.so.1 "$out"/lib/libc-2.33.so.1
    ln -s "${glibc}"/lib/libc-2.38.so.1 "$out"/lib/libc-2.38.so.1
  '';

  prepare-venv = writeShellScriptBin "prepare-venv" ''
    set -e
    SOURCE_DATE_EPOCH=$(date +%s)

    prepare_venv() {
        local sub_project_dir=$1
        local venv_target_dir=$2
        local activate_venv="''${3:-false}"
        local configure_jupyter_in_venv="''${4:-false}"
        local run_test_python_command="''${5:-""}"

        if ! "$activate_venv" ; then
            local PIPT_EXPLICIT_VENV_TARGET_PATH
            local PIPT_PYTHON_INTERPRETER
            local LD_LIBRARY_PATH
            local PYTHONPATH
            local JUPYTER_CONFIG_DIR
        fi

        export PIPT_EXPLICIT_VENV_TARGET_PATH="$venv_target_dir"
        export PIPT_PYTHON_INTERPRETER="${pythonPackages.python.interpreter}"
        local OLD_PYTHONPATH="$PYTHONPATH"
        export PYTHONPATH="$PWD"/"$venv_target_dir"/${pythonPackages.python.sitePackages}/:"$OLD_PYTHONPATH"
        export LD_LIBRARY_PATH=${lib.makeLibraryPath [stdenv.cc.cc (toString "${symlinks_to_libs}") ]}

        export JUPYTER_CONFIG_DIR="$venv_target_dir"/.auto_created_jupyter_config

        local current_dir="$PWD"
        cd "$sub_project_dir"

        ./pipt sync

        cd "$current_dir"

        if [[ -n "$run_test_python_command" ]]; then
            # Test some imports (for system libraries missing / not found)
            echo "Run test Python command: $run_test_python_command"
            "$venv_target_dir"/bin/python -c "$run_test_python_command"
            echo "Test command completed."
        fi

        if "$configure_jupyter_in_venv" ; then
            echo "Configure jupyter notebook in virtual environment"
            echo "Write jupyter config to: $JUPYTER_CONFIG_DIR"
            rm -rf "$JUPYTER_CONFIG_DIR"
            mkdir -p "$JUPYTER_CONFIG_DIR"
            # "$venv_target_dir"/bin/pip install jupyterlab==3.0.16 jupyterlab-code-formatter==1.4.10

            mkdir -p "$JUPYTER_CONFIG_DIR"/lab/user-settings/@ryantam626/jupyterlab_code_formatter
            echo '{"preferences": {"default_formatter": {"python": ["black"]}},}' > "$JUPYTER_CONFIG_DIR"/lab/user-settings/@ryantam626/jupyterlab_code_formatter/settings.jupyterlab-setting
            mkdir -p "$JUPYTER_CONFIG_DIR"/lab/user-settings/@jupyterlab/shortcuts-extension
            echo '{"shortcuts": [{"command": "jupyterlab_code_formatter:black", "keys": ["Ctrl K", "Ctrl M"], "selector": ".jp-Notebook.jp-mod-editMode"}]}' > "$JUPYTER_CONFIG_DIR"/lab/user-settings/@jupyterlab/shortcuts-extension/shortcuts.jupyterlab-settings

        fi

        if "$activate_venv" ; then
            echo "Activating venv"
            source "$venv_target_dir/bin/activate"
        fi
        echo "finished prepare_venv"

    }

    prepare_venv "''${@}"
  '';


  prepare-runtime-venv = writeShellScriptBin "prepare-runtime-venv" ''
    set -e

    echo "BUILD AND ACTIVATE VENV AT ${venvDirRuntime}"
    source ${prepare-venv}/bin/prepare-venv "${projectDir}"/runtime "${venvDirRuntime}" true true "import numpy; import pandas; import sklearn; import scipy; # import tensorflow"
  '';

  prepare-python-demo-adapter-venv = writeShellScriptBin "prepare-python-demo-adapter-venv" ''
    set -e

    echo "BUILD AND ACTIVATING VENV AT ${venvDirPythonDemoAdapter}"
    source ${prepare-venv}/bin/prepare-venv "${projectDir}"/demo-adapter-python "${venvDirPythonDemoAdapter}" true false "import httpx; import pydantic; import numpy; import pandas"
  '';

  start-postgres = writeShellScriptBin "start-hd-postgres" ''

    echo "Stop possible running postgres server"
    pg_ctl -D .tmp/pg_dev_db stop || true
    echo "Clean up postgres data dir and recreate"

    # Note: Alternatively db encoding can be set in the initdb command with -E ... here.
    rm -fR ${projectDir}/.tmp/pg_dev_db && initdb -E UTF8 -D ${projectDir}/.tmp/pg_dev_db

    echo "Starting postgres"

    # This starts postgres with the current user as db user and without password
    postgres -D ${projectDir}/.tmp/pg_dev_db  -k ${projectDir}
  '';

  start-python-demo-adapter = writeShellScriptBin "start-python-demo-adapter" ''
    set -e
    source ${prepare-python-demo-adapter-venv}/bin/prepare-python-demo-adapter-venv
    cd ${pythonDemoAdapterDir}

    PORT=8092 python ./main.py
  '';

  start-runtime = writeShellScriptBin "start-hd-runtime" ''
    set -e

    source ${prepare-runtime-venv}/bin/prepare-runtime-venv

    cd ${runtimeDir}
    export HD_DATABASE_URL="postgresql+psycopg2://$(whoami):hetida_designer_dbpasswd@localhost:5432/hetida_designer_db"

    WRITABLE_SQLITE_TMP_DIR="$(mktemp -d)"
    export SQL_ADAPTER_SQL_DATABASES='
      [
        {
          "name": "sqlite example db (read only)",
          "key": "example_sqlite_db",
          "connection_url": "sqlite+pysqlite:///./tests/data/sql_adapter/example_sqlite.db?mode=ro",
          "append_tables": [],
          "replace_tables" : []
        },
        {
          "name": "writable sqlite db",
          "key": "temp_sqlite_db",
          "connection_url": "sqlite+pysqlite:///'"$WRITABLE_SQLITE_TMP_DIR"'/writable_sqlite.db",
          "append_tables": ["append_alert_table", "model_run_stats"],
          "replace_tables" : ["model_config_params"]
        }
      ]
    '
    export HETIDA_DESIGNER_ADAPTERS="demo-adapter-python|Python-Demo-Adapter|http://localhost:8092|http://localhost:8092,local-file-adapter|Local-File-Adapter|http://localhost:8080/adapters/localfile|http://localhost:8080/adapters/localfile,sql-adapter|SQL Adapter|http://localhost:8080/adapters/sql|http://localhost:8080/adapters/sql,kafka|Kafka Adapter|http://localhost:8080/adapters/kafka|http://localhost:8080/adapters/kafka,external-sources|External Sources|http://localhost:8080/adapters/external_sources|http://localhost:8080/adapters/external_sources"
    export HD_USE_AUTH=false
    export HD_MAINTENANCE_SECRET="maintenance"
    echo "WAIT FOR POSTGRES DB"
    sleep 5 # wait for stopping possibly existing postgres instances before trying
    # wait for postgres to be up using the pg_isready utility
    timer="2"
    until pg_isready -h ${projectDir} 2>/dev/null; do
        >&2 echo "Postgres is unavailable - sleeping for $timer seconds"
        sleep $timer
    done

    echo "CREATING DB SCHEMA"
    python -c "from sqlalchemy_utils import create_database; from hetdesrun.persistence.db_engine_and_session import get_db_engine; create_database(get_db_engine().url);"

    echo "STARTING RUNTIME"
    PORT=8080 \
    HD_USE_AUTH=false \
    HD_KAFKA_CONFIGS='
    {
        "test_kafka_config1": {
            "display_name": "Test Kafka Config No 1",
            "topic": "multi-ts-ingestion",
            "types": ["multitsframe"],
            "producer_config": {
              "bootstrap_servers": ["localhost:9094"]
            },
            "consumable": true
        },
        "test_kafka_config2": {
            "display_name": "Test Kafka Config No 2",
            "topic": "multi-ts-ingestion2",
            "types": null,
            "producer_config": {
              "bootstrap_servers": ["localhost:9094"]
            },
            "consumer_config": {
              "bootstrap_servers": ["localhost:9094"]
            },
            "consumable": true
        }
    }
    ' python main.py
    PORT=8080 python ./main.py
  '';

  start-frontend = writeShellScriptBin "start-hd-frontend" ''
    cd ${frontendDir}
    npm run start
  '';

  procfile = writeText "procfile" ''
    runtime: ${start-runtime}/bin/start-hd-runtime
    frontend: ${start-frontend}/bin/start-hd-frontend
    postgres: ${start-postgres}/bin/start-hd-postgres
    pythondemoadapter: ${start-python-demo-adapter}/bin/start-python-demo-adapter

  '';

in
pkgs.mkShell rec {
  name = "hetida-desiger-local-dev-environment";

  inherit projectDir venvDirRuntime;

  buildInputs = [
    # A Python interpreter including the 'venv' module is required to bootstrap
    # the environment (>36)
    python312Packages.python

    # Some libraries that may be required by Python libraries we want to use.
    taglib
    openssl
    git
    libxml2
    libxslt
    libzip
    zlib
    cacert
    curl
    # glib
    glibc
    glibcLocales

    # some helpful tools
    coreutils
    which
    sudo

    # additional libraries/packages necessary for typical data science Python libraries
    blas
    lapack
    gfortran
    gcc
    gccStdenv
    clangStdenv

    # Postgres

    postgresql
    postgresql.lib
    # Node
    nixpkgs_for_nodejs14.nodejs-14_x
    chromium # for tests
    #google-chrome
    # you may use google-chrome for tests with chrome instead of chromium.
    # Requires NIXPKGS_ALLOW_UNFREE=1 when running nix-shell

    waitfor
    overmind

  ];

  OVERMIND_PROCFILE = procfile;
  OVERMIND_NO_PORT = "1";
  OVERMIND_CAN_DIE = "runtime";


  shellHook = ''
    set -e
    SOURCE_DATE_EPOCH=$(date +%s)

    ${prepare-runtime-venv}/bin/prepare-runtime-venv

    ${prepare-python-demo-adapter-venv}/bin/prepare-python-demo-adapter-venv

    echo "NODE VERSION"
    which node
    node --version

    echo "NPM VERSION"
    which npm
    npm --version

    # Install node packages

    PACKAGE_JSON_HASH=$(./runtime/pipt _hash_multiple ./frontend/package-lock.json)

    if [[ -d ./frontend/node_modules ]] && [[ -e ./frontend/node_modules/package-lock.json.hash ]] && [[ "$PACKAGE_JSON_HASH" == "$(cat ./frontend/node_modules/package-lock.json.hash)" ]] ; then
        echo "$PACKAGE_JSON_HASH"
        echo "$(cat ./frontend/node_modules/package-lock.json.hash)"
        echo "--> Node modules probably still in sync. Not syncing again."
        echo "--> If you are not sure, simply delete ./frontend/node_modules subdir"
        echo "    and restart nix shell."
    else
        current_dir=$(pwd)
        cd ./frontend && npm ci
        # npm-ci = sync with package-lock.json. Could be improved:
        # Does not intelligently check by using
        # hashes
        cd $current_dir
        ./runtime/pipt _hash_multiple ./frontend/package-lock.json > ./frontend/node_modules/package-lock.json.hash
    fi



    set +e # disable exit on error!
  '';

}
