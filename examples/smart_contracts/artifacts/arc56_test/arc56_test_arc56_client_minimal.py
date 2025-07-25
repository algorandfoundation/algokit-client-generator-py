# flake8: noqa
# fmt: off
# mypy: disable-error-code="no-any-return, no-untyped-call, misc, type-arg"
# This file was automatically generated by algokit-client-generator.
# DO NOT MODIFY IT BY HAND.
# requires: algokit-utils@^3.0.0

# common
import dataclasses
import typing
# core algosdk
import algosdk
from algosdk.transaction import OnComplete
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.source_map import SourceMap
from algosdk.transaction import Transaction
from algosdk.v2client.models import SimulateTraceConfig
# utils
import algokit_utils
from algokit_utils import AlgorandClient as _AlgoKitAlgorandClient

_APP_SPEC_JSON = r"""{"arcs": [4, 56], "bareActions": {"call": [], "create": []}, "methods": [{"actions": {"call": ["NoOp"], "create": []}, "args": [{"type": "((uint64,uint64),(uint64,uint64))", "name": "inputs", "struct": "Inputs"}], "name": "foo", "returns": {"type": "(uint64,uint64)", "struct": "Outputs"}}, {"actions": {"call": ["OptIn"], "create": []}, "args": [], "name": "optInToApplication", "returns": {"type": "void"}}, {"actions": {"call": [], "create": ["NoOp"]}, "args": [], "name": "createApplication", "returns": {"type": "void"}}], "name": "ARC56Test", "state": {"keys": {"box": {"boxKey": {"key": "Ym94S2V5", "keyType": "AVMBytes", "valueType": "string"}}, "global": {"globalKey": {"key": "Z2xvYmFsS2V5", "keyType": "AVMBytes", "valueType": "uint64"}}, "local": {"localKey": {"key": "bG9jYWxLZXk=", "keyType": "AVMBytes", "valueType": "uint64"}}}, "maps": {"box": {"boxMap": {"keyType": "Inputs", "valueType": "Outputs", "prefix": "cA=="}}, "global": {"globalMap": {"keyType": "string", "valueType": "{ foo: uint16; bar: uint16 }", "prefix": "cA=="}}, "local": {"localMap": {"keyType": "AVMBytes", "valueType": "string", "prefix": "cA=="}}}, "schema": {"global": {"bytes": 37, "ints": 1}, "local": {"bytes": 13, "ints": 1}}}, "structs": {"{ foo: uint16; bar: uint16 }": [{"name": "foo", "type": "uint16"}, {"name": "bar", "type": "uint16"}], "Outputs": [{"name": "sum", "type": "uint64"}, {"name": "difference", "type": "uint64"}], "Inputs": [{"name": "add", "type": [{"name": "a", "type": "uint64"}, {"name": "b", "type": "uint64"}]}, {"name": "subtract", "type": [{"name": "a", "type": "uint64"}, {"name": "b", "type": "uint64"}]}]}, "desc": "", "sourceInfo": {"approval": {"pcOffsetMethod": "cblocks", "sourceInfo": [{"pc": [36], "errorMessage": "The requested action is not implemented in this contract. Are you using the correct OnComplete? Did you set your app ID?", "teal": 25}, {"pc": [51], "errorMessage": "argument 0 (inputs) for foo must be a ((uint64,uint64),(uint64,uint64))", "teal": 40}, {"pc": [78], "errorMessage": "subtract.a must be greater than subtract.b", "teal": 67}, {"pc": [257], "errorMessage": "this contract does not implement the given ABI method for create NoOp", "teal": 160}, {"pc": [271], "errorMessage": "this contract does not implement the given ABI method for call NoOp", "teal": 168}, {"pc": [285], "errorMessage": "this contract does not implement the given ABI method for call OptIn", "teal": 176}]}, "clear": {"pcOffsetMethod": "none", "sourceInfo": []}}}"""
APP_SPEC = algokit_utils.Arc56Contract.from_json(_APP_SPEC_JSON)

def _parse_abi_args(args: object | None = None) -> list[object] | None:
    """Helper to parse ABI args into the format expected by underlying client"""
    if args is None:
        return None

    def convert_dataclass(value: object) -> object:
        if dataclasses.is_dataclass(value):
            return tuple(convert_dataclass(getattr(value, field.name)) for field in dataclasses.fields(value))
        elif isinstance(value, (list, tuple)):
            return type(value)(convert_dataclass(item) for item in value)
        return value

    match args:
        case tuple():
            method_args = list(args)
        case _ if dataclasses.is_dataclass(args):
            method_args = [getattr(args, field.name) for field in dataclasses.fields(args)]
        case _:
            raise ValueError("Invalid 'args' type. Expected 'tuple' or 'TypedDict' for respective typed arguments.")

    return [
        convert_dataclass(arg) if not isinstance(arg, algokit_utils.AppMethodCallTransactionArgument) else arg
        for arg in method_args
    ] if method_args else None

