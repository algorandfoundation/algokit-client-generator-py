import pytest
from algokit_utils import OnUpdate, get_localnet_default_account
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from examples.minimal.client import MinimalAppClient


@pytest.fixture(scope="session")
def minimal_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> MinimalAppClient:
    client = MinimalAppClient(
        algod_client=algod_client,
        indexer_client=indexer_client,
        creator=get_localnet_default_account(algod_client),
    )

    client.deploy(allow_delete=True, allow_update=True, on_update=OnUpdate.UpdateApp)
    return client


def test_delete(minimal_client: MinimalAppClient) -> None:
    minimal_client.delete_bare()
