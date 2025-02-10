import algokit_utils
import pytest
from algokit_utils.models import AlgoAmount
from algokit_utils import AlgorandClient

from examples.smart_contracts.artifacts.minimal.minimal_client import MinimalFactory


@pytest.fixture
def default_deployer(algorand: AlgorandClient) -> algokit_utils.SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def minimal_factory(
    algorand: AlgorandClient, default_deployer: algokit_utils.SigningAccount
) -> MinimalFactory:
    return algorand.client.get_typed_app_factory(
        MinimalFactory, default_sender=default_deployer.address
    )


def test_delete(minimal_factory: MinimalFactory) -> None:
    client, _ = minimal_factory.deploy()
    client.create_transaction.delete.bare()
