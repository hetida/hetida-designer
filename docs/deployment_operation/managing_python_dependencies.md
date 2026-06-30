# Python dependency management

## General notes

Often, workflow engines manage Python dependencies on the step / operator level, i.e. a virtual environment ("venv") with a fixed / ideally locked set of Python dependencies is bound to the data science artifacts (e.g. workflows, components).

While appropriate for automation tasks, this is suboptimal for production Data Science / analytics / Machine Learning for several reasons:

- For each step a new process must be started and managed:
  - This adds a startup latency to each step
  - Importing Python data science libraries often adds notable memory overhead and takes time
- It requires data to be serialized/deserialized in-between steps, which is not feasible for efficient operation on large analytical datasets

hetida designer runtime's execution simply runs in the same process which handles the execution request, with dependencies being those of the runtime container / process. No new processes are initialized and data is passed from one to the next operator by providing is as a reference/variable, i.e. data stays in-memory. See [design decisions](../design_decisions.md).

That means adding dependencies requires adding them to the runtime image. Consequently

- all executions share the same set of dependencies.
- dependencies cannot be added ad-hoc or via the user interface.
- a higher trust level towards user code is required, see [security hints](./security_hints.md), since operator execution is not sandboxed/isolated.

!!! tip "Remark"
Summarized there is a trade-off between convenience and isolation on the one side and production performance / efficiency on the other side. hetida designer opts for the latter.

!!! info "Runtime Included Dependencies"
Since dependencies cannot be added via user interface / on the fly, the hetida designer runtime docker image comes with a comprehensive set of Python Data Science dependencies pre-installed, like numpy, pandas, scikit-learn, scipy and many more.

## Adding custom Python dependencies

While the pre-installed dependencies may be sufficient for many use cases it is often necessary to employ more and specialised libraries.

In order to add such custom dependencies, as explained above, they need to be made available/installed in the runtime Docker image.

### Example 1: Adding a library via pip install

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
docker compose -f docker-compose-custom-dependencies.yml build --no-cache hetida-designer-runtime
```

Now you can run your new setup with

```bash
docker compose -f docker-compose-custom-dependencies.yml up -d
```

To test availability of the xgboost library you may write a small component importing it (`import xgboost`) and verify that the component can be run.

### Example 2: Adding libraries with uv pip compile and uv pip sync

Using uv lock and uv sync guarantees that the installed versions of your custom dependencies are compatible with the pre-installed dependencies.

To do this, start by creating a file `requirements-custom.in` (here in the runtime subdirectory of the repository) and enter

```
-c requirements.txt
-c requirements-base.txt
xgboost
```

You may add additional libraries to the file and even specify version ranges. See the [uv](https://docs.astral.sh/uv/) documentation for further details.

Next create a a new file Dockerfile `Dockerfile-runtime-custom-python-deps`with:

```dockerfile
FROM hetida/designer-runtime

USER root

COPY ./runtime/requirements-custom.in /app/requirements-custom.in

WORKDIR /app

RUN uv pip compile --generate-hashes ./requirements-custom.in -o ./requirements-custom.txt
RUN uv pip sync --system ./requirements-base.txt ./requirements.txt ./requirements-custom.txt

USER hd_app
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
docker compose -f docker-compose-custom-dependencies.yml build --no-cache hetida-designer-runtime
```

Now you can run your new setup with

```bash
docker compose -f docker-compose-custom-dependencies.yml up -d
```

To test availability of the xgboost library you may write a small component importing it (`import xgboost`) and verify that the component can be run.

## Employing separate runtime services with varying dependencies

Using `HD_AUTH_RUNTIME_ENGINE_URL_BY_ROLE`, [multiple runtime services](./varying_runtime_services.md) with varying dependencies and environment variables can be employed and are selected based on a token role.
