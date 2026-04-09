---
icon: lucide/footprints
---

## Getting Started with hetida designer

### Docker-compose setup

hetida designer consists of multiple containerized services and is meant to run on a [Kubernetes](https://kubernetes.io/) cluster in production. To try and run hetida designer locally on a single machine it includes a [docker-compose](https://docs.docker.com/compose/) setup.

Run

```sh
git clone https://github.com/hetida/hetida-designer.git

cd hetida-designer && git checkout release

docker-compose up -d
```

to start the provided docker compose setup ([docker-compose.yml](https://github.com/hetida/hetida-designer/blob/release/docker-compose.yml)).

Then open `http://localhost/` in your browser to access the hetida designer's web user interface:

![hetida designer home screen](./assets/hetida-designer-home.png)


### Next Steps
From here we recommend working through the tutorials starting either with [basic concepts](./user_guide/tutorials/basic_concepts.md) or jumping directly into [component / workflow development](./user_guide/tutorials/component_workflow_tutorial.md).