# Scheduling in hetida designer


## Introduction
hetida designer offers basic scheduling for running transformations regularly. Schedules are configured and observed in the scheduling tab of the hetida designer UI:

![scheduling tab](../assets/scheduling-tab.png)

You can add a schedule, give it a name, assign a workflow/component to it, specify the wiring for execution and a cron expression. After activating a schedule, a scheduler running as part of the backend service will pick it up after some time and trigger its execution when it is due.

Furthermore, from the UI you can execute it manually out of turn, inspect previously run scheduled executions and delete the schedule.

The dialog showing scheduled executions allows to inspect the execution input payload as well as the corresponding execution result including log messages from components.

![schedule executions](../assets/schedule_executions.png)

The result may even contain plots, just like for test executions invoked manually from the hetida designer UI. E.g. a scheduled machine learning model training workflow may output a training progress plot that you want to inspect afterwards.

Scheduled executions are deleted regularly from the database. This "retention" is configurabe (see below).

## Configuration
All environment variables are for the hetida designer backend. The runtime is not affected by scheduling configuration.

### General
* `HETIDA_DESIGNER_SCHEDULING_ACTIVE=true`. Whether scheduling is active, i.e. the scheduler runs as part of the backend service and the API exposes the scheduling related endpoints. If multiple instances of the backend service are employed in your setup, e.g. an additional [backend serving a restricted subset of transformations](./restricted_webservice.md), only one backend should have scheduling active, namely the one which the frontend communicates with. If no backend is running with active scheduling, existing schedules will not be picked up and run.
* `HETIDA_DESIGNER_SCHEDULING_SYNC_INTERVAL_SECONDS=30`. The scheduler syncs its active jobs from the database regularly. The interval is determined by this setting.

### Retention
Regularly old schedule execution entries are removed in order to keep the database small ("retention"). Configurations are:
* `HETIDA_DESIGNER_SCHEDULING_RETENTION_JOB_TRIGGER_INTERVAL_SECONDS=300`. The interval between those deletions is configured by this setting.
* `HETIDA_DESIGNER_SCHEDULING_RETENTION_TIMEDELTA=P2D`. Determines whether a schedule execution is old and therefore should be deleted: If its last state update is older than this timedelta backwards from now, it will be deleted. This must be a ISO 8601 timedelta, see https://en.wikipedia.org/wiki/ISO_8601#Durations. Example: `P14D` for 14 days.

Retention settings should be adapted to the amount and frequency of scheduled executions you expect. Note that if the schedules' wirings do include large amounts of direct_provisioning input data (manual input) or are directly outputting larger data objects or plot data, the schedule executions may occupy significant amount of database storage.

### Authentication
In [authenticated setups](../enabling_openidconnect_auth.md), the scheduler must be configured with client credentials in order to be able to make requests to the runtime service.
* `HD_SCHEDULING_INTERNAL_AUTH_MODE=CLIENT`
* `HD_SCHEDULING_INTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS` must be a valid client credential grant configuration, see [auth](../enabling_openidconnect_auth.md) documentation.

Note, that since all users are allowed to create and edit schedules, they effectively can perform actions with the rights / authority of these service credentials. This may elevate the user's privileges if the service user has more rights.

## Technical notes
* Scheduling requires the hetida designer backend to run in pure uvicorn mode (the new default) and is not supported in (deprecated) gunicorn mode.
* It requires to run the backend service as a single instance / 1 replica, i.e. not scaled. If multiple backend service instances are running, only one should have scheduling active as is described above. However multiple worker processes in a single backend instance are allowed. Note that these restrictions of course do not apply to the runtime service if it is separate from the backend, as is recommended for production setups.

## Advanced production scheduling / automation / orchestration
For advanced automation in production the integrated basic scheduling in hetida designer may not be sufficient. Ultimately, hetida designer is not a job engine / scheduler / orchestrator.

We recommend to employ proper automation solutions like [hatchet](https://github.com/hatchet-dev/hatchet), [temporal](https://github.com/temporalio/temporal) or similar and invoke executions via the designer backend REST API execution endpoints or via [Kafka](./execution_via_kafka.md).