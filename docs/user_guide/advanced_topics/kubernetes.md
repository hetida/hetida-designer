# Kubernetes Setup

hetida designer is recommended to be deployed on Kubernetes for production setups. In particular this enables scaling of the runtime service.

Such a setup typically includes
* a postgres database for hetida designer backend
* deployments for 
    * runtime
    * backend
    * frontend
    * project-specific custom [adapters](../../adapter_system/intro.md)
    * Kafka consumption mode services
    * [Exec services restricted to certain trafos](../../execution/restricted_webservice.md) ("HD_RESTRICT_TO_TRAFO_EXEC_SERVICE" environment variable)
* respective configmaps, secrets, services and ingress
* Typically only the runtime needs [scaling](../../execution/scaling.md) at some point

Note: Currently hetida designer does not provide an official helm chart or operator. You may use the docker-compose setup described in the Readme as a starting point.
