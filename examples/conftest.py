import uuid

import algokit_utils
import pytest
from algokit_utils.protocols import AlgorandClientProtocol
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient


def get_unique_name() -> str:
    return str(uuid.uuid4()).replace("-", "")


@pytest.fixture(scope="session")
def algorand() -> AlgorandClientProtocol:
    return algokit_utils.AlgorandClient.from_environment()


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    return algokit_utils.get_algod_client(algokit_utils.get_default_localnet_config("algod"))


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return algokit_utils.get_indexer_client(algokit_utils.get_default_localnet_config("indexer"))


@pytest.fixture
def new_account(algod_client: AlgodClient) -> algokit_utils.Account:
    return algokit_utils.get_account(algod_client, get_unique_name())


@pytest.fixture(scope="session")
def funded_account(algod_client: AlgodClient) -> algokit_utils.Account:
    return algokit_utils.get_account(algod_client, get_unique_name())
