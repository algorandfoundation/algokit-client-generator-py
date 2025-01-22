# type: ignore

from algopy import ARC4Contract, GlobalState, String, arc4
from algopy.arc4 import abimethod


class Vector(arc4.Struct, kw_only=True, frozen=True):
    x: arc4.String
    y: arc4.String


class HelloWorld(ARC4Contract):
    def __init__(self) -> None:
        self.my_struct = GlobalState(Vector(x=arc4.String("1"), y=arc4.String("2")))

    @abimethod()
    def hello(self, name: String) -> String:
        return "Hello, " + name
