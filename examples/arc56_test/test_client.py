# mypy: disable-error-code="no-untyped-call"
import algokit_utils
import algokit_utils.applications
import pytest
from algokit_utils.applications import FundAppAccountParams, OnUpdate
from algokit_utils.models import AlgoAmount
from algokit_utils.protocols import AlgorandClientProtocol

from examples.arc56_test.client import (
    Arc56TestClient,
    Arc56TestFactory,
    FooArgs,
    FooUint16BarUint16,
    Inputs,
    InputsAdd,
    InputsSubtract,
    Outputs,
)


@pytest.fixture
def default_deployer(algorand: AlgorandClientProtocol) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def arc56_test_factory(algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> Arc56TestFactory:
    return algorand.client.get_typed_app_factory(Arc56TestFactory, default_sender=default_deployer.address)


@pytest.fixture
def arc56_test_client(state_factory: Arc56TestFactory) -> Arc56TestClient:
    client, _ = state_factory.deploy(
        deploy_time_params={"VALUE": 1}, deletable=True, updatable=True, on_update=OnUpdate.UpdateApp
    )
    return client


def test_arc56_demo(
    algorand: AlgorandClientProtocol, arc56_test_factory: Arc56TestFactory, default_deployer: algokit_utils.Account
) -> None:
    client, result = arc56_test_factory.send.create.create_application(deploy_time_params={"someNumber": 1337})

    # call with a default sender
    outputs = client.send.foo(args=FooArgs(inputs=Inputs(add=InputsAdd(a=1, b=2), subtract=InputsSubtract(a=10, b=5))))
    assert outputs.abi_return
    assert outputs.abi_return.sum == 3
    assert outputs.abi_return.difference == 5

    # call with a different sender
    bob = algorand.account.random()
    algorand.account.ensure_funded_from_environment(bob, AlgoAmount.from_micro_algo(10_000_000))
    bob_outputs = client.send.foo(
        args=FooArgs(inputs=Inputs(add=InputsAdd(a=1, b=2), subtract=InputsSubtract(a=10, b=5))), sender=bob.address
    )
    assert bob_outputs.abi_return
    assert bob_outputs.abi_return.sum == 3
    assert bob_outputs.abi_return.difference == 5

    # Overwrite some of the transaction fields
    client.send.foo(
        args=FooArgs(inputs=Inputs(add=InputsAdd(a=1, b=2), subtract=InputsSubtract(a=10, b=5))),
        validity_window=50,
        note=b"Hello world",
    )

    # create another app
    another_client, _ = arc56_test_factory.send.create.create_application(deploy_time_params={"someNumber": 1338})

    # composer together multiple appClients
    call_result = (
        algorand.new_group()
        .add_app_call_method_call(
            client.params.foo(
                args=FooArgs(inputs=Inputs(add=InputsAdd(a=1, b=2), subtract=InputsSubtract(a=10, b=5))),
                validity_window=50,
                note=b"Hello world",
            )
        )
        .add_app_call_method_call(
            another_client.params.foo(
                args=FooArgs(inputs=Inputs(add=InputsAdd(a=1, b=2), subtract=InputsSubtract(a=10, b=5)))
            )
        )
        .send()
    )

    assert call_result.returns
    decoded = client.decode_return_value(
        "foo(((uint64,uint64),(uint64,uint64)))(uint64,uint64)", call_result.returns[0]
    )
    assert decoded
    assert decoded.sum == 3
    assert decoded.difference == 5

    with pytest.raises(Exception, match="subtract.a must be greater than subtract.b"):
        client.send.foo(args=FooArgs(inputs=Inputs(add=InputsAdd(a=1, b=100), subtract=InputsSubtract(a=1, b=2))))

    assert client.state.global_state.global_key() == 1337
    assert another_client.state.global_state.global_key() == 1338
    assert client.state.global_state.global_map.get_value("foo") == FooUint16BarUint16(foo=13, bar=37)

    client.app_client.fund_app_account(FundAppAccountParams(amount=AlgoAmount.from_micro_algo(1_000_000)))
    client.send.opt_in.opt_in_to_application(populate_app_call_resources=True)

    assert client.state.local_state(default_deployer.address).local_key() == 1337
    assert client.state.local_state(default_deployer.address).local_map.get_value(b"foo") == "bar"
    assert client.state.box.box_key() == "baz"
    assert client.state.box.box_map.get_value(
        Inputs(add=InputsAdd(a=1, b=2), subtract=InputsSubtract(a=4, b=3))
    ) == Outputs(
        sum=3,
        difference=1,
    )
