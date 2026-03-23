# hetida designer

## What is hetida designer?

hetida designer is an open source, scalable analytics engine for people wanting to do production data science and machine learning in Python without the hassles.

![screenshots](./docs/assets/screenshot-composition2.png)

### From a user point of view
On the one hand, hetida designer is aimed at **data scientists** and **subject matter experts** who can write Python data science code and want to deploy it productively. Once hetida designer is set up, these users can develop, test, manage, document and employ their Data Science artifacts in its UI on their own without having to aquire professional software engineering knowledge (git, yaml files, Dockerfiles / containerization, deployment and ci / cd, devops, writing Rest APIs ...). 

On the other hand, it enables **professional software or data engineers** to invoke, use, automate and integrate these artifacts and provide and receive data to/from them: Executing is just a REST call away, immediately. Adapters can be written to provide controlled and discoverable access to development as well as production data sources and sinks.

### From a technical point of view
hetida designer manages (versioning, lifecycle), exposes (Rest, Kafka) and scalably runs Python code and workflows while decoupling data access and result extraction via its adapter system. It furthermore integrates metadata in an opinionated way and treats visualization as a first class output, even for automated production runs.

hetida designer typically runs on Kubernetes to enable appropriate scaling, in particular for its runtime. Often it is part of a larger data (iot, timeseries) platform setup, like https://hetida.io/en/. A docker-compose setup is provided for small installations and trying out hetida designer.

hetida designer comes with a web UI, a backend / API, a runtime, a CLI Tool (hdctl) for maintenance and import/export tasks, built-in adapters for its adapter system and a set of base / example components and workflows. Additionally, experimental dashboard functionality is available, as well as simple scheduling.

### Main features
* managing Python data science code artifacts and workflows in a UI including versioning, lifecycle and documentation
* decoupling data provisioning from analytics
* no extra deployment steps required: Components (code) and workflows managed in the hetida designer UI are immediately usable / invokable via REST API or Kafka.
* visualization outputs (Plotly) are first-class citizens. One (surprisingly prevalent) use case for hetida designer is to provide custom Plotly visualizations for other applications' dashboarding.
* Data Scientists and Subject Matter Experts not required to learn git, yaml, ci/cd, devops, ... they can do everything in the UI. This enables collaboration with and between team members having varied skill level and exposure to software engineering. 
* modularity and reusability through nestable workflows and components being able to import other components.
* pytest unittesting and standard Python logging
* maintainable data science through versioning and lifecycle management
* clear and precise visualization of data flow in workflows: See at a glance which output connects to which input
* simple cron scheduling
* experimental dashboarding: Every component/workflow defines a dashboard.

