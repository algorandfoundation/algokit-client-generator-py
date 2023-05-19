import algokit_utils
import pytest
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from examples.conftest import get_unique_name
from examples.lifecycle.client import (
    CreateStringStringArgs,
    CreateStringUint32VoidArgs,
    DeployCreate_CreateStringStringArgs,
    DeployCreate_CreateStringUint32VoidArgs,
    LifeCycleAppClient,
)


@pytest.fixture(scope="session")
def lifecycle_client(algod_client: AlgodClient, funded_account: algokit_utils.Account) -> LifeCycleAppClient:
    return LifeCycleAppClient(algod_client=algod_client, signer=funded_account.signer, template_values={"UPDATABLE": 1})


@pytest.fixture()
def deploy_lifecycle_client(
    algod_client: AlgodClient, indexer_client: IndexerClient, funded_account: algokit_utils.Account
) -> LifeCycleAppClient:
    return LifeCycleAppClient(
        algod_client=algod_client,
        indexer_client=indexer_client,
        creator=funded_account,
        app_name=get_unique_name(),
    )


def test_create_bare(lifecycle_client: LifeCycleAppClient) -> None:
    create_response = lifecycle_client.create(args=None)
    assert create_response
    response = lifecycle_client.hello_string_string(name="Bare")

    assert response.return_value == "Hello, Bare\n"


def test_create_1arg(lifecycle_client: LifeCycleAppClient) -> None:
    create_response = lifecycle_client.create(args=CreateStringStringArgs(greeting="Greetings"))
    assert create_response.return_value == "Greetings_1"
    response = lifecycle_client.hello_string_string(name="1 Arg")

    assert response.return_value == "Greetings, 1 Arg\n"


def test_create_2arg(lifecycle_client: LifeCycleAppClient) -> None:
    create_response = lifecycle_client.create(args=CreateStringUint32VoidArgs(greeting="Greetings", times=2))
    assert create_response.return_value is None
    response = lifecycle_client.hello_string_string(name="2 Arg")

    assert response.return_value == "Greetings, 2 Arg\nGreetings, 2 Arg\n"


def test_deploy_bare(deploy_lifecycle_client: LifeCycleAppClient) -> None:
    deploy_lifecycle_client.deploy(allow_update=True, create_args=None)
    assert deploy_lifecycle_client.app_client.app_id

    response = deploy_lifecycle_client.hello_string_string(name="Deploy Bare")

    assert response.return_value == "Hello, Deploy Bare\n"


def test_deploy_create_1arg(deploy_lifecycle_client: LifeCycleAppClient) -> None:
    deploy_response = deploy_lifecycle_client.deploy(
        allow_update=True,
        create_args=DeployCreate_CreateStringStringArgs(args=CreateStringStringArgs(greeting="Deploy Greetings")),
    )
    assert deploy_lifecycle_client.app_client.app_id
    assert isinstance(deploy_response.create_response, algokit_utils.ABITransactionResponse)
    assert deploy_response.create_response.return_value == "Deploy Greetings_1"

    response = deploy_lifecycle_client.hello_string_string(name="1 Arg")

    assert response.return_value == "Deploy Greetings, 1 Arg\n"


def test_deploy_create_2arg(deploy_lifecycle_client: LifeCycleAppClient) -> None:
    deploy_lifecycle_client.deploy(
        allow_update=True,
        create_args=DeployCreate_CreateStringUint32VoidArgs(
            args=CreateStringUint32VoidArgs(greeting="Deploy Greetings", times=2),
        ),
    )
    assert deploy_lifecycle_client.app_client.app_id

    response = deploy_lifecycle_client.hello_string_string(name="2 Arg")

    assert response.return_value == "Deploy Greetings, 2 Arg\nDeploy Greetings, 2 Arg\n"
