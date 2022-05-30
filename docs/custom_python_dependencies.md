# Adding custom Python dependencies

The hetida designer runtime is equipped with a good selection of standard Python libraries from the Python Data Science Stack like numpy, pandas, scikit-learn, scipy or tensorflow and more. 

While these may be sufficient for many use cases it is often necessary to use more and specialised libraries.

In order to add such custom dependencies they need to be available/installed in the runtime Docker image.

## Example 1: Adding a library via pip install

Create a new file Dockerfile `Dockerfile-runtime-custom-python-deps` and enter the following lines:

```dockerfile
FROM hetida/designer-runtime

RUN pip install xgboost==1.4.2
```

Now save the `docker-compose.yml` file as a new file with name `docker-compose-custom-dependencies.yml` and edit the hetida designer runtime service section as follows:

```yml
...
    hetida-designer-runtime:
    build:
        context: .
        dockerfile: Dockerfile-runtime-custom-python-deps
...
```

After that build the modified runtime image with

```bash
docker-compose -f docker-compose-custom-dependencies.yml build --no-cache hetida-designer-runtime
```

Now you can run your new setup with

```bash
docker-compose -f docker-compose-custom-dependencies.yml up -d
```

To test availability of the xgboost library you may write a small component importing it (`import xgboost`) and verify that the component can be run.

## Example 2: Adding libraries with pip-compile and pip-sync

Using pip-compile and pip-sync guarantees that the installed versions of your custom dependencies are compatible with the pre-installed dependencies.

To do this, start by creating a file `requirements-custom.in` (here in the runtime subdirectory of the repository) and enter

```
-c requirements.txt
-c requirements-base.txt
xgboost
```

You may add additional libraries to the file and even specify version ranges. See the [pip-tools](https://github.com/jazzband/pip-tools/) documentation for further details.

Next create a a new file Dockerfile `Dockerfile-runtime-custom-python-deps`with:

```dockerfile
FROM hetida/designer-runtime

USER root

COPY ./runtime/requirements-custom.in /app/requirements-custom.in

WORKDIR /app

RUN pip-compile --generate-hashes ./requirements-custom.in
RUN pip-sync ./requirements-base.txt ./requirements.txt ./requirements-custom.txt

USER hdrt_app
```

After that build the modified runtime image with

```bash
docker-compose -f docker-compose-custom-dependencies.yml build --no-cache hetida-designer-runtime
```

Now you can run your new setup with

```bash
docker-compose -f docker-compose-custom-dependencies.yml up -d
```

To test availability of the xgboost library you may write a small component importing it (`import xgboost`) and verify that the component can be run.
