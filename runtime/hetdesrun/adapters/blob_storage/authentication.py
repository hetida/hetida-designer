import json
import logging
import urllib
from typing import Optional
from uuid import uuid4

import boto3
import requests
from botocore.client import Config
from fastapi import FastAPI

from hetdesrun.webservice.config import get_config
from hetdesrun import VERSION

boto3.set_stream_logger("boto3.resources", logging.DEBUG)
logger = logging.getLogger(__name__)

authorize_url = "http://localhost:8080/auth/realms/minio/protocol/openid-connect/auth"
token_url = "http://localhost:8080/auth/realms/minio/protocol/openid-connect/token"

# callback url specified when the application was defined
callback_uri = "http://localhost:8000/oauth2/callback"

# keycloak id and secret
client_id = 'account'
client_secret = 'daaa3008-80f0-40f7-80d7-e15167531ff0'

sts_client = boto3.client(
    "sts",
    region_name="eu-central-1",
    use_ssl=False,
    endpoint_url="http://localhost:9000",
)

app = FastAPI(title="", description="",version=VERSION, root_path=get_config().swagger_prefix)


def make_authorization_url() -> str:
    # Generate a random string for the state parameter
    # Save it for use later to prevent xsrf attacks

    state = str(uuid4())
    params = {
        "client_id": client_id,
        "response_type": "code",
        "state": state,
        "redirect_uri": callback_uri,
        "scope": "openid",
    }

    url = authorize_url + "?" + urllib.parse.urlencode(params)
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
        "redirect_uri": callback_uri,
    }
    access_token_response = requests.post(
        token_url,
        data=data,
        verify=False,
        allow_redirects=False,
        auth=(client_id, client_secret),
        timeout=90
    )

    # we can now use the id_token as much as we want to access protected resources.
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
        endpoint_url="http://localhost:9000",
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
        config=Config(signature_version="s3v4"),
        region_name="eu-central-1",
    )

    return "success"
