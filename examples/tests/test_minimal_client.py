import pytest
from algokit_utils import OnUpdate, get_localnet_default_account
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from examples.smart_contracts.artifacts.minimal.minimal_client import MinimalClient


@pytest.fixture(scope="session")
def minimal_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> MinimalClient:
    client = MinimalClient(
        algod_client=algod_client,
        indexer_client=indexer_client,
        creator=get_localnet_default_account(algod_client),
    )

    client.deploy(allow_delete=True, allow_update=True, on_update=OnUpdate.UpdateApp)
    return client


def test_delete(minimal_client: MinimalClient) -> None:
    minimal_client.delete_bare()
