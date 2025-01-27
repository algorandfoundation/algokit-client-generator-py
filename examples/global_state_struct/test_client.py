import algokit_utils
import pytest
from algokit_utils.models import AlgoAmount
from algokit_utils import AlgorandClient

from examples.global_state_struct.client import HelloWorldFactory


@pytest.fixture
def default_deployer(algorand: AlgorandClient) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def my_test_factory(
    algorand: AlgorandClient, default_deployer: algokit_utils.Account
) -> HelloWorldFactory:
    return algorand.client.get_typed_app_factory(
        HelloWorldFactory, default_sender=default_deployer.address
    )


def test_global_state_struct(my_test_factory: HelloWorldFactory) -> None:
    client, _ = my_test_factory.deploy()

    struct = client.state.global_state.get_all()
    assert struct["my_struct"].x == "1"
    assert struct["my_struct"].y == "2"
