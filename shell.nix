# with import <nixpkgs> { };
# fix nixpkgs commit:
with import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/79cb2cb9869d7bb8a1fac800977d3864212fd97d.tar.gz") {};

let
  pythonPackages = python38Packages; # Fix Python version from the used nixpkgs commit
  projectDir = toString ./.;
  runtimeDir = toString ./runtime;
  backendDir = toString ./backend;
  frontendDir = toString ./frontend;

  start-postgres = writeShellScriptBin "start-hd-postgres" ''
    echo "Stop possible running postgres server"
    pg_ctl -D .tmp/pg_dev_db stop || true
    echo "Clean up postgres data dir and recreate"    
    rm -fR ${projectDir}.tmp/pg_dev_db && initdb -D ${projectDir}.tmp/pg_dev_db
    echo "Starting postgres"
    # This starts postgres with the current user as db user and without password
    postgres -D ${projectDir}.tmp/pg_dev_db  -k ${projectDir}
  '';

  init-postgres = writeShellScriptBin "init-hd-postgres" ''
    
    # wait for postgres to be up
    set -e
    timer="2"
    until pg_isready -h ${projectDir} 2>/dev/null; do
        >&2 echo "Postgres is unavailable - sleeping for $timer seconds"
        sleep $timer
    done
    echo "Postgres ready. Creating the database!"

    createdb -h ${projectDir} hetida_designer_db
    echo "Created database"
  '';

  start-backend = writeShellScriptBin "start-hd-backend" ''
      cd ${backendDir}
      mvn spring-boot:run \
        -Dspring.datasource.url=jdbc:postgresql://localhost:5432/hetida_designer_db \
        -Dspring.datasource.username=$(whoami) \
        -Dorg.hetida.designer.backend.codegen=http://localhost:8090/codegen \
        -Dorg.hetida.designer.backend.codecheck=http://localhost:8090/codecheck \
        -Dorg.hetida.designer.backend.runtime=http://localhost:8090/runtime
      
      # -Dspring.profiles.active=test -Dspring.autoconfigure.exclude=org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration
  '';
  start-runtime = writeShellScriptBin "start-hd-runtime" ''
      cd ${runtimeDir}
      PORT=8090 python ./main.py
  '';

  start-frontend = writeShellScriptBin "start-hd-frontend" ''
      cd ${frontendDir}
      npm run start
  '';

  procfile = writeText "procfile" ''
      runtime: ${start-runtime}/bin/start-hd-runtime
      backend: ${start-backend}/bin/start-hd-backend
      frontend: ${start-frontend}/bin/start-hd-frontend
      postgres: ${start-postgres}/bin/start-hd-postgres
      initpostgres: ${init-postgres}/bin/init-hd-postgres
  '';
  
in pkgs.mkShell rec {
  name = "piptoolsPythonEnv";
  venvDir = "./runtime/nix_venv_hd_dev";
  buildInputs = [
    # A Python interpreter including the 'venv' module is required to bootstrap
    # the environment (>36)
    pythonPackages.python

    # This allows to execute some shell code to initialize a venv in $venvDir before
    # dropping into the shell
    # pythonPackages.venvShellHook

    # Those are dependencies that we would like to use from nixpkgs, which will
    # add them to PYTHONPATH and thus make them accessible from within the venv.
    # Note: they then can't be overriden in the venv!
    
    # pythonPackages.numpy
    # pythonPackages.requests

    # In this particular example, in order to compile any binary extensions they may
    # require, the Python modules listed in the hypothetical requirements.txt need
    # the following packages to be installed locally:
    taglib
    openssl
    git
    libxml2
    libxslt
    libzip
    zlib
    coreutils
    which
    sudo
    
    # libraries/packages necessary for typical data science Python libraries
    blas
    lapack
    gfortran
    gcc
    gccStdenv
    clangStdenv

    #
    
    postgresql

    # Java
    jdk8
    maven
    
    # Node
    nodejs-12_x
    chromium
    #google-chrome # for tests with chrome instead of chromium. Requires NIXPKGS_ALLOW_UNFREE=1
    # when running nix-shell

    # docker
    # docker-compose

    # podman
    # podman-compose

    overmind

  ];

#   # Run this command, only after creating the virtual environment
#   postVenvCreation = ''
#     unset SOURCE_DATE_EPOCH
#     pip install pip-tools==6.1.0
#     pip-sync requirements.txt
#   '';

#   # Now we can execute any commands within the virtual environment.
#   # This is optional and can be left out to run pip manually.
#   postShellHook = ''
#     # allow pip to install wheels
#     pip-sync requirements.txt
#     unset SOURCE_DATE_EPOCH
#   '';

    OVERMIND_PROCFILE = procfile;
    OVERMIND_NO_PORT = "1";
    OVERMIND_CAN_DIE = "runtime,initpostgres";

  shellHook = ''
    SOURCE_DATE_EPOCH=$(date +%s)

    echo "FINDING VENV at ${venvDir}"
    if [ -d "${venvDir}" ]; then
      echo "Skipping venv creation, '${venvDir}' already exists"
    else
      echo "Creating new venv environment in path: '${venvDir}'"
      # Note that the module venv was only introduced in python 3, so for 2.7
      # this needs to be replaced with a call to virtualenv
      ${pythonPackages.python.interpreter} -m venv "${venvDir}"
      
      "${venvDir}"/bin/pip install pip-tools==6.1.0
    fi

    # Under some circumstances it might be necessary to add your virtual
    # environment to PYTHONPATH, which you can do here too;
    PYTHONPATH=$PWD/${venvDir}/${pythonPackages.python.sitePackages}/:$PYTHONPATH

    # Additionally for pandas / numpy to work you need:
    # (https://discourse.nixos.org/t/python-package-with-runtime-dependencies/5522/9)
    export LD_LIBRARY_PATH=${lib.makeLibraryPath [stdenv.cc.cc]}      

    echo "ACTIVATING VENV AT ${venvDir}"
    source "${venvDir}/bin/activate"

    # As in the previous example, this is optional.
    # pip install -r /home/steffen/pro/hetida_designer/hetida-designer/runtime/requirements-dev.txt

    echo "INSTALL FIXED PIP, WHEEL AND PIP-TOOLS INTO VENV"
    "${venvDir}"/bin/pip install pip==21.1 wheel==0.36.2 pip-tools==6.1.0
    echo "START PIP-SYNC"
    "${venvDir}"/bin/pip-sync /home/steffen/pro/hetida_designer/hetida-designer/runtime/requirements.txt /home/steffen/pro/hetida_designer/hetida-designer/runtime/requirements-dev.txt
    
    echo "JAVA VERSION:"
    which java
    java -version

    echo "MAVEN VERSION:"
    which mvn
    mvn -version

    echo "install mvn deps"
    current_dir=$(pwd)    
    cd ./backend && mvn clean install
    cd $current_dir

    echo "You may run mvn test in the backend directory to test the backend."

    echo "NODE VERSION"
    which node
    node --version

    echo "NPM VERSION"
    which npm
    npm --version

    # Install node packages
    current_dir=$(pwd)
    cd ./frontend && npm ci # npm-ci = sync with package-lock.json
    cd $current_dir

  '';

}




# run via
#     NIXPKGS_ALLOW_UNFREE=1 nix-shell --pure shell.nix
# unfree for chrome-browser