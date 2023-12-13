import pytest
from algokit_utils import OnUpdate, get_localnet_default_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from examples.helloworld.client import HelloWorldAppClient


@pytest.fixture(scope="session")
def helloworld_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> HelloWorldAppClient:
    client = HelloWorldAppClient(
        algod_client=algod_client,
        indexer_client=indexer_client,
        creator=get_localnet_default_account(algod_client),
    )
    client.deploy(allow_delete=True, allow_update=True, on_update=OnUpdate.UpdateApp)
    return client


def test_hello(helloworld_client: HelloWorldAppClient) -> None:
    response = helloworld_client.hello(name="World")

    assert response.return_value == "Hello, World"


def test_hello_check_args(helloworld_client: HelloWorldAppClient) -> None:
    response = helloworld_client.hello_world_check(name="World")

    assert response.return_value is None


def test_lifecycle(algod_client: AlgodClient) -> None:
    account = get_localnet_default_account(algod_client)
    signer = AccountTransactionSigner(account.private_key)

    helloworld_client = HelloWorldAppClient(
        algod_client=algod_client, signer=signer, template_values={"UPDATABLE": 1, "DELETABLE": 1}
    )

    assert helloworld_client.create_bare()
    assert helloworld_client.update_bare()

    response = helloworld_client.hello(name="World")

    assert response.return_value == "Hello, World"

    assert helloworld_client.delete_bare()


def test_compose(helloworld_client: HelloWorldAppClient) -> None:
    response = (helloworld_client.compose().hello(name="there").hello_world_check(name="World")).execute()

    hello_response, check_response = response.abi_results
    assert hello_response.return_value == "Hello, there"
    assert check_response.return_value is None

def test_simulate_hello(helloworld_client: HelloWorldAppClient) -> None:
    response = helloworld_client.compose().hello(name="mate").simulate()

    assert response.abi_results[0].return_value == "Hello, mate"
    assert response.simulate_response["txn-groups"][0]["app-budget-consumed"] < 50