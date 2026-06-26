# Kubernetes Setup

hetida designer is recommended to be deployed on [Kubernetes](https://kubernetes.io/) for production setups. In particular this enables scaling of the runtime service.

Such a setup typically includes

* a postgres database for hetida designer backend
* deployments for 
    * runtime
    * backend
    * frontend
    * project-specific custom [adapters](../integration_guide/adapter_system/adapter_system_introduction.md)
    * [Kafka consumption mode](../integration_guide/trafo_exec_guide/kafka_consumption_mode.md) services
    * [Trafo restricted exec services](../integration_guide/trafo_exec_guide/restricted_webservice.md)
* respective configmaps, secrets, services and ingress
* Typically only the runtime needs [scaling](./scaling.md) at some point

!!! info
    Currently hetida designer does not provide an official helm chart or operator. You may use the [docker-compose](../get_started.md) setup as a starting point.
