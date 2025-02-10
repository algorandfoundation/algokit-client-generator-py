from dataclasses import is_dataclass

import algokit_utils
import pytest
from algokit_utils import AlgorandClient
from algokit_utils.models import AlgoAmount

from examples.smart_contracts.artifacts.structs.structs_client import StructsFactory


@pytest.fixture
def default_deployer(algorand: AlgorandClient) -> algokit_utils.SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def my_test_factory(algorand: AlgorandClient, default_deployer: algokit_utils.SigningAccount) -> StructsFactory:
    return algorand.client.get_typed_app_factory(StructsFactory, default_sender=default_deployer.address)


def test_root_struct_from_response_is_dataclass(my_test_factory: StructsFactory) -> None:
    client, _ = my_test_factory.deploy()

    struct = client.state.global_state.get_all()
    assert struct["my_struct"].x == client.state.global_state.my_struct.x == "1"
    assert struct["my_struct"].y == client.state.global_state.my_struct.y == "2"


def test_nested_structs_from_response_are_dataclasses(my_test_factory: StructsFactory) -> None:
    client, _ = my_test_factory.deploy()

    root_struct = client.send.give_me_root_struct().abi_return
    assert root_struct is not None
    assert root_struct.nested.content.x == "1"
    assert root_struct.nested.content.y == "2"
    assert is_dataclass(root_struct)
    assert is_dataclass(root_struct.nested)
    assert is_dataclass(root_struct.nested.content)


def test_nested_structs_from_state_are_dataclasses(
    my_test_factory: StructsFactory, default_deployer: algokit_utils.SigningAccount
) -> None:
    client, _ = my_test_factory.deploy()
    struct = client.state.global_state.get_all()
    nested_struct_from_state = client.state.global_state.my_nested_struct

    assert is_dataclass(nested_struct_from_state)
    assert is_dataclass(nested_struct_from_state.nested)
    assert is_dataclass(nested_struct_from_state.nested.content)
    assert nested_struct_from_state.nested.content.x == struct["my_nested_struct"].nested.content.x == "1"
    assert nested_struct_from_state.nested.content.y == struct["my_nested_struct"].nested.content.y == "2"

    client.algorand.account.ensure_funded_from_environment(client.app_address, AlgoAmount.from_algo(10))

    client.send.opt_in.opt_in(send_params={"populate_app_call_resources": True})
    all_local_state = client.state.local_state(default_deployer.address).get_all()
    local_state = client.state.local_state(default_deployer.address).my_localstate_struct

    assert is_dataclass(local_state)
    assert local_state.x == all_local_state["my_localstate_struct"].x == "1"
    assert local_state.y == all_local_state["my_localstate_struct"].y == "2"

    nested_local_state = client.state.local_state(default_deployer.address).my_nested_localstate_struct
    assert is_dataclass(nested_local_state)
    assert is_dataclass(nested_local_state.nested)
    assert is_dataclass(nested_local_state.nested.content)
    assert nested_local_state.nested.content.x == all_local_state["my_nested_localstate_struct"].nested.content.x == "1"
    assert nested_local_state.nested.content.y == all_local_state["my_nested_localstate_struct"].nested.content.y == "2"

    all_boxes = client.state.box.get_all()
    my_box_struct = client.state.box.my_box_struct
    my_nested_box_struct = client.state.box.my_nested_box_struct

    assert is_dataclass(my_box_struct)
    assert is_dataclass(my_nested_box_struct)
    assert is_dataclass(my_nested_box_struct.nested)
    assert is_dataclass(my_nested_box_struct.nested.content)
    assert my_box_struct.x == all_boxes["my_box_struct"].x == "1"
    assert my_box_struct.y == all_boxes["my_box_struct"].y == "2"
    assert my_nested_box_struct.nested.content.x == all_boxes["my_nested_box_struct"].nested.content.x == "1"
    assert my_nested_box_struct.nested.content.y == all_boxes["my_nested_box_struct"].nested.content.y == "2"

    box_map_struct = client.state.box.my_boxmap_struct.get_value(123)
    nested_box_map_struct = client.state.box.my_nested_boxmap_struct.get_value(123)

    assert is_dataclass(box_map_struct)
    assert is_dataclass(nested_box_map_struct)
    assert is_dataclass(nested_box_map_struct.nested)
    assert is_dataclass(nested_box_map_struct.nested.content)
    assert box_map_struct.x == "1"
    assert box_map_struct.y == "2"
    assert nested_box_map_struct.nested.content.x == "1"
    assert nested_box_map_struct.nested.content.y == "2"
