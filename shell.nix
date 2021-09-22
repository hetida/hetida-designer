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
with import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/79cb2cb9869d7bb8a1fac800977d3864212fd97d.tar.gz") {};

let
  pythonPackages = python38Packages; # Fix Python version from the used nixpkgs commit
  projectDir = toString ./.;
  venvDir = toString ./runtime/nix_venv_hd_dev;
  runtimeDir = toString ./runtime;
  backendDir = toString ./backend;
  frontendDir = toString ./frontend;

  waitfor = stdenv.mkDerivation {
    name = "waitfor";
    propagatedBuildInputs = [pkgs.netcat pkgs.wget pkgs.cacert];
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

  start-postgres = writeShellScriptBin "start-hd-postgres" ''
    echo "Stop possible running postgres server"
    pg_ctl -D .tmp/pg_dev_db stop || true
    echo "Clean up postgres data dir and recreate"    
    rm -fR ${projectDir}/.tmp/pg_dev_db && initdb -D ${projectDir}/.tmp/pg_dev_db
    echo "Starting postgres"
    # This starts postgres with the current user as db user and without password
    postgres -D ${projectDir}/.tmp/pg_dev_db  -k ${projectDir}
  '';

  start-backend = writeShellScriptBin "start-hd-backend" ''
      set -e

      # wait for postgres to be up using the pg_isready utility
      timer="2"
      until pg_isready -h ${projectDir} 2>/dev/null; do
          >&2 echo "Postgres is unavailable - sleeping for $timer seconds"
          sleep $timer
      done

      echo "Postgres ready. Creating the database!"

      createdb -h ${projectDir} hetida_designer_db
      echo "Created database. Now starting Backend."      
    
      cd ${backendDir}
      SPRING_PROFILES_ACTIVE=default,overmind SPRING_DATASOURCE_USERNAME=$(whoami) mvn spring-boot:run \
        -Dspring.datasource.url=jdbc:postgresql://localhost:5432/hetida_designer_db \
        -Dspring.datasource.username=$(whoami) \
        -Dorg.hetida.designer.backend.codegen=http://localhost:8090/codegen \
        -Dorg.hetida.designer.backend.codecheck=http://localhost:8090/codecheck \
        -Dorg.hetida.designer.backend.runtime=http://localhost:8090/runtime
  '';

  start-runtime = writeShellScriptBin "start-hd-runtime" ''
      cd ${runtimeDir}
      PORT=8090 python ./main.py
  '';

  start-frontend = writeShellScriptBin "start-hd-frontend" ''
      cd ${frontendDir}
      npm run start
  '';

  init-components = writeShellScriptBin "init-hd-components" ''
      set -e
      cd ${runtimeDir}
      # wait for backend
      ${waitfor}/bin/waitfor -t 60 http://localhost:8080/api/info
      # Deploy components and workflows
      HETIDA_DESIGNER_BACKEND_API_URL=http://localhost:8080/api/ ${venvDir}/bin/python -c "from hetdesrun.utils import post_components_from_directory, post_workflows_from_directory; post_components_from_directory('./components'); post_workflows_from_directory('./workflows'); post_workflows_from_directory('./workflows2')"
  '';

  procfile = writeText "procfile" ''
      runtime: ${start-runtime}/bin/start-hd-runtime
      backend: ${start-backend}/bin/start-hd-backend
      frontend: ${start-frontend}/bin/start-hd-frontend
      postgres: ${start-postgres}/bin/start-hd-postgres
      initcomponents: ${init-components}/bin/init-hd-components
      
  '';
  
in pkgs.mkShell rec {
  name = "hetida-desiger-local-dev-environment";

  inherit projectDir venvDir;

  buildInputs = [
    # A Python interpreter including the 'venv' module is required to bootstrap
    # the environment (>36)
    python38Packages.python

    # Some libraries that may be required by Python libraries we want to use.
    taglib
    openssl
    git
    libxml2
    libxslt
    libzip
    zlib

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

    # Java
    jdk8
    maven
    
    # Node
    nodejs-12_x
    chromium # for tests
    #google-chrome 
    # you may use google-chrome for tests with chrome instead of chromium.
    # Requires NIXPKGS_ALLOW_UNFREE=1 when running nix-shell

    waitfor
    overmind

  ];

    OVERMIND_PROCFILE = procfile;
    OVERMIND_NO_PORT = "1";
    OVERMIND_CAN_DIE = "runtime,initcomponents";

    JUPYTER_CONFIG_DIR =  toString ./.jupyter;

  shellHook = ''
    set -e
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
    "${venvDir}"/bin/pip install pip==21.1 wheel==0.36.2 pip-tools==6.1.0 jupyterlab==3.0.16 jupyterlab-code-formatter==1.4.10
    echo "START PIP-SYNC"
    "${venvDir}"/bin/pip-sync ${projectDir}/runtime/requirements.txt ${projectDir}/runtime/requirements-dev.txt

    echo "Initialize/configure jupyter notebook in virtual environment"
    mkdir -p ${JUPYTER_CONFIG_DIR}
    "${venvDir}"/bin/pip install jupyterlab==3.0.16 jupyterlab-code-formatter==1.4.10

    echo '{"preferences": {"default_formatter": {"python": ["black"]}},}' > ${JUPYTER_CONFIG_DIR}/lab/user-settings/@ryantam626/jupyterlab_code_formatter/settings.jupyterlab-setting
    echo '{"shortcuts": [{"command": "jupyterlab_code_formatter:black", "keys": ["Ctrl K", "Ctrl M"], "selector": ".jp-Notebook.jp-mod-editMode"}]}' > ${JUPYTER_CONFIG_DIR}/lab/user-settings/@jupyterlab/shortcuts-extension/shortcuts.jupyterlab-settings

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

    set +e # disable exit on error!
  '';

}