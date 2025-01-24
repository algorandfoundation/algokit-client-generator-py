from typing import Literal

from algopy import (
    Account,
    Application,
    Asset,
    BoxMap,
    Bytes,
    LocalState,
    String,
    TemplateVar,
    Txn,
    UInt64,
    arc4,
    gtxn,
)

from examples.smart_contracts.base.contract import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME, ExampleARC4Contract

VALUE_TEMPLATE_NAME = "VALUE"


class Input(arc4.Struct):
    name: arc4.String
    age: arc4.UInt64


class Output(arc4.Struct):
    message: arc4.String
    result: arc4.UInt64


class State(ExampleARC4Contract):
    value: UInt64
    bytes1: Bytes
    bytes2: Bytes
    int1: UInt64
    int2: UInt64
    local_bytes1: LocalState[Bytes]
    local_bytes2: LocalState[Bytes]
    local_int1: LocalState[UInt64]
    local_int2: LocalState[UInt64]
    box: BoxMap[arc4.StaticArray[arc4.Byte, Literal[4]], arc4.String]

    def __init__(self) -> None:
        self.local_int1 = LocalState(UInt64)
        self.local_int2 = LocalState(UInt64)
        self.local_bytes1 = LocalState(Bytes)
        self.local_bytes2 = LocalState(Bytes)

        self.box = BoxMap(arc4.StaticArray[arc4.Byte, Literal[4]], arc4.String, key_prefix=b"")

    @arc4.baremethod(create="require", allow_actions=["NoOp", "OptIn"])
    def create(self) -> None:
        self.authorize_creator()
        self.value = TemplateVar[UInt64](VALUE_TEMPLATE_NAME)

    @arc4.abimethod(create="require")
    def create_abi(self, input: String) -> String:
        self.authorize_creator()
        return input

    @arc4.abimethod(allow_actions=["UpdateApplication"])
    def update_abi(self, input: String) -> String:
        self.authorize_creator()
        assert TemplateVar[bool](UPDATABLE_TEMPLATE_NAME), "Check app is updatable"
        return input

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete_abi(self, input: String) -> String:
        self.authorize_creator()
        assert TemplateVar[bool](DELETABLE_TEMPLATE_NAME), "Check app is deletable"
        return input

    @arc4.abimethod(allow_actions=["OptIn"])
    def opt_in(self) -> None:
        pass

    @arc4.abimethod(readonly=True)
    def error(self) -> None:
        assert False, "Deliberate error"

    @arc4.abimethod(readonly=True)
    def call_abi(self, value: String) -> String:
        return String("Hello, ") + value

    @arc4.abimethod(readonly=True)
    def call_abi_txn(self, txn: gtxn.PaymentTransaction, value: String) -> String:
        return String("Sent ") + self.itoa(txn.amount) + String(". ") + value

    @arc4.abimethod
    def call_with_references(self, asset: Asset, account: Account, application: Application) -> UInt64:
        assert asset, "asset not provided"
        # FIXME: The original check is for an empty address, while this __bool__ checks against ZeroAddress.
        assert account, "account not provided"
        assert application, "application not provided"
        return UInt64(1)

    @arc4.abimethod(readonly=True)
    # FIXME: Uncomment this.
    # def default_value(self, arg_with_default: String = String("default value")) -> String:
    def default_value(self, arg_with_default: String) -> String:
        arg_with_default = arg_with_default or String("default_string")
        return arg_with_default

    @arc4.abimethod(readonly=True)
    # FIXME: Uncomment this.
    # def default_value_from_abi(self, arg_with_default: String = String("default value")) -> String:
    def default_value_from_abi(self, arg_with_default: String) -> String:
        arg_with_default = arg_with_default or String("default_string")
        return String("ABI, ") + arg_with_default

    @arc4.abimethod
    def structs(self, name_age: Input) -> Output:
        return Output(arc4.String(String("Hello, ") + name_age.name.native), arc4.UInt64(name_age.age.native * 2))

    @arc4.abimethod
    def set_global(
        self, int1: UInt64, int2: UInt64, bytes1: String, bytes2: arc4.StaticArray[arc4.Byte, Literal[4]]
    ) -> None:
        self.int1 = int1
        self.int2 = int2
        self.bytes1 = bytes1.bytes
        self.bytes2 = bytes2.bytes

    @arc4.abimethod
    def set_local(
        self, int1: UInt64, int2: UInt64, bytes1: String, bytes2: arc4.StaticArray[arc4.Byte, Literal[4]]
    ) -> None:
        self.local_int1[Txn.sender] = int1
        self.local_int2[Txn.sender] = int2
        self.local_bytes1[Txn.sender] = bytes1.bytes
        self.local_bytes2[Txn.sender] = bytes2.bytes

    @arc4.abimethod
    def set_box(self, name: arc4.StaticArray[arc4.Byte, Literal[4]], value: arc4.String) -> None:
        self.box[name] = value