### What is it not?
* an orchestration and automation framwork or platform (despite having simple built-in cron scheduling.)
* a low-code / no-code graphical programming environment:
    * User's are expected to write their own components at an early point.
    * hetida designer is far from providing a comprehensive and complete set of core components and workflows for data science.
    * workflows in hetida designer are just [DAGs](https://en.wikipedia.org/wiki/Directed_acyclic_graph): Looping and conditional logic need to be done in component code..
* a database
* a dashboarding solution
* a data platform. See https://hetida.io/en/ for a platform that integrates hetida designer as its analytics engine.
* an alternative to tableau, knime, rapidminer, alteryx, n8n, nodered, mlflow, kubeflow, kedro, bento, prefect, windmill.dev, dataiku, dagster, apache airflow, flyte, ... (add yours to the list when tempted to ask "So hetida designer is like X?"). hetida designer has its own distinct set of features and philosophy: hetida designer focusses on data science code and workflows (instead of models or experiments and general automation) and running them in production with modifiable data sources and sinks. Its philosophy is to make this possible without requiring data scientists and subject matter experts to grapple with git, yaml files, deployments, DevOps, and the like.

### More Screenshots 📸

<details>
<summary>Show more UI Screenshots</summary>

Home Tab
![home tab](./docs/assets/ui-screenshots/home-tab.png)

Component Editor
![component editor](./docs/assets/ui-screenshots/component-editor.png)

Workflow
![workflow](./docs/assets/ui-screenshots/workflow.png)

Test Execution Dialog
![test execution dialog](./docs/assets/ui-screenshots/test-execution-wiring-dialog.png)

Select Data From Adapter
![select data from adapter](./docs/assets/ui-screenshots/select-from-adapter.png)

Test execution result
![test execution result](./docs/assets/ui-screenshots/test-execution-result.png)

Markdown Documentation Editor
![documentation editor](./docs/assets/ui-screenshots/documentation-editor.png)

Details Dialog
![trafo details](./docs/assets/ui-screenshots/trafo-details-dialog.png)

Input/Output configuration dialog
![io dialog](./docs/assets/ui-screenshots/io-dialog.png)

Dashboard (experimental)
![Dashboard](./docs/assets/ui-screenshots/dashboard.png)

Scheduling
![scheduling](./docs/assets/ui-screenshots/scheduling.png)

Another Workflow Example
![iso forest example](./docs/assets/ui-screenshots/iso-forest-example.png)
</details>


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

If you'd like to ask a question, file a bug, or contribute bugfixes, improvements, or documentation, you'll find all
necessary information in our [contribution guidelines](./CONTRIBUTING.md).

### <a name="gs-docker-compose"></a> Getting started with Docker Compose (recommended)

#### Installing prerequisite dependencies

You'll have to install a recent version of [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git), [docker](https://docs.docker.com/get-docker/) and [docker compose](https://docs.docker.com/compose/install/).
The exact procedure depends on your operating system. Follow the links to find out more about how to install these dependencies on your machine.

**Note for Windows Users**: On Windows, we recommend to configure Docker to use Linux Containers (the default setting) and git to use the checkout strategy *Checkout as-is, commit Unix-style line endings*. In every case, make sure that these settings match.

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

#### Starting hetida designer

**Note:** The following command will expose ports of designer containers to your local network and depending on your OS setup these ports may be exposed to the outside world allowing arbitrary code execution. If in doubt, [restrict all port rules to localhost](https://stackoverflow.com/a/48208039) by editing the `docker-compose.yml` accordingly.

**Note:** By default [base component and worklfow deployment](./docs/base_component_deployment.md) will run automatically and fill the empty database.

Once you have the source code, docker and docker compose properly set up, run

```shell
docker compose up -d
```

to start the application. 

Make sure you execute this command from inside the root source code directory, i.e. the hetida-designer directory you checked out from git.

Wait some time for the hetida designer to start up (downloading / building of docker images may take some time the first time you are doing this).

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

```docker
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

see [standalone docker setup docs](./docs/standalone-docker-setup.md)

### <a name="gs-local"></a> Setting up a Development Environment
see [development setup docs](./docs/development-setup.md).

## <a name="tutorial"></a> Tutorial

see [tutorial](./docs/tutorial.md)


## <a name="adapter-system"></a>The Adapter System

hetida designer provides a flexible adapter system allowing integration of arbitrary data sources and sinks. It allows you to write your own custom adapters and makes them available in user interfaces making it possible to discover, browse and search data sources and sinks. One example for such a user interface is the hetida designer test execution dialog.

The adapter system allows to execute the exact same workflow on local csv files as inputs during experimentation/development and then switch to production database data simply through swapping adapters in a so-called "wiring" data structure.

Please start by reading the [introduction to the adapter system](./docs/adapter_system/intro.md) and follow the links to detailed explanations/documentation from there.

## <a name="running-in-production"></a>Running Workflows in production

It is one of the main goals of hetida designer to make it easy to run workflows in production scenarios. That is to make the transition from experimenting/development to production usage as smooth as possible.

There are several mechanisms that contribute to reaching this goal:

* The revision system: Workflows have revisions and a "released" workflow revision cannot be changed anymore. This makes production usage replicable.

* The adapter system allowing to simply swap adapters in a "wiring" data structure from using local test data (e.g. csv files) to using data from databases

* The fact that execution of each workflow revision is immediately available through a web service endpoint – there is **no extra deployment step necessary**. 
  
  * Note that a Kafka consumer for the same purpose is also built into the backend and can be activated and configured via environment variables of the designer backend (see [documentation](./docs/execution/execution_via_kafka.md))

Read more about how to handle and write wirings and how to use the execution endpoints [here](./docs/execution/running_transformation_revisions.md)

## <a name="security-hints"></a>Security Hints

Hetida designer allows to execute arbitrary Python code. The included plain execution engine executes workflows in the same processes that serve the runtime component (which typically run as a (non-root) process in a Docker container if you use the runtime docker image). There is no isolation / sandboxing both in-between operators of a workflow and different executions (of the same or different components/workflows).

This is intentional, since hetida designer has a focus on data science and therefore needs to avoid expensive serialisation/deserialisation of mass data as well as the overhead of loading resource-heavy data science libraries like pandas, scipy, etc. each time an execution is triggered. Note that here hetida designer significantly differs from more "business automation" workflow engines.

Knowing this, the following security measurements should at minimum be employed when working with the hetida designer:

* Never expose the frontend, the backend webservice, the database, and the runtime webservice to the public!
* It is strongly recommended to employ / activate authentification for frontend, backend, and runtime.
* **MOST IMPORTANT: You should trust your users of the designer to the same degree that you trust a professional software engineer of your organization who is authorized to develop, run, and deploy arbitrary code (in production if hetida designer has access to your production systems e.g. via adapters)**
* You should restrict resource access (memory, cpu, networking bandwidth etc) of the docker service / docker container of the runtime in order to limit DoS attacks.
* You should restrict the runtime container to only have configured the absolutely necessary secrets and permissions
* You should never solely rely on the isolation that is provided by running something in a Docker container. The container should be isolated from other systems as much as possible. It should be monitored continuously for suspicious activities.
* Depending on your security requirements, you should consider further isolation methods like deferring every workflow execution to a one-time container or doing the same on process level. Do not hesitate to ask questions or create a feature request on the issue tracker.
* **If you do not feel comfortable employing security measures yourself, do not hesitate to ask for help from professional security consultants.**

## <a name="glossary"></a> Glossary - important concepts that help you understand how the hetida designer works

![wiring-concept](./docs/diagrams/wiring-concept.excalidraw.svg)

* **Hetida designer**: The software developed in this repository consisting of the web user interface, the backend, and the runtime.
* **Hetida**: A analytical iot/timeseries platform (see https://hetida.io/en/). Hetida designer is a (stand-alone, open source) module of the hetida platform.
* **Workflow, Workflow Revision**: A composition of analytical operations where outputs can be linked to inputs. Also has some IO configuration. Workflows have revisions and in the workflow editor one actually edits a workflow revision.
* **Component, Component Revision**: A piece of code together with some IO configuration that can be used/instantiated as operator in a workflow revision. Components have revisions and in the Component editor one actually edits a component revision.
* **Operator** An instance of either a workflow revision or a component revision used in a workflow. These are the "boxes" you can drag into the workflow editor. A workflow can contain multiple operators belonging to the same component or workflow revision.
* **Transformation, Transformation Revision**: An umbrella term for the entities “Workflow” and “Component” or respectively "Workflow Revision" and "Component Revision".
* **IO Config**: workflow and component revisions have an input/output configuration consisting of pairs of name and type for inputs and outputs. This is basically the interface that is employed when they are run or used as operators.
* **Wiring**: To run a workflow revision a wiring is necessary. A wiring maps data sources / data sinks via adapters to the inputs/outputs of the workflow revision IO config. It consists of input wirings and output wirings.
* **Adapter**: A small piece of software that provides access to data sources or data sinks in order to make them available for execution of workflow revisions. Typically, [adapters](./docs/adapter_system/intro.md) connect to databases (SQL, NoSQL (e.g. timeseries databases)), blob storage, files, external APIs and more. The base installation comes with several [builtin adapters](./docs/adapter_system/builtin_adapters.md). You can of course [write your own adapter implementations](#adapter-system).
* **Draft Mode /  Released Mode**: Workflow and component revisions can be in either of these modes. They are only editable in Draft Mode. Through **Publishing** they are switched to Release Mode. A workflow can only be released if all operators refer to released workflows/components. This guarantees trackable execution runs for released workflows/components. You can of course create a new revision to make further edits.
* **Deprecate**: Workflow and component revisions in Released Mode cannot be deleted, but they can be deprecated. This means they still exist and workflow revisions containing operators belonging to them can still be executed. By default they are not visible in the sidebars anymore (you can make them visible through a checkbox). You cannot create new operators from them. Additionally, the user interface marks existing operators as deprecated and invites to update to another revision.
* **Delete**: Component and Workflow revisions in Draft Mode can be deleted fully.
* **Documentation**: To every workflow and component revision a markdown documentation can be written and used.


![lifecycle-versioning](./docs/diagrams/lifecycle-versioning.excalidraw.svg)