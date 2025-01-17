# mypy: disable-error-code="no-untyped-call"
import algokit_utils
import pytest
from algokit_utils.applications.app_deployer import OnUpdate
from algosdk.atomic_transaction_composer import TransactionWithSigner

from examples.state.client import (
    StateAppClient,
)
import algokit_utils
import pytest
from algokit_utils.models import AlgoAmount
from algokit_utils.protocols import AlgorandClientProtocol
from algokit_utils.transactions import PaymentParams
from algokit_utils.models import AlgoAmount

from examples.state.client import StateAppFactory


@pytest.fixture
def default_deployer(algorand: AlgorandClientProtocol) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def state_factory(algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> StateAppFactory:
    return algorand.client.get_typed_app_factory(StateAppFactory, default_sender=default_deployer.address)



@pytest.fixture
def deployed_state_app_client(
    state_factory: StateAppFactory
) -> StateAppClient:
    client, _ = state_factory.deploy(deploy_time_params={"VALUE": 1} , deletable=True, updatable=True, on_update=OnUpdate.UpdateApp)
    return client


def test_call_abi(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.send.call_abi(args={"value": "there"})

    assert response.abi_return == "Hello, there"


def test_call_abi_txn(deployed_state_app_client: StateAppClient ) -> None:
    from_account = deployed_state_app_client.algorand.account.localnet_dispenser()
    payment = deployed_state_app_client.algorand.create_transaction.payment(PaymentParams(  sender=from_account.address,
        receiver=deployed_state_app_client.app_address,
        amount=AlgoAmount.from_micro_algo(200_000),
        note=b"Bootstrap payment",
    ))
    
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
    deployed_state_app_client.send.opt_in()
    response = deployed_state_app_client.send.set_local(args={'int1': 1, "int2": 2, "bytes1": "test", "bytes2": b"test"})

    assert response.abi_return is None
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_bytes1() == b"test"
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_int1() == 1
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_bytes2() == b"test"
    assert deployed_state_app_client.state.local_state(default_deployer.address).local_int2() == 2


# def test_set_box(deployed_state_app_client: StateAppClient) -> None:
#     algokit_utils.transfer(
#         deployed_state_app_client.algod_client,
#         algokit_utils.TransferParameters(
#             from_account=algokit_utils.get_localnet_default_account(deployed_state_app_client.algod_client),
#             to_address=deployed_state_app_client.app_address,
#             micro_algos=120000,
#         ),
#     )
#     response = deployed_state_app_client.set_box(
#         name=b"test", value="test", transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, b"test")])
#     )

#     assert response.return_value is None


# def test_error(deployed_state_app_client: StateAppClient) -> None:
#     with pytest.raises(algokit_utils.LogicError):
#         deployed_state_app_client.error()


# def test_create_abi(state_app_client: StateAppClient) -> None:
#     state_app_client.app_client.template_values = {"VALUE": 1, "UPDATABLE": 1, "DELETABLE": 1}

#     response = state_app_client.create_create_abi(input="test")

#     assert response.return_value == "test"


# def test_update_abi(deployed_state_app_client: StateAppClient) -> None:
#     response = deployed_state_app_client.update_update_abi(input="test")

#     assert response.return_value == "test"


# def test_delete_abi(deployed_state_app_client: StateAppClient) -> None:
#     response = deployed_state_app_client.delete_delete_abi(input="test")

#     assert response.return_value == "test"


# def test_opt_in(deployed_state_app_client: StateAppClient) -> None:
#     response = deployed_state_app_client.opt_in_opt_in()

#     assert response.confirmed_round


# def test_default_arg(deployed_state_app_client: StateAppClient) -> None:
#     assert deployed_state_app_client.default_value(arg_with_default="test").return_value == "test"
#     assert deployed_state_app_client.default_value().return_value == "default value"


# def test_default_arg_abi(deployed_state_app_client: StateAppClient) -> None:
#     assert deployed_state_app_client.default_value_from_abi(arg_with_default="test").return_value == "ABI, test"
#     assert deployed_state_app_client.default_value_from_abi().return_value == "ABI, default value"


# def test_clear_state(deployed_state_app_client: StateAppClient) -> None:
#     response = deployed_state_app_client.opt_in_opt_in()
#     assert response.confirmed_round

#     clear_response = deployed_state_app_client.clear_state()
#     assert clear_response.confirmed_round


# def test_get_global_state(deployed_state_app_client: StateAppClient) -> None:
#     int1_expected = 1
#     int2_expected = 2
#     deployed_state_app_client.set_global(int1=int1_expected, int2=int2_expected, bytes1="test", bytes2=b"test")
#     response = deployed_state_app_client.get_global_state()

#     assert response.bytes1.as_bytes == b"test"
#     assert response.bytes2.as_str == "test"
#     assert response.int1 == int1_expected
#     assert response.int2 == int2_expected
#     assert response.value == 1


# def test_get_local_state(deployed_state_app_client: StateAppClient) -> None:
#     int1_expected = 1
#     int2_expected = 2
#     deployed_state_app_client.opt_in_opt_in()
#     deployed_state_app_client.set_local(int1=int1_expected, int2=int2_expected, bytes1="test", bytes2=b"test")
#     response = deployed_state_app_client.get_local_state(account=None)

#     assert response.local_bytes1.as_str == "test"
#     assert response.local_bytes2.as_str == "test"
#     assert response.local_int1 == int1_expected
#     assert response.local_int2 == int2_expected


# def test_deploy_create_1arg(state_app_client: StateAppClient) -> None:
#     response = state_app_client.deploy(
#         allow_update=True,
#         allow_delete=True,
#         template_values={"VALUE": 1},
#         create_args=DeployCreate(args=CreateAbiArgs(input="Deploy Greetings")),
#         update_args=Deploy(args=UpdateAbiArgs(input="Deploy Update")),
#         delete_args=Deploy(args=DeleteAbiArgs(input="Deploy Delete")),
#     )
#     assert state_app_client.app_client.app_id
#     assert isinstance(response.create_response, algokit_utils.ABITransactionResponse)
#     assert response.create_response.return_value == "Deploy Greetings"

#     state_app_client.app_client.app_id = 0

#     response = state_app_client.deploy(
#         allow_update=True,
#         allow_delete=True,
#         on_update=OnUpdate.UpdateApp,
#         template_values={"VALUE": 2},
#         create_args=DeployCreate(args=CreateAbiArgs(input="Deploy Greetings")),
#         update_args=Deploy(args=UpdateAbiArgs(input="Deploy Update")),
#         delete_args=Deploy(args=DeleteAbiArgs(input="Deploy Delete")),
#     )
#     assert state_app_client.app_client.app_id
#     assert isinstance(response.update_response, algokit_utils.ABITransactionResponse)
#     assert response.update_response.return_value == "Deploy Update"

#     state_app_client.app_client.app_id = 0

#     response = state_app_client.deploy(
#         allow_update=True,
#         allow_delete=True,
#         on_update=OnUpdate.ReplaceApp,
#         template_values={"VALUE": 3},
#         create_args=DeployCreate(args=CreateAbiArgs(input="Deploy Greetings")),
#         update_args=Deploy(args=UpdateAbiArgs(input="Deploy Update")),
#         delete_args=Deploy(args=DeleteAbiArgs(input="Deploy Delete")),
#     )
#     assert state_app_client.app_client.app_id
#     assert isinstance(response.delete_response, algokit_utils.ABITransactionResponse)
#     assert response.delete_response.return_value == "Deploy Delete"


# def test_struct_args(deployed_state_app_client: StateAppClient) -> None:
#     age = 42
#     response = deployed_state_app_client.structs(name_age=Input(name="World", age=age))

#     assert response.return_value.message == "Hello, World"
#     assert response.return_value.result == age * 2


# def test_compose(deployed_state_app_client: StateAppClient) -> None:
#     response = (
#         deployed_state_app_client.compose()
#         .opt_in_opt_in()
#         .call_abi(value="there")
#         .set_local(int1=1, int2=2, bytes1="1234", bytes2=(1, 2, 3, 4))
#     ).execute()

#     opt_in_response, call_abi_response, set_local_response = response.abi_results
#     assert opt_in_response.tx_id
#     assert call_abi_response.return_value == "Hello, there"
#     assert set_local_response.return_value is None


# def test_call_references(deployed_state_app_client: StateAppClient) -> None:
#     asset_id = 1234
#     _, account = deployed_state_app_client.app_client.resolve_signer_sender()
#     response = deployed_state_app_client.call_with_references(
#         asset=asset_id,
#         account=account,
#         application=deployed_state_app_client.app_id,
#     )

#     assert response.return_value
