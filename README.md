# hetida designer

## What is hetida designer?

hetida designer is a graphical composition tool for analytical workflows based on the Python data science stack.

It aims to unify graphical composition of analytical methods on an equal footing with Python-based self-development in one user interface. To give an example: You can write your complete own visualization components on [plotly](https://plotly.com/python/) basis.

Another goal is to make the created workflows available for production use (e.g. as a web service) immediately without the need for further deployment steps. This includes a flexible adapter system for connecting to arbitrary data sources and sinks.![workflow editor](./docs/assets/screenshot-composition.png)

## Getting Started with hetida designer

This guide explains how to set up and get started with hetida designer on
your machine.

- [Getting started with Docker Compose (recommended)](#gs-docker-compose)
- [Use Standalone Docker Images](#gs-docker-standalone)
- [Code Contributors: Local development setup](#gs-local)
- [Tutorial: How to build and execute your first workflow with hetida designer?](#tutorial)
- [Adapter System](#adapter-system)
- [Running workflows in production](#running-in-production)
- [Security Hints](#security-hints)
- [Glossary: Important hetida designer concepts explained](#glossary)

All kinds of contributions are highly welcome. If you'd like to ask a question,
file a bug, or contribute bugfixes, improvements, or documentation, you'll find all
necessary information in our [contribution guidelines](./CONTRIBUTING.md).

### <a name="gs-docker-compose"></a> Getting started with Docker Compose (recommended)

#### Installing prerequisite dependencies

You'll have to install a recent version of [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/).
The exact procedure depends on your operating system. Follow the links to find out more about how to install these dependencies on your machine.

**Note for Windows Users**: On Windows, we recommend to configure Docker to use Linux Containers (the default setting) and git to use the checkout strategy *Checkout as-is, commit Unix-sytyle line endings*. In every case, make sure that these settings match.

#### Getting the source code

Once you have installed git, open up a terminal, move to the directory where you'd like
to install the hetida designer's source code, and execute the following command:

```shell
git clone https://github.com/hetida/hetida-designer.git
```

This should download the latest copy of the repository. Next, enter the newly
created source code directory and check out the release branch:

```shell
cd hetida-designer
git checkout release
```

#### Starting the hetida designer

**Note:** The following command will expose ports of designer containers to your local network and depending on your OS setup these ports may be exposed to the outside world allowing arbitrary code execution. If in doubt, [restrict all port rules to localhost](https://stackoverflow.com/a/48208039) by editing the docker-compose.yml accordingly.

Once you have the source code, docker and docker-compose properly set up, run

```shell
docker-compose up -d
```

to start the application. 

Make sure you execute this command from inside the root source code directory, i.e. the hetida-designer directory you checked out from git.

Wait some time for the hetida designer to start up (downloading / building of docker images may take some time the first time you are doing this).

#### Deployment of base component set into your installation

Now you should run

```bash
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_all; import_all("./transformations/", update_component_code=False);'
```

to install/deploy base components and some example workflows. **This step is only necessary the first time starting hetida designer!**

#### Opening hetida designer

Then open `http://localhost/` to access the hetida designer frontend.

You should see the designer's home page:

![hetida designer home screen](./docs/assets/hetida-designer-home.png)

Now, you are ready to follow our [tutorial](#tutorial) to build your first hetida designer
workflow and execute it right away!

#### Troubleshooting

The `-d` flag causes the containers to run in the background which means that you'll
not see log output by default. If the application does not seem to work, you can have
a look at the logs by executing `docker-compose logs -f`.

#### <a name="modify-ports"></a> Modifying ports.

To expose a port, you can modify `docker-compose.yml` and add/change the port binding. For example

```docker
  hetida-designer-frontend:
    ...
    ports:
      - 127.0.0.1:4200:8080
    ...
```

makes the frontend available at 127.0.0.1:4200.

You can expose the backend and runtime ports with

```
  hetida-designer-backend:
    ...
    ports:
      - 127.0.0.1:8080:8090

  hetida-designer-runtime:
    ...
    ports:
      - 127.0.0.1:8090:8090      
```

Changing the backend and/or runtime ports is quite a bit more involved. You'll have to also
update the corresponding configuration and rebuild the docker image or start the backend or runtime locally (see below).

### <a name="gs-docker-standalone"></a> Getting started using Standalone Docker Images

#### Installing prerequisite dependencies

You'll have to install a recent version of [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
and [docker](https://docs.docker.com/get-docker/).

**Note for Windows Users**: On Windows, we recommend to configure Docker to use Linux Containers (the default setting) and git to use the checkout strategy *Checkout as-is, commit Unix-sytyle line endings*. In every case, make sure that these settings match.

#### Getting the source code

Get the source code by entering the following commands in your terminal:

```shell
git clone git@github.com:hetida/hetida-designer.git
cd hetida-designer
git checkout develop
```

#### Application Submodules

The application consists of three submodules: a backend REST service, a runtime that
executes hetida designer workflows, and a frontend that allows you to interact with the
backend and the runtime to build components, workflows and test them. Note that both backend and runtime can be run together or as separated services. The later is recommended for security reasons and to be able to scale the runtime separately from the application backend.

You'll find corresponding Dockerfile in the source code's root folder. You can start (parts of) hetida designer in standalone docker containers as follows.

#### Frontend

1. Change `apiEndpoint` in `hetida_designer_config.json` to `http://localhost:8080/api`.
2. Run `docker build -t hetida/frontend -f ./Dockerfile-frontend .` to build the image.
3. Run `docker run -d -p 127.0.0.1:80:80 hetida/frontend` to run the frontend image. (use `-d` flag to run container in background)

#### Backend

1. Run `docker build -t hetida/backend -f ./Dockerfile-runtime .` to build the image.
2. Run `docker run -e HD_IS_RUNTIME_SERVICE=false --network hetida-designer-network -p 127.0.0.1:8080:8090 hetida/backend` to run the backend image. (use -d flag to run container in background). After this the backend OpenAPI UI is available at http://127.0.0.1:8090/docs.

#### Runtime

1. Run `docker build -t hetida/runtime -f ./Dockerfile-runtime .` to build the image.
2. Run `docker run -e HD_IS_BACKEND_SERVICE=false -p 127.0.0.1:8091:8090 hetida/runtime` to run the runtime image (use -d flag to run container in background). After this the runtime OpenAPI UI is available at http://127.0.0.1:8091/docs.

#### Backend + Runtime as one container
1. Run `docker build -t hetida/backend_runtime -f ./Dockerfile-runtime .` to build the image.
2. Run `docker run -p 127.0.0.1:8092:8090 hetida/backend_runtime` to run the image (use -d flag to run container in background). After this the combined backend + runtime OpenAPI UI is available at http://127.0.0.1:8092/docs.

### <a name="gs-local"></a> Setting up a Development Environment

We're excited that you'd like to work on the source code of hetida designer!
Contributions are highly welcome! See our [contributor guidelines](./CONTRIBUTING.md)
if you'd like to contribute your improvements back to us.

Follow the below steps to get ready to hack on the hetida designer source code...

#### Setting up a docker development environment

Make sure you have read and understood how to set up and start hetida designer using
[docker compose](#gs-docker-compose) and [docker](#gs-docker-standalone).

This is important, as usually you'll not want to develop on all three submodules of
the application at the same time. A partial docker setup will help you to have your
development environment up and running quickly as you'll only work locally on the
submodule that you'd like to change.

So first of all, follow the above instructions to set up a fully working local installation
either with [docker-compose](#gs-docker-compose) or with [standalone docker containers](#gs-docker-standalone). If using docker-compose, you should expose backend and runtime 
ports in the docker-compose file as is described under [Modifying Ports](#modify-ports). There is a `docker-compose-dev.yml` that builds images from your local development files which you can use via

```
docker-compose -f docker-compose-dev.yml up -d
```

Note that in this case it makes sense to run the base component deployment command using the locally
built runtime image via

```
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida-designer_hetida-designer-runtime -c 'from hetdesrun.exportimport.importing import import_all; import_all("./transformations/", update_component_code=False);'
```

In case your checked out repository directory has a different name replace `hetida-designer_hetida-designer-runtime` by `<directory name>_hetida-designer-runtime`.

Once you have the application running, only stop the container containing the submodule that you
want to work on. We use a monorepo approach, so you already have the source code for all submodules on your machine by now.

Depending on whether you want to work on the frontend, backend, or runtime, find the
instructions on setting up one of these modules for development below.

#### Frontend

Dependencies: Node 12.18.x and npm 6.14.x (other versions are not tested).

1. Navigate to the `frontend` folder.
2. Run `npm install` to install application dependencies.
3. Run `npm run start` to run the frontend on port 4200.

The frontend subdirectory also contains end-to-end tests via playwright documented [here](./frontend/end2end_tests.md).
#### Runtime and Backend

> **Note**: The backend was rewritten in Python for version 0.7. It is now developed together with the runtime.

Dependencies: Python 3.9 (other versions are not
tested, but higher versions will probably work as well). 

You may need additional packages like a C compiler (e.g. gcc) depending on your
OS's availability of precompiled packages for numerical libraries like **numpy**
or **scipy**. That said, development on Linux is recommended.

1. Navigate to the `runtime` folder.
2. Create, sync and activate virtual environmnet: `./pipt shell`

Now a development web server using a sqlite in-memory db can be started via
```
python main.py
```

If you want to develop against the postgres db running in the docker-compose dev environment the command is
```
HD_DATABASE_URL="postgresql+psycopg2://hetida_designer_dbuser:hetida_designer_dbpasswd@localhost:5430/hetida_designer_db" python main.py
```

In both cases the OpenAPI UI can be found at http://localhost:8000/docs.

Note that this starts runtime+backend combined. If you only want one of both you have to deactivate the other one by setting one of the environment variables `HD_IS_BACKEND_SERVICE` or `HD_IS_RUNTIME_SERVICE` to `false`.

When deactivating the backend endpoints you do not need to specify a database connection URL.
#### Running Runtime + Backend Tests

This assumes existence of the Python virtual environment as described above.

1. Navigate to the `runtime` folder.
2. Activate virtuale environment with `./pipt shell`.
3. Run `python -m pytest --cov=hetdesrun tests`.

## <a name="tutorial"></a> Tutorial

### How to build and execute your first workflow with hetida designer

In the hetida designer web user interface, click on "Add Workflow" in the Workflow side bar. 

![add_workflow](./docs/assets/first_workflow/add_workflow_button.png)

In the "Create new Workflow" dialog, enter a name (like "Demo") and for now leave everything else as it is. Click on "Create Workflow"

![create_workflow_dialog](./docs/assets/first_workflow/create_workflow_dialog.png) 

Next, you see the workflow editor which is empty. Switch to the component sidebar, open one of the category drawers, and drag and drop some components onto the workflow editor pane. Boxes appear indicating operators of your workflow (i.e. instances of the chosen components). 

In this tutorial, we create an example workflow for a univariate anomaly detection: A simple volatility detection on a time series. We add connections between operators by clicking on outputs on the right side of the boxes and then clicking on an input on the left side of another box. You can easily find the components used in the picture below by using the search filter in the component sidebar.

![volatility_example_without_io](./docs/assets/first_workflow/volatility_example_without_io.png)

Some Notes: 

* You can delete connections by right-clicking on them and selecting "Delete Link". You can also delete operators (boxes) through their right-click menu.

* Connection lines can be subdivided by left clicking on them and dragging one of the appearing handles to make them go around boxes. 
  
  ![connection_handles](./docs/assets/first_workflow/connection_handles.png)

* Connections must respect types of inputs / outputs (indicated by color). However, some inputs /outputs have type "Any" which means that everything can go out/into them.

* You can also drag Workflows from the Workflow sidebar as operators into a workflow (this can be nested!). For example, consider a workflow containing a data preparation pipeline that you want to use in an arbitrary amount of modeling workflows.

* You can only drag *released* components/workflows onto the workflow pane. This guarantees revision safety, i.e. once a workflow is released this revision of the workflow is fixed and cannot be changed anymore. This way, workflow executions can be reproduced at all points in time. To edit a released component/workflow a new revision has to be created.

Note that several inputs are unconnected and that one output (in our example this will be a result plot) is unconnected. There are no "Load Data from DB" or similar operators in our workflow. This is a point where hetida designer significantly differs from some similar-looking graphical analytics tools you may know: Data ingestion (and data egestion) is decoupled form the analytics and therefore fully flexible for production runs. Of course, this does not prevent you from writing components yourself that directly access data sources or data sinks -- but keep in mind that by doing this you loose the decoupling advantages and flexibility of the adapter system.

#### Configuring IO

We now have to configure which of these inputs should be fixed and which should be exposed to be dynamically connectable to appropriate data sources at execution time. Open the IO Dialog

![wf_io_dialog_button](./docs/assets/first_workflow/wf_io_dialog_button.png)

We configure the series input and the threshold input as "Dynamic" and provide exposed field labels "input_series" and "threshold" for them. Furthermore, window_size and window_timestamp_location are configured to be fixed values "180min" and "center" for this example. The resulting alert plot simply gets the field label "alert_plot". The result looks like this:

![configured_wf_io](./docs/assets/first_workflow/configured_wf_io.png)

Note that this configuration represents the interface of your workflow. The field labels provided here for dynamic input/output are exactly the JSON field names when calling the workflow as a web service or via a message queue in production. After clicking on "Save" this configuration is represented in the workflow editor pane:

![volatility_example_with_io](./docs/assets/first_workflow/volatility_example_with_io.png)

Fixed values get "fixed" to the corresponding operator while dynamic inputs/outputs are indicated by an attached (freely movable) plug.

#### Running the workflow

To run the workflow, click on the "Execute" button

![wf_run_button](./docs/assets/first_workflow/wf_run_button.png)

The execution dialog offers two modes for data ingestion into the workflow's dynamic inputs (as configured via the IO Configuration dialog):

* **Manual**: Here you can enter data directly or upload some JSON or CSV file from your computer.
* **Adapter**: Adapters allow to connect data sources (e.g. databases) to dynamic workflow input (and similar for outputs and sinks). They are small pieces of software which can be written individually for your specific data sources and data structures. They may present business views on data for easy selection in the execution dialog. More on that in documentation on the hetida designer adapter system

In your local installation, there probably is either no adapter or only the demo adapters  installed/available, so we choose "Manual" mode everywhere for this demo. For threshold we simply enter the value 600.0. For input_series you may copy or upload demo data from [volatility_detection_data.json](./runtime/demodata/volatility_detection_data.json): Click on the pencil-like symbol in the Input Value field of input_series) and on "Import JSON / CSV" in the upcoming dialog.

![input_series_demo_data_upload_dialog](./docs/assets/first_workflow/upload_demo_data_json.png)

Then, select the downloaded demo data file.

Click "Save" and run "Execute". The result pops up after short time:

![](./docs/assets/first_workflow/demo_wf_execution_result.png)

### Editing and writing components

#### Looking into components

Hetida designer makes it easy to look into / edit / create components. Components consist of Python code and an input / output configuration.

If you followed the tutorial above about workflow creation, you may have a direct look into a used component by right-clicking on an operator in your workflow, choosing "Show Details" and expanding the view

![expand_component_details](./docs/assets/first_workflow/expand_component_details.png)

This opens the component editor

![component_editor](./docs/assets/first_workflow/component_editor.png)

Note that this component revision is "released" (remember that you can only use released component revisions in a workflow). Therefore, the code editor does not allow to edit the code and you cannot change anything in the input / output configuration dialog either. You need to either create a new revision or a copy via one of the following buttons:

![new_revision_and_copy_button](./docs/assets/first_workflow/new_revision_and_copy_button.png)

However, for this tutorial we choose to create a completely new component:

#### Adding a new component

This can be done in the component sidebar via the "Add component" button.

![add_component_button](./docs/assets/first_workflow/add_component_button.png)

As for workflows, you have to provide at least a name in the appearing dialog window. For this example, we want to create an [Isolation Forest](https://en.wikipedia.org/wiki/Isolation_forest) component (similar to the existing Isolation Forest base component). We call our component "Isolation Forest Demo" and leave everything else as is

![create_component_dialog](./docs/assets/first_workflow/create_component_dialog.png)

The code editor opens with some absolute basic code doing nothing so far:

![code_editor_iso_foreststart](./docs/assets/first_workflow/code_editor_isoforest_start.png)

#### Configure IO

The next step is to configure input / outputs for our component. As for workflows, this is done via the IO Dialog. Open it via the button:

![component_io_dialog_button](./docs/assets/first_workflow/component_io_dialog_button.png)

It currently is rather empty. Click the add buttons

![component_empty_io_dialog_add_buttons](./docs/assets/first_workflow/component_empty_io_dialog_add_buttons.png)

and add inputs and outputs to produce the following result:

![component_io_filled](./docs/assets/first_workflow/component_io_filled.png)

Note how inputs and outputs (colored depending on selected type) appear in the displayed component box. Click save to get back to the code editor.

![code_editor_generated](./docs/assets/first_workflow/code_editor_generated.png)

Note that the generated code is adapted to the added IO configuration: Hetida designer tries to support you as long as you do not change the main function definition and the accompanying comments. 

#### Writing code

You may now start to enter custom code at several positions. Here, we first add import statements at the beginning

```python
from sklearn.ensemble import IsolationForest
import pandas as pd
```

and then replace the `pass` statement in the main furnction with

```python
    iso_forest = IsolationForest(n_jobs=-1, n_estimators=n_estimators)
    iso_forest.fit(train_data)

    dec_vals = pd.Series(iso_forest.decision_function(test_data), index=test_data.index)

    return {"decision_function_values": dec_vals, "trained_model": iso_forest}
```

The result looks like this:

![component_code_complete](./docs/assets/first_workflow/component_code_complete.png)

#### Test execution

Like workflows, components can be test executed via the "Execute" button.

![component_execution_button](./docs/assets/first_workflow/component_execution_button.png)

This is of course useful to verify that your component works and your code has no errors. We don't describe this step in detail here since it is completely analogous to the workflow execution. If you want to see an isolation forest component in action, there is an example workflow in the "Examples" category containing visualisations

![iso_forest_example_workflow](./docs/assets/first_workflow/iso_forest_example_workflow.png)

resulting in a visualisation of "what it learned":

![iso_forest_example_workflow_result](./docs/assets/first_workflow/iso_forest_example_workflow_result.png)

#### Releasing components

To be able to actually use your component in workflows it must be "released".  "Releasing" puts the component revision from "Draft Mode" to "Released Mode". A component revision in draft mode can be edited ad libitum but can not be used in workflows. A released component revision can not be edited anymore but can be used in workflows. One has to create a new revision of a released component if one wants to change how it works.

To release a component revision click on the "Publish" button

![component_release_button](./docs/assets/first_workflow/component_release_button.png)

After confirmation the symbol of your component changes in the component sidebar and the "New revision" button is available

![component_new_revision_button](./docs/assets/first_workflow/component_new_revision_button.png)

## <a name="adapter-system"></a>The Adapter System

hetida designer provides a flexible adapter system allowing integration of arbitrary data sources and sinks. It allows you to write your own custom adapters and makes them available in user interfaces making it possible to discover, browse and search data sources and sinks. One example for such a user interface is the hetida designer test execution dialog.

The adapter system allows to execute the exact same workflow on local csv files as inputs during experimentation/development and then switch to production database data simply through swapping adapters in a so-called "wiring" data structure.

Please start by reading the [introduction to the adapter system](./docs/adapter_system/intro.md) and follow the links to detailed explanations/documentation from there.

## <a name="running-in-production"></a>Running Workflows in production

It is one of the main goals of hetida designer to make it easy to run workflows in production scenarios. That is to make the transition from experimenting/development to production usage as smooth as possible.

There are several mechanisms that contribute to reaching this goal:

* The revision system: Workflows have revisions and a "released" workflow revision cannot be changed anymore. This makes production usage replicable.

* The adapter system allowing to simply swap adapters in a "wiring" data structure  from using local test data (e.g. csv files) to using data from databases

* The fact that execution of each workflow revision is immediately available through a web service endpoint – there is **no extra deployment step necessary**. 
  
  * Note that a Kafka consumer for the same pupose is also built into the backend and can be activated and configured via environment variables of the designer backend (see [documentation](./docs/execution/execution_via_kafka.md))

Read more about how to handle and write wirings and how to use the execution endpoints [here](./docs/execution/running_transformation_revisions.md)

## <a name="security-hints"></a>Security Hints

Hetida designer allows to execute arbitrary Python code. The included plain execution engine executes workflows in the same processes that serve the runtime component (which typically run as a (non-root) process in a Docker container if you use the runtime docker image). Knowing this, the following security measurements should at minimum be employed when working with the hetida designer:

* Never expose the frontend, the backend webservice, the database, and the runtime webservice to the public!
* It is strongly recommended to employ / activate authentification for frontend, backend, and runtime.
* **You should trust your users of the designer to the same degree that you trust a professional software engineer of your organization who is authorized to develop, run, and deploy arbitrary code (in production if hetida designer has access to your production systems e.g. via adapters)**
* You should restrict resource access (memory, cpu, networking bandwidth etc) of the docker service / docker container of the runtime in order to limit DoS attacks.
* You should never solely rely on the isolation that is provided by running something in a Docker container. The container should be isolated from other systems as much as possible. It should be monitored continuously for suspicious activities.
* Depending on your security requirements, you should consider further isolation methods like deferring every workflow execution to a one-time container or doing the same on process level. Do not hesitate to ask questions or create a feature request on the issue tracker.
* **If you do not feel comfortable employing security measures yourself, do not hesitate to ask for help from professional security consultants.**

## <a name="glossary"></a> Glossary - important concepts that help you understand how the hetida designer works

* **Hetida designer**: The software developed in this repository consisting of the web user interface, the backend, and the runtime.
* **Hetida**: A software platform for management and analysis of data (see https://hetida.de/). Hetida designer is a (stand-alone) module of the hetida platform.
* **Workflow, Workflow Revision**: A composition of analytical operations where outputs can be linked to inputs. Also has some IO configuration. Workflows have revisions and in the workflow editor one actually edits a workflow revision.
* **Component, Component Revision**: A piece of code together with some IO configuration that can be used/instantiated as operator in a workflow revision. Components have revisions and in the Component editor one actually edits a component revision.
* **Operator** An instance of either a workflow revision or a component revision used in a workflow. These are the "boxes" you can drag into the workflow editor. A workflow can contain multiple operators belonging to the same component or workflow revision. 
* **IO Config**: workflow and component revisions have an input/output configuration consisting of pairs of name and type for inputs and outputs. This is basically the interface that is employed when they are run or used as operators.
* **Wiring**: To run a workflow revision a wiring is necessary. A wiring maps data sources / data sinks via adapters to the inputs/outputs of the workflow revision IO config.
* **Adapter**: A small piece of software that provides access to data sources or data sinks in order to make them available for execution of workflow revisions. Typically, adapters connect to databases (SQL, NoSQL (e.g. timeseries databases). The base installation comes with some demo adapters and a local file adapter. You can of course [write your own adapter implementations](#adapter-system).
* **Draft Mode /  Released Mode**: Workflow and component revisions can be in either of these modes. They are only editable in Draft Mode. Through **Publishing** they are switched to Release Mode. They can only be used as operators when in Released Mode. This guarantees trackable execution runs. You can of course create a new revision to make further edits.
  **Deprecate**: Workflow and component revisions in Released Mode cannot be deleted, but they can be deprecated. This means they still exist and workflow revisions containing operators belonging to them can still be executed. They are not visible in the sidebars anymore and therefore you cannot create new operators from them. Additionally, the user interface marks existing operatores as deprecated and invites to update to another revision.
  **Delete**: Component and Workflow revisions in Draft Mode can be deleted.
  **Documentation**: To every workflow and component revision a markdown documentation can be written and used.
