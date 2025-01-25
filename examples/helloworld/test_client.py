import algokit_utils
import pytest
from algokit_utils.applications import OnUpdate
from algokit_utils.models import AlgoAmount
from algokit_utils import AlgorandClient

from examples.helloworld.client import HelloArgs, HelloWorldAppClient, HelloWorldAppFactory, HelloWorldCheckArgs


@pytest.fixture
def default_deployer(algorand: AlgorandClient) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def helloworld_factory(
    algorand: AlgorandClient, default_deployer: algokit_utils.Account
) -> HelloWorldAppFactory:
    return algorand.client.get_typed_app_factory(HelloWorldAppFactory, default_sender=default_deployer.address)


def test_calls_hello(helloworld_factory: HelloWorldAppFactory) -> None:
    client, _ = helloworld_factory.deploy(deletable=True, updatable=True, on_update=OnUpdate.UpdateApp)

    # Test with dict args
    response = client.send.hello(args=HelloArgs(name="World"))
    assert response.abi_return == "Hello, World"

    # Test with tuple args
    response_2 = client.send.hello(args=("World!",))
    assert response_2.abi_return == "Hello, World!"

    # Test void return
    response_3 = client.send.hello_world_check(args=HelloWorldCheckArgs(name="World"))
    assert response_3.abi_return is None


def test_composer_with_manual_transaction(
    helloworld_factory: HelloWorldAppFactory, algorand: AlgorandClient, default_deployer: algokit_utils.Account
) -> None:
    client, _ = helloworld_factory.deploy()

    # Create transactions to add manually
    transactions = client.create_transaction.hello_world_check(args=HelloWorldCheckArgs(name="World"))

    # Get client from creator and name
    client2 = algorand.client.get_typed_app_client_by_creator_and_name(
        HelloWorldAppClient, creator_address=default_deployer.address, app_name=client.app_name
    )

    transactions2 = client2.create_transaction.hello(args=HelloArgs(name="Bananas"), sender=default_deployer.address)

    # Test composition with manual transactions
    result = (
        client.new_group()
        .hello(args=("World",))
        .add_transaction(transactions.transactions[0], transactions.signers[0])
        .add_transaction(transactions2.transactions[0])
        .hello(args=HelloArgs(name="World!"))
        .send()
    )

    # Check returns
    assert result.returns[0].value == "Hello, World"
    assert result.returns[1].value == "Hello, World!"
    assert len(result.tx_ids) == 4


def test_simulate_hello(helloworld_factory: HelloWorldAppFactory) -> None:
    client, _ = helloworld_factory.deploy()

    response = client.new_group().hello(args=HelloArgs(name="mate")).simulate()
    
    assert response.returns[0].value == "Hello, mate"
    assert response.simulate_response
    assert response.simulate_response["txn-groups"][0]["app-budget-consumed"] < 50  


def test_can_be_cloned(helloworld_factory: HelloWorldAppFactory) -> None:
    client, _ = helloworld_factory.deploy()
    cloned_client = client.clone(app_name="overridden")

    assert client.app_name == "HelloWorldApp"
    assert cloned_client.app_name == "overridden"
