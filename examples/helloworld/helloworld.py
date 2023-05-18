import beaker
import pyteal as pt

from examples.deployment_standard import (
    deploy_time_immutability_control,
    deploy_time_permanence_control,
)

app = beaker.Application("HelloWorldApp").apply(deploy_time_immutability_control).apply(deploy_time_permanence_control)


@app.external
def hello(name: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    """Returns Hello, {name}"""
    return output.set(pt.Concat(pt.Bytes("Hello, "), name.get()))


@app.external
def hello_world_check(name: pt.abi.String) -> pt.Expr:
    """Asserts {name} is "World" """
    return pt.Assert(name.get() == pt.Bytes("World"))
