import uuid

import algokit_utils
import pytest
from algosdk.v2client.algod import AlgodClient


def get_unique_name() -> str:
    return str(uuid.uuid4()).replace("-", "")


@pytest.fixture(scope="session")
def algorand() -> algokit_utils.AlgorandClient:
    return algokit_utils.AlgorandClient.from_environment()


@pytest.fixture
def new_account(algod_client: AlgodClient) -> algokit_utils.SigningAccount:
    return algokit_utils.get_account(algod_client, get_unique_name())


@pytest.fixture(scope="session")
def funded_account(algod_client: AlgodClient) -> algokit_utils.SigningAccount:
    return algokit_utils.get_account(algod_client, get_unique_name())