def _init_dataclass(cls: type, data: dict) -> object:
    """
    Recursively instantiate a dataclass of type `cls` from `data`.

    For each field on the dataclass, if the field type is also a dataclass
    and the corresponding data is a dict, instantiate that field recursively.
    """
    field_values = {}
    for field in dataclasses.fields(cls):
        field_value = data.get(field.name)
        # Check if the field expects another dataclass and the value is a dict.
        if dataclasses.is_dataclass(field.type) and isinstance(field_value, dict):
            field_values[field.name] = _init_dataclass(typing.cast(type, field.type), field_value)
        else:
            field_values[field.name] = field_value
    return cls(**field_values)

@dataclasses.dataclass(frozen=True)
class InputsAdd:
    """Struct for InputsAdd"""
    a: int
    b: int

@dataclasses.dataclass(frozen=True)
class InputsSubtract:
    """Struct for InputsSubtract"""
    a: int
    b: int

@dataclasses.dataclass(frozen=True)
class Inputs:
    """Struct for Inputs"""
    add: InputsAdd
    subtract: InputsSubtract

@dataclasses.dataclass(frozen=True)
class Outputs:
    """Struct for Outputs"""
    sum: int
    difference: int

@dataclasses.dataclass(frozen=True)
class FooUint16BarUint16:
    """Struct for { foo: uint16; bar: uint16 }"""
    foo: int
    bar: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class FooArgs:
    """Dataclass for foo arguments"""
    inputs: Inputs

    @property
    def abi_method_signature(self) -> str:
        return "foo(((uint64,uint64),(uint64,uint64)))(uint64,uint64)"


class _Arc56TestOptIn:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def opt_in_to_application(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.opt_in(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "optInToApplication()void",
        }))


class Arc56TestParams:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    @property
    def opt_in(self) -> "_Arc56TestOptIn":
        return _Arc56TestOptIn(self.app_client)

    def foo(
        self,
        args: tuple[Inputs] | FooArgs,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
        method_args = _parse_abi_args(args)
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "foo(((uint64,uint64),(uint64,uint64)))(uint64,uint64)",
            "args": method_args,
        }))

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        
    ) -> algokit_utils.AppCallParams:
        return self.app_client.params.bare.clear_state(
            params,
            
        )


class _Arc56TestOptInTransaction:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def opt_in_to_application(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.opt_in(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "optInToApplication()void",
        }))


class Arc56TestCreateTransactionParams:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    @property
    def opt_in(self) -> "_Arc56TestOptInTransaction":
        return _Arc56TestOptInTransaction(self.app_client)

    def foo(
        self,
        args: tuple[Inputs] | FooArgs,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
        method_args = _parse_abi_args(args)
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "foo(((uint64,uint64),(uint64,uint64)))(uint64,uint64)",
            "args": method_args,
        }))

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        
    ) -> Transaction:
        return self.app_client.create_transaction.bare.clear_state(
            params,
            
        )


class _Arc56TestOptInSend:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def opt_in_to_application(
        self,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[None]:
    
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.opt_in(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "optInToApplication()void",
        }), send_params=send_params)
        parsed_response = response
        return typing.cast(algokit_utils.SendAppTransactionResult[None], parsed_response)


class Arc56TestSend:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    @property
    def opt_in(self) -> "_Arc56TestOptInSend":
        return _Arc56TestOptInSend(self.app_client)

    def foo(
        self,
        args: tuple[Inputs] | FooArgs,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[Outputs]:
        method_args = _parse_abi_args(args)
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "foo(((uint64,uint64),(uint64,uint64)))(uint64,uint64)",
            "args": method_args,
        }), send_params=send_params)
        parsed_response = dataclasses.replace(response, abi_return=_init_dataclass(Outputs, typing.cast(dict, response.abi_return))) # type: ignore
        return typing.cast(algokit_utils.SendAppTransactionResult[Outputs], parsed_response)

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[algokit_utils.ABIReturn]:
        return self.app_client.send.bare.clear_state(
            params,
            send_params=send_params,
        )


class GlobalStateValue(typing.TypedDict):
    """Shape of global_state state key values"""
    globalKey: int

class LocalStateValue(typing.TypedDict):
    """Shape of local_state state key values"""
    localKey: int

class BoxStateValue(typing.TypedDict):
    """Shape of box state key values"""
    boxKey: str

