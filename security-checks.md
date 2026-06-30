# Security Checks

We use trivy for security checks. Install trivy as recommended for your OS.

Hint: You may add `--severity HIGH,CRITICAL` to trivy commands below to further filter for only higher level vulnerabilities.

There is a `.trivyignore.yaml` file to handle CVE exceptions.


## During Development

### backend / runtime

To check docker-compose-dev image build, run from main directory:
```
docker-compose -f docker-compose-dev.yml build hetida-designer-backend

trivy image --ignorefile .trivyignore.yaml --ignore-unfixed hetida-designer-hetida-designer-backend:latest
```


### frontend

The final image (does not scan dependencies!):
```
docker-compose -f docker-compose-dev.yml build hetida-designer-frontend

trivy image --ignorefile .trivyignore.yaml --ignore-unfixed hetida-designer-hetida-designer-frontend:latest
```

**Note**: The final frontend docker image includes an sbom containing node dependencies so that a later trivy scan finds it and no separate scan of the source commit is necessary. A scan of the final image is enough.


## Check existing released versions

```
trivy image hetida/designer-backend:0.13.10
trivy image hetida/designer-runtime:0.13.10
trivy image hetida/designer-frontend:0.13.10 # dependencies included as `/sbom.cdx.json` in image, see above
```

Note that this will not apply the trivyignore file. To do so you must have hetida designer repo checked out and point to the trivyignore file, e.g. via `--ignorefile .trivyignore.yaml`.

## Obtain SBOMs of released versions

```
trivy image --format cyclonedx hetida/designer-backend:0.13.10
trivy image --format cyclonedx hetida/designer-runtime:0.13.10
trivy image --format cyclonedx hetida/designer-frontend:0.13.10 # will contain node deps