# mypy: disable-error-code="no-untyped-call"
import algokit_utils
import algokit_utils.applications
import pytest
from algokit_utils import AlgorandClient, CommonAppCallParams
from algokit_utils.applications import OnUpdate
from algokit_utils.models import AlgoAmount

from examples.smart_contracts.artifacts.state.state_client import (
    CallAbiArgs,
    CallWithReferencesArgs,
    DefaultValueArgs,
    DefaultValueFromAbiArgs,
    DefaultValueFromGlobalStateArgs,
    DefaultValueFromLocalStateArgs,
    DefaultValueIntArgs,
    SetGlobalArgs,
    SetLocalArgs,
    StateClient,
    StateFactory,
)


@pytest.fixture
def default_deployer(algorand: AlgorandClient) -> algokit_utils.SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def state_factory(algorand: AlgorandClient, default_deployer: algokit_utils.SigningAccount) -> StateFactory:
    return algorand.client.get_typed_app_factory(StateFactory, default_sender=default_deployer.address)


@pytest.fixture
def deployed_state_app_client(state_factory: StateFactory) -> StateClient:
    client, _ = state_factory.deploy(
        compilation_params={
            "deploy_time_params": {"VALUE": 1},
            "deletable": True,
            "updatable": True,
        },
        on_update=OnUpdate.UpdateApp,
    )
    return client


def test_exposes_state_correctly(state_factory: StateFactory, default_deployer: algokit_utils.SigningAccount) -> None:
    client, _ = state_factory.deploy(
        compilation_params={"deploy_time_params": {"VALUE": 1}},
    )
    client.send.set_global(args=SetGlobalArgs(int1=1, bytes1="asdf", bytes2=b"\x01\x02\x03\x04", int2=2))
    global_state = client.state.global_state.get_all()

    assert global_state["int1"] == 1
    assert global_state["int2"] == 2
    assert global_state["bytes1"] == b"asdf"
    assert global_state["bytes2"] == b"\x01\x02\x03\x04"

    client.send.opt_in.opt_in()
    client.send.set_local(args=SetLocalArgs(int1=1, int2=2, bytes1="asdf", bytes2=b"\x01\x02\x03\x04"))
    local_state = client.state.local_state(default_deployer.address).get_all()
    assert local_state["local_int1"] == 1
    assert local_state["local_int2"] == 2
    assert local_state["local_bytes1"] == b"asdf"
    assert local_state["local_bytes2"] == b"\x01\x02\x03\x04"


def test_readonly_methods_dont_consume_algos(state_factory: StateFactory) -> None:
    client, _ = state_factory.deploy(
        compilation_params={"deploy_time_params": {"VALUE": 1}},
    )

    tx_cost = AlgoAmount.from_micro_algo(1_000)

    low_funds_account = state_factory.algorand.account.random()
    state_factory.algorand.account.ensure_funded_from_environment(low_funds_account, tx_cost)

    result = client.send.call_abi(
        args=CallAbiArgs(value="oh hi"),
        params=CommonAppCallParams(sender=low_funds_account.address),
    )
    assert result.abi_return == "Hello, oh hi"

    # If we can invoke this method twice it confirms that we are still above the min balance + single tx amount and the
    # previous call did not consume algos
    result2 = client.send.call_abi(
        args=CallAbiArgs(value="oh hi 2"),
        params=CommonAppCallParams(sender=low_funds_account.address),
    )
    assert result2.abi_return == "Hello, oh hi 2"


def test_arguments_with_defaults(state_factory: StateFactory) -> None:
    client, _ = state_factory.deploy(
        compilation_params={"deploy_time_params": {"VALUE": 1}},
    )

    client.send.set_global(args=SetGlobalArgs(int1=50, int2=2, bytes1="asdf", bytes2=bytes([1, 2, 3, 4])))
    client.send.opt_in.opt_in()
    client.send.set_local(args=SetLocalArgs(bytes1="default value", int2=0, int1=0, bytes2=bytes([1, 2, 3, 4])))

    constant_defined = client.send.default_value(args=DefaultValueArgs(arg_with_default="defined value"))
    assert constant_defined.abi_return == "defined value"

    constant_default = client.send.default_value()
    assert constant_default.abi_return == "default value"

    abi_defined = client.send.default_value_from_abi(args=DefaultValueFromAbiArgs(arg_with_default="defined value"))
    assert abi_defined.abi_return == "ABI, defined value"

    abi_default = client.send.default_value_from_abi()
    assert abi_default.abi_return == "ABI, default value"

    int_defined = client.send.default_value_int(args=DefaultValueIntArgs(arg_with_default=42))
    assert int_defined.abi_return == 42

    int_default = client.send.default_value_int()
    assert int_default.abi_return == 123

    global_defined = client.send.default_value_from_global_state(
        args=DefaultValueFromGlobalStateArgs(arg_with_default=123)
    )
    assert global_defined.abi_return == 123

    global_default = client.send.default_value_from_global_state()
    assert global_default.abi_return == 50

    local_defined = client.send.default_value_from_local_state(
        args=DefaultValueFromLocalStateArgs(arg_with_default="defined value")
    )
    assert local_defined.abi_return == "Local state, defined value"

    local_default = client.send.default_value_from_local_state()
    assert local_default.abi_return == "Local state, default value"


def test_methods_can_be_composed(state_factory: StateFactory, default_deployer: algokit_utils.SigningAccount) -> None:
    client, _ = state_factory.deploy(
        compilation_params={"deploy_time_params": {"VALUE": 1}},
    )
    client.new_group().opt_in.opt_in().set_local(
        args=SetLocalArgs(bytes1="default value", int2=0, int1=0, bytes2=b"\x01\x02\x03\x04")
    ).send()

    local_state = client.state.local_state(default_deployer.address).get_all()
    assert local_state["local_bytes1"] == b"default value"
    assert local_state["local_bytes2"] == b"\x01\x02\x03\x04"
    assert local_state["local_int1"] == 0
    assert local_state["local_int2"] == 0


def test_call_with_references(state_factory: StateFactory, default_deployer: algokit_utils.SigningAccount) -> None:
    client, _ = state_factory.deploy(
        compilation_params={"deploy_time_params": {"VALUE": 1}},
    )
    client.send.call_with_references(
        args=CallWithReferencesArgs(asset=1234, account=default_deployer.address, application=client.app_id)
    )