class Arc56TestState:
    """Methods to access state for the current ARC56Test app"""

    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    @property
    def global_state(
        self
    ) -> "_GlobalState":
            """Methods to access global_state for the current app"""
            return _GlobalState(self.app_client)

    def local_state(
        self, address: str
    ) -> "_LocalState":
            """Methods to access local_state for the current app"""
            return _LocalState(self.app_client, address)

    @property
    def box(
        self
    ) -> "_BoxState":
            """Methods to access box for the current app"""
            return _BoxState(self.app_client)

class _GlobalState:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client
        
        # Pre-generated mapping of value types to their struct classes
        self._struct_classes: dict[str, typing.Type[typing.Any]] = {
            "{ foo: uint16; bar: uint16 }": FooUint16BarUint16
        }

    def get_all(self) -> GlobalStateValue:
        """Get all current keyed values from global_state state"""
        result = self.app_client.state.global_state.get_all()
        if not result:
            return typing.cast(GlobalStateValue, {})

        converted = {}
        for key, value in result.items():
            key_info = self.app_client.app_spec.state.keys.global_state.get(key)
            struct_class = self._struct_classes.get(key_info.value_type) if key_info else None
            converted[key] = (
                _init_dataclass(struct_class, value) if struct_class and isinstance(value, dict)
                else value
            )
        return typing.cast(GlobalStateValue, converted)

    @property
    def global_key(self) -> int:
        """Get the current value of the globalKey key in global_state state"""
        value = self.app_client.state.global_state.get_value("globalKey")
        if isinstance(value, dict) and "uint64" in self._struct_classes:
            return _init_dataclass(self._struct_classes["uint64"], value)  # type: ignore
        return typing.cast(int, value)

    @property
    def global_map(self) -> "_MapState[str, FooUint16BarUint16]":
        """Get values from the globalMap map in global_state state"""
        return _MapState(
            self.app_client.state.global_state,
            "globalMap",
            self._struct_classes.get("{ foo: uint16; bar: uint16 }")
        )

class _LocalState:
    def __init__(self, app_client: algokit_utils.AppClient, address: str):
        self.app_client = app_client
        self.address = address
        # Pre-generated mapping of value types to their struct classes
        self._struct_classes: dict[str, typing.Type[typing.Any]] = {}

    def get_all(self) -> LocalStateValue:
        """Get all current keyed values from local_state state"""
        result = self.app_client.state.local_state(self.address).get_all()
        if not result:
            return typing.cast(LocalStateValue, {})

        converted = {}
        for key, value in result.items():
            key_info = self.app_client.app_spec.state.keys.local_state.get(key)
            struct_class = self._struct_classes.get(key_info.value_type) if key_info else None
            converted[key] = (
                _init_dataclass(struct_class, value) if struct_class and isinstance(value, dict)
                else value
            )
        return typing.cast(LocalStateValue, converted)

    @property
    def local_key(self) -> int:
        """Get the current value of the localKey key in local_state state"""
        value = self.app_client.state.local_state(self.address).get_value("localKey")
        if isinstance(value, dict) and "uint64" in self._struct_classes:
            return _init_dataclass(self._struct_classes["uint64"], value)  # type: ignore
        return typing.cast(int, value)

    @property
    def local_map(self) -> "_MapState[bytes, str]":
        """Get values from the localMap map in local_state state"""
        return _MapState(
            self.app_client.state.local_state(self.address),
            "localMap",
            None
        )

class _BoxState:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client
        
        # Pre-generated mapping of value types to their struct classes
        self._struct_classes: dict[str, typing.Type[typing.Any]] = {
            "Outputs": Outputs
        }

    def get_all(self) -> BoxStateValue:
        """Get all current keyed values from box state"""
        result = self.app_client.state.box.get_all()
        if not result:
            return typing.cast(BoxStateValue, {})

        converted = {}
        for key, value in result.items():
            key_info = self.app_client.app_spec.state.keys.box.get(key)
            struct_class = self._struct_classes.get(key_info.value_type) if key_info else None
            converted[key] = (
                _init_dataclass(struct_class, value) if struct_class and isinstance(value, dict)
                else value
            )
        return typing.cast(BoxStateValue, converted)

    @property
    def box_key(self) -> str:
        """Get the current value of the boxKey key in box state"""
        value = self.app_client.state.box.get_value("boxKey")
        if isinstance(value, dict) and "string" in self._struct_classes:
            return _init_dataclass(self._struct_classes["string"], value)  # type: ignore
        return typing.cast(str, value)

    @property
    def box_map(self) -> "_MapState[Inputs, Outputs]":
        """Get values from the boxMap map in box state"""
        return _MapState(
            self.app_client.state.box,
            "boxMap",
            self._struct_classes.get("Outputs")
        )

