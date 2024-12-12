"""
This module is used to authenticate the user for GoCaaS and get the token
"""
import os
from typing import Any

from common.utils import configure_logging

logger = configure_logging("AUTHENTICATOR")

AWS_ENV = os.getenv("aws_env", "local")


def get_jwt_token(
        env=AWS_ENV,
        refresh_min_interval=45,
        primary_region="us-west-2",
        secondary_region="us-west-2"
) -> Any:
    """
    Get the token from the AwsIamAuthTokenClient
    """
    from gd_auth.client import AwsIamAuthTokenClient

    if env == "prod":
        sso_host = "sso.godaddy.com"
    elif env == "test" or env == "ote":
        sso_host = "sso.test-godaddy.com"
    else:
        sso_host = "sso.dev-godaddy.com"

    return AwsIamAuthTokenClient(
        sso_host,
        refresh_min=refresh_min_interval,
        primary_region=primary_region,
        secondary_region=secondary_region,
    )
