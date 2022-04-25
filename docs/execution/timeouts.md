# Timeouts during workflow execution

When executing long-running workflows timeouts can occur, leading to execution errors. Timeouts can occur at different steps:
* If running the workflow via the test execution button, the frontend container nginx reverse proxy can time out. To adjust these timeouts the [nginx.conf file](../../frontend/nginx.conf) must be modified. One way to do this is mounting a modified nginx.conf to the appropriate location into the service-container.
* The runtime Gunicorn Server can time out. These timeouts can be set via `TIMEOUT` and `GRACEFUL_TIMEOUT` environment variables on the runtime service. See [gunicorn documentation](https://docs.gunicorn.org/en/stable/settings.html#timeout).