_KeyType = typing.TypeVar("_KeyType")
_ValueType = typing.TypeVar("_ValueType")

class _AppClientStateMethodsProtocol(typing.Protocol):
    def get_map(self, map_name: str) -> dict[typing.Any, typing.Any]:
        ...
    def get_map_value(self, map_name: str, key: typing.Any) -> typing.Any | None:
        ...

class _MapState(typing.Generic[_KeyType, _ValueType]):
    """Generic class for accessing state maps with strongly typed keys and values"""

    def __init__(self, state_accessor: _AppClientStateMethodsProtocol, map_name: str,
                struct_class: typing.Type[_ValueType] | None = None):
        self._state_accessor = state_accessor
        self._map_name = map_name
        self._struct_class = struct_class

    def get_map(self) -> dict[_KeyType, _ValueType]:
        """Get all current values in the map"""
        result = self._state_accessor.get_map(self._map_name)
        if self._struct_class and result:
            return {k: _init_dataclass(self._struct_class, v) if isinstance(v, dict) else v
                    for k, v in result.items()}  # type: ignore
        return typing.cast(dict[_KeyType, _ValueType], result or {})

    def get_value(self, key: _KeyType) -> _ValueType | None:
        """Get a value from the map by key"""
        key_value = dataclasses.asdict(key) if dataclasses.is_dataclass(key) else key  # type: ignore
        value = self._state_accessor.get_map_value(self._map_name, key_value)
        if value is not None and self._struct_class and isinstance(value, dict):
            return _init_dataclass(self._struct_class, value)  # type: ignore
        return typing.cast(_ValueType | None, value)


