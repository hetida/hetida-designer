# End to End tests
[Playwright](https://playwright.dev/) is used for end-to-end tests.

## Setup playwright for testing
This has to be done only once. In the `frontend` subdirectory run
```sh
npm install
npx playwright install
```

## Start designer dev setup
Although the tests can be run against any running Designer installation (see below), it is recommended to start a fresh designer dev docker-compose setup. This is described in the [main readme](../README.md) file. Nevertheless it is recommended to start a clean setup via
```
docker-compose -f docker-compose-dev.yml down --volumes \
    && docker-compose -f docker-compose-dev.yml build \
    && docker-compose -f docker-compose-dev.yml up --force-recreate
```
and then run a fresh deployment of the base components / workflows via
```
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida-designer_hetida-designer-runtime -c 'from hetdesrun.exportimport.importing import import_all; import_all("./transformations/");'
```

> :information_source: **Note:** Malformed components / workloads in the running development designer setup may interfere with end-to-end tests / lead to failing tests.

## Run end-to-end tests
Simply run
```
npm run run-e2e-all
```
in the frontend directory.

In the case that the designer installation against which you want to run the tests provides its frontend at a different URL than `http://localhost` you may provide the frontend URL via environment variable:
```bash
PLAYWRIGHT_TARGET_URL="http://my-domain/hd-frontend" npm run run-e2e-all
```

