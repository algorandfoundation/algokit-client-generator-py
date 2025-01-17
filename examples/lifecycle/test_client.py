import algokit_utils
import algosdk
import pytest
from algokit_utils.models import AlgoAmount
from algokit_utils.protocols import AlgorandClientProtocol

from examples.lifecycle.client import (
    LifeCycleAppFactory,
    LifeCycleAppMethodCallCreateParams,
)


@pytest.fixture
def default_deployer(algorand: AlgorandClientProtocol) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def lifecycle_factory(algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> LifeCycleAppFactory:
    return algorand.client.get_typed_app_factory(LifeCycleAppFactory, default_sender=default_deployer.address)


def test_create_bare(lifecycle_factory: LifeCycleAppFactory) -> None:
    client, create_response = lifecycle_factory.send.create.bare(updatable=True)
    assert create_response.transaction.application_call.on_complete == algosdk.transaction.OnComplete.NoOpOC

    response = client.send.hello_string_string(args={"name": "Bare"})
    assert response.abi_return == "Hello, Bare\n"


def test_create_bare_optin(lifecycle_factory: LifeCycleAppFactory) -> None:
    client, create_response = lifecycle_factory.send.create.bare(
        updatable=True, on_complete=algosdk.transaction.OnComplete.OptInOC
    )
    assert create_response.transaction.application_call.on_complete == algosdk.transaction.OnComplete.OptInOC

    response = client.send.hello_string_string(args={"name": "Bare"})
    assert response.abi_return == "Hello, Bare\n"


def test_create_1arg(lifecycle_factory: LifeCycleAppFactory) -> None:
    client, create_response = lifecycle_factory.send.create.create_string_string(
        args={"greeting": "Greetings"}, updatable=True
    )
    assert create_response.abi_return is not None
    assert create_response.abi_return == "Greetings_1"

    response = client.send.hello_string_string(args={"name": "1 Arg"})
    assert response.abi_return == "Greetings, 1 Arg\n"


def test_create_2arg(lifecycle_factory: LifeCycleAppFactory) -> None:
    client, create_response = lifecycle_factory.send.create.create_string_uint32_void(
        args={"greeting": "Greetings", "times": 2}, updatable=True
    )
    assert create_response.abi_return is None
    response = client.send.hello_string_string(args={"name": "2 Arg"})
    assert response.abi_return == "Greetings, 2 Arg\nGreetings, 2 Arg\n"


def test_deploy_bare(lifecycle_factory: LifeCycleAppFactory) -> None:
    client, _ = lifecycle_factory.deploy()
    assert client.app_id

    response = client.send.hello_string_string(args={"name": "Deploy Bare"})
    assert response.abi_return == "Hello, Deploy Bare\n"


def test_deploy_create_1arg(lifecycle_factory: LifeCycleAppFactory) -> None:
    client, response = lifecycle_factory.deploy(
        create_params=LifeCycleAppMethodCallCreateParams(args={"greeting": "greeting"}, method="create(string)string")
    )

    assert client.app_id
    assert response.operation_performed == "create" and response.create_response
    assert response.create_response.abi_return == "greeting_1"

    response = client.send.hello_string_string(args={"name": "1 Arg"})

    assert response.abi_return == "greeting, 1 Arg\n"


def test_deploy_create_2arg(lifecycle_factory: LifeCycleAppFactory) -> None:
    client, response = lifecycle_factory.deploy(
        create_params=LifeCycleAppMethodCallCreateParams(
            args={"greeting": "Deploy Greetings", "times": 2}, method="create(string,uint32)void"
        )
    )

    assert client.app_id

    response = client.send.hello_string_string(args={"name": "2 Arg"})

    assert response.abi_return == "Deploy Greetings, 2 Arg\nDeploy Greetings, 2 Arg\n"