class Arc56TestClient:
    """Client for interacting with ARC56Test smart contract"""

    @typing.overload
    def __init__(self, app_client: algokit_utils.AppClient) -> None: ...
    
    @typing.overload
    def __init__(
        self,
        *,
        algorand: _AlgoKitAlgorandClient,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> None: ...

    def __init__(
        self,
        app_client: algokit_utils.AppClient | None = None,
        *,
        algorand: _AlgoKitAlgorandClient | None = None,
        app_id: int | None = None,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> None:
        if app_client:
            self.app_client = app_client
        elif algorand and app_id:
            self.app_client = algokit_utils.AppClient(
                algokit_utils.AppClientParams(
                    algorand=algorand,
                    app_spec=APP_SPEC,
                    app_id=app_id,
                    app_name=app_name,
                    default_sender=default_sender,
                    default_signer=default_signer,
                    approval_source_map=approval_source_map,
                    clear_source_map=clear_source_map,
                )
            )
        else:
            raise ValueError("Either app_client or algorand and app_id must be provided")
    
        self.params = Arc56TestParams(self.app_client)
        self.create_transaction = Arc56TestCreateTransactionParams(self.app_client)
        self.send = Arc56TestSend(self.app_client)
        self.state = Arc56TestState(self.app_client)

    @staticmethod
    def from_creator_and_name(
        creator_address: str,
        app_name: str,
        algorand: _AlgoKitAlgorandClient,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: algokit_utils.ApplicationLookup | None = None,
    ) -> "Arc56TestClient":
        return Arc56TestClient(
            algokit_utils.AppClient.from_creator_and_name(
                creator_address=creator_address,
                app_name=app_name,
                app_spec=APP_SPEC,
                algorand=algorand,
                default_sender=default_sender,
                default_signer=default_signer,
                approval_source_map=approval_source_map,
                clear_source_map=clear_source_map,
                ignore_cache=ignore_cache,
                app_lookup_cache=app_lookup_cache,
            )
        )
    
    @staticmethod
    def from_network(
        algorand: _AlgoKitAlgorandClient,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> "Arc56TestClient":
        return Arc56TestClient(
            algokit_utils.AppClient.from_network(
                app_spec=APP_SPEC,
                algorand=algorand,
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                approval_source_map=approval_source_map,
                clear_source_map=clear_source_map,
            )
        )

    @property
    def app_id(self) -> int:
        return self.app_client.app_id
    
    @property
    def app_address(self) -> str:
        return self.app_client.app_address
    
    @property
    def app_name(self) -> str:
        return self.app_client.app_name
    
    @property
    def app_spec(self) -> algokit_utils.Arc56Contract:
        return self.app_client.app_spec
    
    @property
    def algorand(self) -> _AlgoKitAlgorandClient:
        return self.app_client.algorand

    def clone(
        self,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> "Arc56TestClient":
        return Arc56TestClient(
            self.app_client.clone(
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                approval_source_map=approval_source_map,
                clear_source_map=clear_source_map,
            )
        )

    def new_group(self) -> "Arc56TestComposer":
        return Arc56TestComposer(self)

    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["foo(((uint64,uint64),(uint64,uint64)))(uint64,uint64)"],
        return_value: algokit_utils.ABIReturn | None
    ) -> Outputs | None: ...
    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["createApplication()void"],
        return_value: algokit_utils.ABIReturn | None
    ) -> None: ...
    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["optInToApplication()void"],
        return_value: algokit_utils.ABIReturn | None
    ) -> None: ...
    @typing.overload
    def decode_return_value(
        self,
        method: str,
        return_value: algokit_utils.ABIReturn | None
    ) -> algokit_utils.ABIValue | algokit_utils.ABIStruct | None: ...

    def decode_return_value(
        self,
        method: str,
        return_value: algokit_utils.ABIReturn | None
    ) -> algokit_utils.ABIValue | algokit_utils.ABIStruct | None | Outputs:
        """Decode ABI return value for the given method."""
        if return_value is None:
            return None
    
        arc56_method = self.app_spec.get_arc56_method(method)
        decoded = return_value.get_arc56_value(arc56_method, self.app_spec.structs)
    
        # If method returns a struct, convert the dict to appropriate dataclass
        if (arc56_method and
            arc56_method.returns and
            arc56_method.returns.struct and
            isinstance(decoded, dict)):
            struct_class = globals().get(arc56_method.returns.struct)
            if struct_class:
                return struct_class(**typing.cast(dict, decoded))
        return decoded


class _Arc56TestOptInComposer:
    def __init__(self, composer: "Arc56TestComposer"):
        self.composer = composer
    def opt_in_to_application(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "Arc56TestComposer":
        self.composer._composer.add_app_call_method_call(
            self.composer.client.params.opt_in.opt_in_to_application(
                
                params=params,
                
            )
        )
        self.composer._result_mappers.append(
            lambda v: self.composer.client.decode_return_value(
                "optInToApplication()void", v
            )
        )
        return self.composer


class Arc56TestComposer:
    """Composer for creating transaction groups for Arc56Test contract calls"""

    def __init__(self, client: "Arc56TestClient"):
        self.client = client
        self._composer = client.algorand.new_group()
        self._result_mappers: list[typing.Callable[[algokit_utils.ABIReturn | None], object] | None] = []

    @property
    def opt_in(self) -> "_Arc56TestOptInComposer":
        return _Arc56TestOptInComposer(self)

    def foo(
        self,
        args: tuple[Inputs] | FooArgs,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "Arc56TestComposer":
        self._composer.add_app_call_method_call(
            self.client.params.foo(
                args=args,
                params=params,
            )
        )
        self._result_mappers.append(
            lambda v: self.client.decode_return_value(
                "foo(((uint64,uint64),(uint64,uint64)))(uint64,uint64)", v
            )
        )
        return self

    def clear_state(
        self,
        *,
        args: list[bytes] | None = None,
        params: algokit_utils.CommonAppCallParams | None = None,
    ) -> "Arc56TestComposer":
        params=params or algokit_utils.CommonAppCallParams()
        self._composer.add_app_call(
            self.client.params.clear_state(
                algokit_utils.AppClientBareCallParams(
                    **{
                        **dataclasses.asdict(params),
                        "args": args
                    }
                )
            )
        )
        return self
    
    def add_transaction(
        self, txn: Transaction, signer: TransactionSigner | None = None
    ) -> "Arc56TestComposer":
        self._composer.add_transaction(txn, signer)
        return self
    
    def composer(self) -> algokit_utils.TransactionComposer:
        return self._composer
    
    def simulate(
        self,
        allow_more_logs: bool | None = None,
        allow_empty_signatures: bool | None = None,
        allow_unnamed_resources: bool | None = None,
        extra_opcode_budget: int | None = None,
        exec_trace_config: SimulateTraceConfig | None = None,
        simulation_round: int | None = None,
        skip_signatures: bool | None = None,
    ) -> algokit_utils.SendAtomicTransactionComposerResults:
        return self._composer.simulate(
            allow_more_logs=allow_more_logs,
            allow_empty_signatures=allow_empty_signatures,
            allow_unnamed_resources=allow_unnamed_resources,
            extra_opcode_budget=extra_opcode_budget,
            exec_trace_config=exec_trace_config,
            simulation_round=simulation_round,
            skip_signatures=skip_signatures,
        )
    
    def send(
        self,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAtomicTransactionComposerResults:
        return self._composer.send(send_params)
