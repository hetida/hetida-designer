import logging

from hetdesrun.utils import (
    post_components_from_directory,
    post_workflows_from_directory,
)
from unittest import mock


def test_component_deployment(caplog):
    response_mock = mock.Mock()
    response_mock.status_code = 200

    with caplog.at_level(logging.DEBUG):
        with mock.patch(
            "hetdesrun.utils.requests.post", return_value=response_mock
        ) as patched_post:

            with mock.patch(
                "hetdesrun.utils.requests.put", return_value=response_mock
            ) as patched_put:
                caplog.clear()
                post_components_from_directory("./components")
                assert "Reduce data set by leaving out values" in caplog.text

    # at least tries to upload many components (we have more than 10 there)
    assert patched_post.call_count > 10
    assert patched_put.call_count > 10

    # Test logging when posting does not work
    response_mock.status_code = 400

    with caplog.at_level(logging.INFO):
        with mock.patch(
            "hetdesrun.utils.requests.post", return_value=response_mock
        ) as patched_post:

            with mock.patch(
                "hetdesrun.utils.requests.put", return_value=response_mock
            ) as patched_put:
                caplog.clear()
                post_components_from_directory("./components")
                assert "COULD NOT POST COMPONENT" in caplog.text
                assert "COULD NOT PUT COMPONENT DOCUMENTATION" in caplog.text


def test_workflow_deployment(caplog):
    response_mock = mock.Mock()
    response_mock.status_code = 200
    with mock.patch(
        "hetdesrun.utils.requests.put", return_value=response_mock
    ) as patched_put:
        post_workflows_from_directory("./workflows")

    # at least tries to upload many workflows
    assert patched_put.call_count > 3
    # Test logging when posting does not work
    response_mock.status_code = 400
    with mock.patch(
        "hetdesrun.utils.requests.put", return_value=response_mock
    ) as patched_put:
        caplog.clear()
        post_workflows_from_directory("./workflows")
        assert "COULD NOT POST WORKFLOW" in caplog.text
        assert "COULD NOT PUT WORKFLOW DOCUMENTATION" in caplog.text
