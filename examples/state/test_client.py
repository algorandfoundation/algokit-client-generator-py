# mypy: disable-error-code="no-untyped-call"
import algokit_utils
import algosdk
import pytest
from algokit_utils import Account, OnUpdate
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from examples.conftest import get_unique_name
from examples.state.client import (
    CreateAbiArgs,
    DeleteAbiArgs,
    Deploy_DeleteAbiArgs,
    Deploy_UpdateAbiArgs,
    DeployCreate_CreateAbiArgs,
    OptInArgs,
    StateAppClient,
    UpdateAbiArgs,
)


@pytest.fixture()
def state_app_client(
    algod_client: AlgodClient, indexer_client: IndexerClient, funded_account: Account
) -> StateAppClient:
    return StateAppClient(
        algod_client=algod_client,
        indexer_client=indexer_client,
        creator=funded_account,
        app_name=get_unique_name(),
        template_values={"VALUE": 1},
    )


@pytest.fixture()
def deployed_state_app_client(state_app_client: StateAppClient) -> StateAppClient:
    state_app_client.deploy(allow_delete=True, allow_update=True, on_update=OnUpdate.UpdateApp)
    return state_app_client


def test_call_abi(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.call_abi(value="there")

    assert response.return_value == "Hello, there"
    assert response.confirmed_round is None


def test_call_abi_txn(deployed_state_app_client: StateAppClient, algod_client: AlgodClient) -> None:
    from_account = algokit_utils.get_localnet_default_account(algod_client)
    payment = algosdk.transaction.PaymentTxn(
        sender=from_account.address,
        receiver=deployed_state_app_client.app_client.app_address,
        amt=200_000,
        note=b"Bootstrap payment",
        sp=algod_client.suggested_params(),
    )
    pay = TransactionWithSigner(payment, from_account.signer)
    response = deployed_state_app_client.call_abi_txn(txn=pay, value="there")

    assert response.return_value == "Sent 200000. there"
    assert response.confirmed_round is None


def test_set_global(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.set_global(
        int1=1, int2=2, bytes1="test", bytes2=bytes("test", encoding="utf8")
    )

    assert response.return_value is None


def test_set_local(deployed_state_app_client: StateAppClient) -> None:
    deployed_state_app_client.opt_in(args=OptInArgs())
    response = deployed_state_app_client.set_local(int1=1, int2=2, bytes1="test", bytes2=b"test")

    assert response.return_value is None


def test_set_box(deployed_state_app_client: StateAppClient) -> None:
    algokit_utils.transfer(
        deployed_state_app_client.app_client.algod_client,
        algokit_utils.TransferParameters(
            from_account=algokit_utils.get_localnet_default_account(deployed_state_app_client.app_client.algod_client),
            to_address=deployed_state_app_client.app_client.app_address,
            micro_algos=120000,
        ),
    )
    response = deployed_state_app_client.set_box(
        name=b"test", value="test", transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, b"test")])
    )

    assert response.return_value is None


def test_error(deployed_state_app_client: StateAppClient) -> None:
    with pytest.raises(algokit_utils.LogicError):
        deployed_state_app_client.error()


def test_create_abi(state_app_client: StateAppClient) -> None:
    state_app_client.app_client.template_values = {"VALUE": 1, "UPDATABLE": 1, "DELETABLE": 1}

    response = state_app_client.create(args=CreateAbiArgs(input="test"))

    assert response.return_value == "test"


def test_update_abi(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.update(args=UpdateAbiArgs(input="test"))

    assert response.return_value == "test"


def test_delete_abi(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.delete(args=DeleteAbiArgs(input="test"))

    assert response.return_value == "test"


def test_opt_in(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.opt_in(args=OptInArgs())

    assert response.confirmed_round


def test_clear_state(deployed_state_app_client: StateAppClient) -> None:
    response = deployed_state_app_client.opt_in(args=OptInArgs())
    assert response.confirmed_round

    clear_response = deployed_state_app_client.clear_state()
    assert clear_response.confirmed_round


def test_get_global_state(deployed_state_app_client: StateAppClient) -> None:
    int1_expected = 1
    int2_expected = 2
    deployed_state_app_client.set_global(int1=int1_expected, int2=int2_expected, bytes1="test", bytes2=b"test")
    response = deployed_state_app_client.get_global_state()

    assert response.bytes1.as_bytes == b"test"
    assert response.bytes2.as_str == "test"
    assert response.int1 == int1_expected
    assert response.int2 == int2_expected
    assert response.value == 1


def test_get_local_state(deployed_state_app_client: StateAppClient) -> None:
    int1_expected = 1
    int2_expected = 2
    deployed_state_app_client.opt_in(args=OptInArgs())
    deployed_state_app_client.set_local(int1=int1_expected, int2=int2_expected, bytes1="test", bytes2=b"test")
    response = deployed_state_app_client.get_local_state(account=None)

    assert response.local_bytes1.as_str == "test"
    assert response.local_bytes2.as_str == "test"
    assert response.local_int1 == int1_expected
    assert response.local_int2 == int2_expected


def test_deploy_create_1arg(state_app_client: StateAppClient) -> None:
    response = state_app_client.deploy(
        allow_update=True,
        allow_delete=True,
        template_values={"VALUE": 1},
        create_args=DeployCreate_CreateAbiArgs(args=CreateAbiArgs(input="Deploy Greetings")),
        update_args=Deploy_UpdateAbiArgs(args=UpdateAbiArgs(input="Deploy Update")),
        delete_args=Deploy_DeleteAbiArgs(args=DeleteAbiArgs(input="Deploy Delete")),
    )
    assert state_app_client.app_client.app_id
    assert isinstance(response.create_response, algokit_utils.ABITransactionResponse)
    assert response.create_response.return_value == "Deploy Greetings"

    state_app_client.app_client.app_id = 0

    response = state_app_client.deploy(
        allow_update=True,
        allow_delete=True,
        on_update=OnUpdate.UpdateApp,
        template_values={"VALUE": 2},
        create_args=DeployCreate_CreateAbiArgs(args=CreateAbiArgs(input="Deploy Greetings")),
        update_args=Deploy_UpdateAbiArgs(args=UpdateAbiArgs(input="Deploy Update")),
        delete_args=Deploy_DeleteAbiArgs(args=DeleteAbiArgs(input="Deploy Delete")),
    )
    assert state_app_client.app_client.app_id
    assert isinstance(response.update_response, algokit_utils.ABITransactionResponse)
    assert response.update_response.return_value == "Deploy Update"

    state_app_client.app_client.app_id = 0

    response = state_app_client.deploy(
        allow_update=True,
        allow_delete=True,
        on_update=OnUpdate.ReplaceApp,
        template_values={"VALUE": 3},
        create_args=DeployCreate_CreateAbiArgs(args=CreateAbiArgs(input="Deploy Greetings")),
        update_args=Deploy_UpdateAbiArgs(args=UpdateAbiArgs(input="Deploy Update")),
        delete_args=Deploy_DeleteAbiArgs(args=DeleteAbiArgs(input="Deploy Delete")),
    )
    assert state_app_client.app_client.app_id
    assert isinstance(response.delete_response, algokit_utils.ABITransactionResponse)
    assert response.delete_response.return_value == "Deploy Delete"
