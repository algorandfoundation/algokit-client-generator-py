# mypy: disable-error-code="no-untyped-call"
import algokit_utils
import algokit_utils.applications
import pytest
from algokit_utils.applications import OnUpdate
from algokit_utils.models import AlgoAmount
from algokit_utils.protocols import AlgorandClientProtocol
from algokit_utils.transactions import PaymentParams
from algosdk.atomic_transaction_composer import TransactionWithSigner

from examples.state.client import (
    Input,
    StateAppClient,
    StateAppFactory,
    StateAppMethodCallCreateParams,
    StateAppMethodCallDeleteParams,
    StateAppMethodCallUpdateParams,
)


@pytest.fixture
def default_deployer(algorand: AlgorandClientProtocol) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def state_factory(algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> StateAppFactory:
    return algorand.client.get_typed_app_factory(StateAppFactory, default_sender=default_deployer.address)


@pytest.fixture
def deployed_state_app_client(state_factory: StateAppFactory) -> StateAppClient:
    client, _ = state_factory.deploy(
        deploy_time_params={"VALUE": 1}, deletable=True, updatable=True, on_update=OnUpdate.UpdateApp
    )
    return client


def test_call_abi(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.send.call_abi(args={"value": "there"})

    assert response.abi_return == "Hello, there"


def test_call_abi_txn(deployed_state_app_client: StateAppClient) -> None:
    from_account = deployed_state_app_client.algorand.account.localnet_dispenser()
    payment = deployed_state_app_client.algorand.create_transaction.payment(
        PaymentParams(
            sender=from_account.address,
            receiver=deployed_state_app_client.app_address,
            amount=AlgoAmount.from_micro_algo(200_000),
            note=b"Bootstrap payment",
        )
    )
    pay = TransactionWithSigner(payment, from_account.signer)
    response = deployed_state_app_client.send.call_abi_txn(args={"txn": pay, "value": "there"})
    assert response.abi_return == "Sent 200000. there"


def test_set_global(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.send.set_global(
        args={"int1": 1, "int2": 2, "bytes1": "test", "bytes2": bytes("test", encoding="utf8")}
    )

    assert response.abi_return is None
    assert deployed_state_app_client.state.global_state.int1() == 1
    assert deployed_state_app_client.state.global_state.int2() == 2
    assert deployed_state_app_client.state.global_state.bytes1() == b"test"
    assert deployed_state_app_client.state.global_state.bytes2() == b"test"


def test_set_local(deployed_state_app_client: StateAppClient, default_deployer: algokit_utils.Account) -> None:
    deployed_state_app_client.send.opt_in.opt_in()
    response = deployed_state_app_client.send.set_local(
        args={"int1": 1, "int2": 2, "bytes1": "test", "bytes2": b"test"}
    )

    assert response.abi_return is None
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_bytes1() == b"test"
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_int1() == 1
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_bytes2() == b"test"
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_int2() == 2


def test_set_box(deployed_state_app_client: StateAppClient) -> None:
    deployed_state_app_client.algorand.account.ensure_funded_from_environment(
        account_to_fund=deployed_state_app_client.app_address,
        min_spending_balance=AlgoAmount.from_micro_algo(120_000),
    )
    response = deployed_state_app_client.send.set_box(
        args={"name": b"test", "value": "test"},
        box_references=[b"test"],
    )

    assert response.abi_return is None

def test_error(deployed_state_app_client: StateAppClient) -> None:
    with pytest.raises(algokit_utils.LogicError):
        deployed_state_app_client.send.error()


def test_create_abi(state_factory: StateAppFactory) -> None:
    _, response = state_factory.send.create.create_abi(
        deploy_time_params={"VALUE": 1, "UPDATABLE": 1, "DELETABLE": 1},
        args={"input": "test"},
    )
    assert response.abi_return == "test"


def test_update_abi(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.send.update.update_abi(
        args={"input": "test"},
        updatable=True,
        deletable=True,
        deploy_time_params={"VALUE": 1},
    )

    assert response.abi_return == "test"


def test_delete_abi(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.send.delete.delete_abi(args={"input": "test"})

    assert response.abi_return == "test"


def test_opt_in(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.send.opt_in.opt_in()

    assert isinstance(response.confirmation, dict)
    assert response.confirmation.get('confirmed-round', 0) > 0


def test_default_arg(deployed_state_app_client: StateAppClient) -> None:
    assert deployed_state_app_client.send.default_value(args={'arg_with_default': "test"}).abi_return == "test"
    assert deployed_state_app_client.send.default_value(args=(None,)).abi_return == "default value"
    assert deployed_state_app_client.send.default_value().abi_return == "default value"


def test_default_arg_abi(deployed_state_app_client: StateAppClient) -> None:
    assert deployed_state_app_client.send.default_value_from_abi(args={"arg_with_default": "test"}).abi_return == "ABI, test"
    assert deployed_state_app_client.send.default_value_from_abi().abi_return == "ABI, default value"


def test_clear_state(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.send.opt_in.opt_in()
    assert isinstance(response.confirmation, dict)
    assert response.confirmation.get('confirmed-round', 0) > 0

    clear_response = deployed_state_app_client.send.clear_state()
    assert isinstance(clear_response.confirmation, dict)
    assert clear_response.confirmation.get('confirmed-round', 0) > 0


def test_get_global_state(deployed_state_app_client: StateAppClient) -> None:
    int1_expected = 1
    int2_expected = 2
    deployed_state_app_client.send.set_global(args={"int1": int1_expected, "int2": int2_expected, "bytes1": "test", "bytes2": b"test"})
    response = deployed_state_app_client.state.global_state.get_all()

    assert response["bytes1"] == b"test"
    assert response["bytes2"] == b"test"
    assert response["int1"] == int1_expected
    assert response["int2"] == int2_expected
    assert response["value"] == 1


def test_get_local_state(deployed_state_app_client: StateAppClient, default_deployer: algokit_utils.Account) -> None:
    int1_expected = 1
    int2_expected = 2
    deployed_state_app_client.send.opt_in.opt_in()
    deployed_state_app_client.send.set_local(args={"int1": int1_expected, "int2": int2_expected, "bytes1": "test", "bytes2": b"test"})
    response = deployed_state_app_client.state.local_state(default_deployer.address).get_all()

    assert response["local_bytes1"] == b"test"
    assert response["local_bytes2"] == b"test"
    assert response["local_int1"] == int1_expected
    assert response["local_int2"] == int2_expected


def test_deploy_create_1arg(state_factory: StateAppFactory) -> None:
    client, response = state_factory.deploy(
        deploy_time_params={"VALUE": 1},
        updatable=True,
        deletable=True,
        on_update=OnUpdate.UpdateApp,
        create_params=StateAppMethodCallCreateParams(args={'input': 'Deploy Greetings'}, method='create_abi(string)string'),
        update_params=StateAppMethodCallUpdateParams(args={'input': 'Deploy Update'}, method='update_abi(string)string'),
        delete_params=StateAppMethodCallDeleteParams(args={'input': 'Deploy Delete'}, method='delete_abi(string)string'),
    )
    assert client.app_id > 0
    assert response.create_response.abi_return == "Deploy Greetings"
    assert not response.update_response
    assert not response.delete_response

    client, response = state_factory.deploy(
        updatable=True,
        deletable=True,
        on_update=OnUpdate.UpdateApp,
        deploy_time_params={"VALUE": 2},
        create_params=StateAppMethodCallCreateParams(args={'input': 'Deploy Greetings'}, method='create_abi(string)string'),
        update_params=StateAppMethodCallUpdateParams(args={'input': 'Deploy Update'}, method='update_abi(string)string'),
        delete_params=StateAppMethodCallDeleteParams(args={'input': 'Deploy Delete'}, method='delete_abi(string)string'),
    )
    assert client.app_id > 0
    assert response.update_response.abi_return == "Deploy Update"
    assert not response.create_response
    assert not response.delete_response

    # state_app_client.app_client.app_id = 0

    client, response = state_factory.deploy(
        updatable=True,
        deletable=True,
        on_update=OnUpdate.ReplaceApp,
        deploy_time_params={"VALUE": 3},
        create_params=StateAppMethodCallCreateParams(args={'input': 'Deploy Greetings'}, method='create_abi(string)string'),
        update_params=StateAppMethodCallUpdateParams(args={'input': 'Deploy Update'}, method='update_abi(string)string'),
        delete_params=StateAppMethodCallDeleteParams(args={'input': 'Deploy Delete'}, method='delete_abi(string)string'),
    )
    assert client.app_id > 0
    assert response.create_response.abi_return == "Deploy Greetings"
    assert response.delete_response.abi_return == "Deploy Delete"
    assert not response.update_response



def test_struct_args(deployed_state_app_client: StateAppClient) -> None:
    age = 42
    response = deployed_state_app_client.send.structs(args={"name_age": Input(name="World", age=age)})

    assert response.abi_return.message == "Hello, World"
    assert response.abi_return.result == age * 2


def test_compose(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.new_group().opt_in.opt_in().call_abi(args={"value": "there"}).set_local(args={"int1": 1, "int2": 2, "bytes1": "1234", "bytes2": (1, 2, 3, 4)}).send()

    opt_in_response, call_abi_response, set_local_response = response.abi_results
    assert opt_in_response.tx_id
    assert call_abi_response.return_value == "Hello, there"
    assert set_local_response.return_value is None


def test_call_references(deployed_state_app_client: StateAppClient) -> None:
    asset_id = 1234
    _, account = deployed_state_app_client.app_client.resolve_signer_sender()
    response = deployed_state_app_client.call_with_references(
        asset=asset_id,
        account=account,
        application=deployed_state_app_client.app_id,
    )

    assert response.return_value
