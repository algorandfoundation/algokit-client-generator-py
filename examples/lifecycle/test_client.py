import pytest
from algokit_utils import (
    Account,
    get_localnet_default_account,
)
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from examples.lifecycle.client_generated import (
    CreateStringArgs,
    CreateVoidArgs,
    DeployCreate_CreateStringArgs,
    DeployCreate_CreateVoidArgs,
    LifeCycleAppClient,
)


@pytest.fixture(scope="session")
def lifecycle_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> LifeCycleAppClient:
    account = get_localnet_default_account(algod_client)
    signer = AccountTransactionSigner(account.private_key)

    return LifeCycleAppClient(algod_client=algod_client, signer=signer, template_values={"UPDATABLE": 1})


def test_create_bare(lifecycle_client: LifeCycleAppClient) -> None:
    create_response = lifecycle_client.create(args=None)
    assert create_response
    response = lifecycle_client.hello_1_args(name="Bare")

    assert response.return_value == "Hello, Bare\n"


def test_create_1arg(lifecycle_client: LifeCycleAppClient) -> None:
    create_response = lifecycle_client.create(args=CreateStringArgs(greeting="Greetings"))
    assert create_response.return_value == "Greetings_1"
    response = lifecycle_client.hello_1_args(name="1 Arg")

    assert response.return_value == "Greetings, 1 Arg\n"


def test_create_2arg(lifecycle_client: LifeCycleAppClient) -> None:
    create_response = lifecycle_client.create(args=CreateVoidArgs(greeting="Greetings", times=2))
    assert create_response.return_value is None
    response = lifecycle_client.hello_1_args(name="2 Arg")

    assert response.return_value == "Greetings, 2 Arg\nGreetings, 2 Arg\n"


@pytest.fixture()
def deploy_lifecycle_client(
    algod_client: AlgodClient, indexer_client: IndexerClient, new_account: Account
) -> LifeCycleAppClient:
    return LifeCycleAppClient(
        algod_client=algod_client,
        indexer_client=indexer_client,
        creator=new_account,
    )


def test_deploy_bare(deploy_lifecycle_client: LifeCycleAppClient) -> None:
    deploy_lifecycle_client.deploy(allow_update=True, create_args=None)
    assert deploy_lifecycle_client.app_client.app_id

    response = deploy_lifecycle_client.hello_1_args(name="Deploy Bare")

    assert response.return_value == "Hello, Deploy Bare\n"


def test_deploy_create_1arg(deploy_lifecycle_client: LifeCycleAppClient) -> None:
    deploy_lifecycle_client.deploy(
        allow_update=True,
        create_args=DeployCreate_CreateStringArgs(args=CreateStringArgs(greeting="Deploy Greetings")),
    )
    assert deploy_lifecycle_client.app_client.app_id

    response = deploy_lifecycle_client.hello_1_args(name="1 Arg")

    assert response.return_value == "Deploy Greetings, 1 Arg\n"


def test_deploy_create_2arg(deploy_lifecycle_client: LifeCycleAppClient) -> None:
    deploy_lifecycle_client.deploy(
        allow_update=True,
        create_args=DeployCreate_CreateVoidArgs(
            args=CreateVoidArgs(greeting="Deploy Greetings", times=2),
        ),
    )
    assert deploy_lifecycle_client.app_client.app_id

    response = deploy_lifecycle_client.hello_1_args(name="2 Arg")

    assert response.return_value == "Deploy Greetings, 2 Arg\nDeploy Greetings, 2 Arg\n"
