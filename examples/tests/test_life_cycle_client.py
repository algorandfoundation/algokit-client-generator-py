import algokit_utils
import algosdk
import pytest
from algokit_utils import AlgorandClient, CommonAppCallCreateParams, OperationPerformed
from algokit_utils.models import AlgoAmount

from examples.smart_contracts.artifacts.life_cycle.life_cycle_client import (
    CreateStringStringArgs,
    CreateStringUint32VoidArgs,
    HelloStringStringArgs,
    LifeCycleFactory,
    LifeCycleMethodCallCreateParams,
)


@pytest.fixture
def default_deployer(algorand: AlgorandClient) -> algokit_utils.SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def lifecycle_factory(algorand: AlgorandClient, default_deployer: algokit_utils.SigningAccount) -> LifeCycleFactory:
    return algorand.client.get_typed_app_factory(LifeCycleFactory, default_sender=default_deployer.address)


def test_create_bare(lifecycle_factory: LifeCycleFactory) -> None:
    client, create_result = lifecycle_factory.send.create.bare(compilation_params={"updatable": True})
    assert create_result.transaction.application_call.on_complete == algosdk.transaction.OnComplete.NoOpOC

    response = client.send.hello_string_string(args=HelloStringStringArgs(name="Bare"))
    assert response.abi_return == "Hello, Bare\n"


def test_create_bare_optin(lifecycle_factory: LifeCycleFactory) -> None:
    client, create_result = lifecycle_factory.send.create.bare(
        params=CommonAppCallCreateParams(on_complete=algosdk.transaction.OnComplete.OptInOC),
        compilation_params={"updatable": True},
    )
    assert create_result.transaction.application_call.on_complete == algosdk.transaction.OnComplete.OptInOC

    response = client.send.hello_string_string(args=HelloStringStringArgs(name="Bare"))
    assert response.abi_return == "Hello, Bare\n"


def test_deploy_bare(lifecycle_factory: LifeCycleFactory) -> None:
    client, _ = lifecycle_factory.deploy()
    assert client.app_id

    response = client.send.hello_string_string(args=HelloStringStringArgs(name="Deploy Bare"))
    assert response.abi_return == "Hello, Deploy Bare\n"


def test_create_1arg(lifecycle_factory: LifeCycleFactory) -> None:
    client, create_result = lifecycle_factory.send.create.create_string_string(
        args=CreateStringStringArgs(greeting="Greetings"),
        compilation_params={"updatable": True},
    )
    assert create_result.abi_return is not None
    assert create_result.abi_return == "Greetings_1"

    response = client.send.hello_string_string(args=HelloStringStringArgs(name="1 Arg"))
    assert response.abi_return == "Greetings, 1 Arg\n"


def test_create_2arg(lifecycle_factory: LifeCycleFactory) -> None:
    client, create_result = lifecycle_factory.send.create.create_string_uint32_void(
        args=CreateStringUint32VoidArgs(greeting="Greetings", times=2),
        compilation_params={"updatable": True},
    )
    assert create_result.abi_return is None
    response = client.send.hello_string_string(args=HelloStringStringArgs(name="2 Arg"))
    assert response.abi_return == "Greetings, 2 Arg\nGreetings, 2 Arg\n"


def test_deploy_create_1arg(lifecycle_factory: LifeCycleFactory) -> None:
    client, response = lifecycle_factory.deploy(
        create_params=LifeCycleMethodCallCreateParams(
            args=CreateStringStringArgs(greeting="greeting"),
            method="create(string)string",
        )
    )

    assert client.app_id
    assert response.operation_performed == OperationPerformed.Create
    assert response.create_result
    assert response.create_result.abi_return == "greeting_1"

    call_response = client.send.hello_string_string(args=HelloStringStringArgs(name="1 Arg"))

    assert call_response.abi_return == "greeting, 1 Arg\n"


def test_deploy_create_2arg(lifecycle_factory: LifeCycleFactory) -> None:
    client, _ = lifecycle_factory.deploy(
        create_params=LifeCycleMethodCallCreateParams(
            args=CreateStringUint32VoidArgs(greeting="Deploy Greetings", times=2),
            method="create(string,uint32)void",
        )
    )

    assert client.app_id

    call_response = client.send.hello_string_string(args=HelloStringStringArgs(name="2 Arg"))

    assert call_response.abi_return
    assert call_response.abi_return == "Deploy Greetings, 2 Arg\nDeploy Greetings, 2 Arg\n"
