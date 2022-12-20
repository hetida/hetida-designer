import json
import logging
import urllib
from typing import Optional
from uuid import uuid4

import boto3
import requests
from botocore.client import Config
from fastapi import FastAPI

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config

boto3.set_stream_logger("boto3.resources", logging.DEBUG)
logger = logging.getLogger(__name__)

sts_client = boto3.client(
    "sts",
    region_name=get_blob_adapter_config().region_name,
    use_ssl=False,
    endpoint_url=get_blob_adapter_config().endpoint_url,
)

app = FastAPI()


def make_authorization_url() -> str:
    # Generate a random string for the state parameter
    # Save it for use later to prevent xsrf attacks

    state = str(uuid4())
    params = {
        "get_config().client_id": get_blob_adapter_config().client_id,
        "response_type": "code",
        "state": state,
        "redirect_uri": get_blob_adapter_config().redirect_uri,
        "scope": "openid",
    }

    url = get_blob_adapter_config().authorize_url + "?" + urllib.parse.urlencode(params)
    return url


@app.get("/")
def homepage() -> str:
    text = '<a href="%s">Authenticate with keycloak</a>'
    return text % make_authorization_url()


@app.post("/oauth2/callback")
def callback(error: Optional[str] = None, code: Optional[str] = None) -> str:
    if error is not None:
        logger.error("Error: %s", error)
        return "Error: " + error

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_blob_adapter_config().redirect_uri,
    }
    access_token_response = requests.post(
        get_blob_adapter_config().token_url,
        data=data,
        verify=False,
        allow_redirects=False,
        auth=(
            get_blob_adapter_config().client_id,
            get_blob_adapter_config().client_secret,
        ),
        timeout=90,
    )

    # we can now use the access_token as much as we want to access protected resources.
    tokens = json.loads(access_token_response.text)
    access_token = tokens["asccess_token"]

    response = sts_client.assume_role_with_web_identity(
        RoleArn="arn:aws:iam::123456789012:user/svc-internal-api",
        RoleSessionName="test",
        WebIdentityToken=access_token,
        DurationSeconds=3600,
    )

    s3_resource = boto3.resource(
        "s3",
        endpoint_url=get_blob_adapter_config().endpoint_url,
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
        config=Config(signature_version="s3v4"),
        region_name=get_blob_adapter_config().region_name,
    )

    return "success"
