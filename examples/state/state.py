from typing import Literal

import beaker
import pyteal as pt
from beaker.lib.storage import BoxMapping
from pyteal.ast import CallConfig, MethodConfig

UPDATABLE_TEMPLATE_NAME = "TMPL_UPDATABLE"
DELETABLE_TEMPLATE_NAME = "TMPL_DELETABLE"


class BareCallAppState:
    value = beaker.GlobalStateValue(stack_type=pt.TealType.uint64)
    bytes1 = beaker.GlobalStateValue(stack_type=pt.TealType.bytes)
    bytes2 = beaker.GlobalStateValue(stack_type=pt.TealType.bytes)
    int1 = beaker.GlobalStateValue(stack_type=pt.TealType.uint64)
    int2 = beaker.GlobalStateValue(stack_type=pt.TealType.uint64)
    local_bytes1 = beaker.LocalStateValue(stack_type=pt.TealType.bytes)
    local_bytes2 = beaker.LocalStateValue(stack_type=pt.TealType.bytes)
    local_int1 = beaker.LocalStateValue(stack_type=pt.TealType.uint64)
    local_int2 = beaker.LocalStateValue(stack_type=pt.TealType.uint64)
    box = BoxMapping(pt.abi.StaticBytes[Literal[4]], pt.abi.String)


app = beaker.Application("StateApp", state=BareCallAppState)


@app.external(read_only=True)
def call_abi(value: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    return output.set(pt.Concat(pt.Bytes("Hello, "), value.get()))


# https://github.com/algorand/pyteal-utils/blob/main/pytealutils/strings/string.py#L63
@pt.Subroutine(pt.TealType.bytes)
def itoa(i: pt.Expr) -> pt.Expr:
    """itoa converts an integer to the ascii byte string it represents"""
    return pt.If(
        i == pt.Int(0),
        pt.Bytes("0"),
        pt.Concat(
            pt.If(i / pt.Int(10) > pt.Int(0), itoa(i / pt.Int(10)), pt.Bytes("")),
            pt.Extract(pt.Bytes("0123456789"), i % pt.Int(10), pt.Int(1)),
        ),
    )


@app.external(read_only=True)
def call_abi_txn(txn: pt.abi.PaymentTransaction, value: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    return output.set(
        pt.Concat(
            pt.Bytes("Sent "),
            itoa(txn.get().amount()),
            pt.Bytes(". "),
            value.get(),
        )
    )


@app.external()
def set_global(
    int1: pt.abi.Uint64, int2: pt.abi.Uint64, bytes1: pt.abi.String, bytes2: pt.abi.StaticBytes[Literal[4]]
) -> pt.Expr:
    return pt.Seq(
        app.state.int1.set(int1.get()),
        app.state.int2.set(int2.get()),
        app.state.bytes1.set(bytes1.get()),
        app.state.bytes2.set(bytes2.get()),
    )


@app.external()
def set_local(
    int1: pt.abi.Uint64, int2: pt.abi.Uint64, bytes1: pt.abi.String, bytes2: pt.abi.StaticBytes[Literal[4]]
) -> pt.Expr:
    return pt.Seq(
        app.state.local_int1.set(int1.get()),
        app.state.local_int2.set(int2.get()),
        app.state.local_bytes1.set(bytes1.get()),
        app.state.local_bytes2.set(bytes2.get()),
    )


@app.external()
def set_box(name: pt.abi.StaticBytes[Literal[4]], value: pt.abi.String) -> pt.Expr:
    return app.state.box[name.get()].set(value.get())


@app.external()
def call_with_references(
    asset: pt.abi.Asset, account: pt.abi.Account, application: pt.abi.Application, *, output: pt.abi.Uint64
) -> pt.Expr:
    return pt.Seq(
        pt.Assert(asset.asset_id(), comment="asset not provided"),
        pt.Assert(pt.Len(account.address()), comment="account not provided"),
        pt.Assert(application.application_id(), comment="application not provided"),
        output.set(pt.Int(1)),
    )


@app.external(read_only=True)
def error() -> pt.Expr:
    return pt.Assert(pt.Int(0), comment="Deliberate error")


@app.external(read_only=True)
def default_value(
    arg_with_default: pt.abi.String = "default value",  # type: ignore[assignment]
    *,
    output: pt.abi.String,
) -> pt.Expr:
    return output.set(arg_with_default.get())


@app.external(read_only=True)
def default_value_from_abi(
    arg_with_default: pt.abi.String = default_value,  # type: ignore[assignment]
    *,
    output: pt.abi.String,
) -> pt.Expr:
    return output.set(pt.Concat(pt.Bytes("ABI, "), arg_with_default.get()))


@app.external(
    authorize=beaker.Authorize.only_creator(),
    bare=True,
    method_config=MethodConfig(no_op=CallConfig.CREATE, opt_in=CallConfig.CREATE),
)
def create() -> pt.Expr:
    return app.state.value.set(pt.Tmpl.Int("TMPL_VALUE"))


@app.create(authorize=beaker.Authorize.only_creator())
def create_abi(input: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:  # noqa: A002: ignore[A003]
    return output.set(input.get())


@app.update(authorize=beaker.Authorize.only_creator(), bare=True)
def update() -> pt.Expr:
    return pt.Assert(pt.Tmpl.Int(UPDATABLE_TEMPLATE_NAME), comment="Check app is updatable")


@app.update(authorize=beaker.Authorize.only_creator())
def update_abi(input: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:  # noqa: A002: ignore[A003]
    return pt.Seq(
        pt.Assert(pt.Tmpl.Int(UPDATABLE_TEMPLATE_NAME), comment="Check app is updatable"), output.set(input.get())
    )


@app.delete(authorize=beaker.Authorize.only_creator(), bare=True)
def delete() -> pt.Expr:
    return pt.Assert(pt.Tmpl.Int(DELETABLE_TEMPLATE_NAME), comment="Check app is deletable")


@app.delete(authorize=beaker.Authorize.only_creator())
def delete_abi(input: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:  # noqa: A002: ignore[A003]
    return pt.Seq(
        pt.Assert(pt.Tmpl.Int(DELETABLE_TEMPLATE_NAME), comment="Check app is deletable"), output.set(input.get())
    )


@app.opt_in
def opt_in() -> pt.Expr:
    return pt.Approve()


class Input(pt.abi.NamedTuple):
    name: pt.abi.Field[pt.abi.String]
    age: pt.abi.Field[pt.abi.Uint64]


class Output(pt.abi.NamedTuple):
    message: pt.abi.Field[pt.abi.String]
    result: pt.abi.Field[pt.abi.Uint64]


@app.external()
def structs(name_age: Input, *, output: Output) -> pt.Expr:
    return pt.Seq(
        (name := pt.abi.String()).set(name_age.name),
        (age := pt.abi.Uint64()).set(name_age.age),
        (message := pt.abi.String()).set(pt.Concat(pt.Bytes("Hello, "), name.get())),
        (result := pt.abi.Uint64()).set(pt.Mul(age.get(), pt.Int(2))),
        output.set(
            message,
            result,
        ),
    )
