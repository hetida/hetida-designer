# About Hetida Chart

This chart of Hetida Designer is dependent on the existence of a `postgresql` instance running already in the cluster.

To run Hetida Designer in a local minikube setup,
execute in the root-dir of the designer
(other environments will follow)

```bash

minikube <-p profile> start
minikube <-p profile> addons enable ingress

helm repo add bitnami https://charts.bitnami.com/bitnami
kubectl create namespace hd
helm upgrade -i -n hd postgres bitnami/postgresql --set global.postgresql.auth.postgresPassword=postgres
helm upgrade -i -n hd test-hetida helm-chart --set components.backend.postgresql.hetidaDbPassword="12345"

```

Create defaults and  example workflows

```bash

kubectl run -n hd --restart Never htdruntime-deployment --image=hetida/designer-runtime:0.6.19  --env "HETIDA_DESIGNER_BACKEND_API_URL=http://test-hetida-hetida-designer-backend:8080/api/" -- python -c "from hetdesrun.utils import post_components_from_directory, post_workflows_from_directory; post_components_from_directory('./components'); post_workflows_from_directory('./workflows'); post_workflows_from_directory('./workflows2')"

```
