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

_APP_SPEC_JSON = r"""{"arcs": [22, 28], "bareActions": {"call": [], "create": ["NoOp"]}, "methods": [{"actions": {"call": ["NoOp"], "create": []}, "args": [{"type": "string", "name": "name"}], "name": "hello", "returns": {"type": "string"}, "events": [], "readonly": false, "recommendations": {}}, {"actions": {"call": ["NoOp"], "create": []}, "args": [], "name": "give_me_root_struct", "returns": {"type": "(((string,string)))", "struct": "RootStruct"}, "events": [], "readonly": false, "recommendations": {}}, {"actions": {"call": ["NoOp"], "create": []}, "args": [], "name": "give_me_struct_with_name_variations", "returns": {"type": "(string,string,string)", "struct": "Struct_WithNameVariations"}, "events": [], "readonly": false, "recommendations": {}}, {"actions": {"call": ["OptIn"], "create": []}, "args": [], "name": "opt_in", "returns": {"type": "void"}, "events": [], "readonly": false, "recommendations": {}}], "name": "Structs", "state": {"keys": {"box": {"my_box_struct": {"key": "bXlfYm94X3N0cnVjdA==", "keyType": "AVMString", "valueType": "Vector"}, "my_nested_box_struct": {"key": "bXlfbmVzdGVkX2JveF9zdHJ1Y3Q=", "keyType": "AVMString", "valueType": "RootStruct"}}, "global": {"my_struct": {"key": "bXlfc3RydWN0", "keyType": "AVMString", "valueType": "Vector"}, "my_nested_struct": {"key": "bXlfbmVzdGVkX3N0cnVjdA==", "keyType": "AVMString", "valueType": "RootStruct"}, "struct_with_name_variations": {"key": "c3RydWN0X3dpdGhfbmFtZV92YXJpYXRpb25z", "keyType": "AVMString", "valueType": "Struct_WithNameVariations"}}, "local": {"my_localstate_struct": {"key": "bXlfbG9jYWxzdGF0ZV9zdHJ1Y3Q=", "keyType": "AVMString", "valueType": "Vector"}, "my_nested_localstate_struct": {"key": "bXlfbmVzdGVkX2xvY2Fsc3RhdGVfc3RydWN0", "keyType": "AVMString", "valueType": "RootStruct"}}}, "maps": {"box": {"my_boxmap_struct": {"keyType": "uint64", "valueType": "Vector", "prefix": "bXlfYm94bWFwX3N0cnVjdA=="}, "my_nested_boxmap_struct": {"keyType": "uint64", "valueType": "RootStruct", "prefix": "bXlfbmVzdGVkX2JveG1hcF9zdHJ1Y3Q="}}, "global": {}, "local": {}}, "schema": {"global": {"bytes": 3, "ints": 0}, "local": {"bytes": 2, "ints": 0}}}, "structs": {"NestedStruct": [{"name": "content", "type": "Vector"}], "RootStruct": [{"name": "nested", "type": "NestedStruct"}], "Struct_WithNameVariations": [{"name": "first_VariatIon", "type": "string"}, {"name": "secondVariation", "type": "string"}, {"name": "third_variation", "type": "string"}], "Vector": [{"name": "x", "type": "string"}, {"name": "y", "type": "string"}]}, "events": [], "networks": {}, "sourceInfo": {"approval": {"pcOffsetMethod": "none", "sourceInfo": [{"pc": [221, 252, 282], "errorMessage": "OnCompletion is not NoOp"}, {"pc": [209], "errorMessage": "OnCompletion is not OptIn"}, {"pc": [311], "errorMessage": "can only call when creating"}, {"pc": [212, 224, 255, 285], "errorMessage": "can only call when not creating"}]}, "clear": {"pcOffsetMethod": "none", "sourceInfo": []}}}"""
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
class Vector:
    """Struct for Vector"""
    x: str
    y: str

@dataclasses.dataclass(frozen=True)
class NestedStruct:
    """Struct for NestedStruct"""
    content: Vector

@dataclasses.dataclass(frozen=True)
class RootStruct:
    """Struct for RootStruct"""
    nested: NestedStruct

@dataclasses.dataclass(frozen=True)
class StructWithNameVariations:
    """Struct for Struct_WithNameVariations"""
    first_VariatIon: str
    secondVariation: str
    third_variation: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class HelloArgs:
    """Dataclass for hello arguments"""
    name: str

    @property
    def abi_method_signature(self) -> str:
        return "hello(string)string"


class _StructsOptIn:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def opt_in(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.opt_in(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "opt_in()void",
        }))


class StructsParams:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    @property
    def opt_in(self) -> "_StructsOptIn":
        return _StructsOptIn(self.app_client)

    def hello(
        self,
        args: tuple[str] | HelloArgs,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
        method_args = _parse_abi_args(args)
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "hello(string)string",
            "args": method_args,
        }))

    def give_me_root_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "give_me_root_struct()(((string,string)))",
        }))

    def give_me_struct_with_name_variations(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "give_me_struct_with_name_variations()(string,string,string)",
        }))

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        
    ) -> algokit_utils.AppCallParams:
        return self.app_client.params.bare.clear_state(
            params,
            
        )


class _StructsOptInTransaction:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def opt_in(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.opt_in(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "opt_in()void",
        }))


class StructsCreateTransactionParams:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    @property
    def opt_in(self) -> "_StructsOptInTransaction":
        return _StructsOptInTransaction(self.app_client)

    def hello(
        self,
        args: tuple[str] | HelloArgs,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
        method_args = _parse_abi_args(args)
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "hello(string)string",
            "args": method_args,
        }))

    def give_me_root_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "give_me_root_struct()(((string,string)))",
        }))

    def give_me_struct_with_name_variations(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "give_me_struct_with_name_variations()(string,string,string)",
        }))

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        
    ) -> Transaction:
        return self.app_client.create_transaction.bare.clear_state(
            params,
            
        )


class _StructsOptInSend:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def opt_in(
        self,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[None]:
    
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.opt_in(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "opt_in()void",
        }), send_params=send_params)
        parsed_response = response
        return typing.cast(algokit_utils.SendAppTransactionResult[None], parsed_response)


class StructsSend:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    @property
    def opt_in(self) -> "_StructsOptInSend":
        return _StructsOptInSend(self.app_client)

    def hello(
        self,
        args: tuple[str] | HelloArgs,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[str]:
        method_args = _parse_abi_args(args)
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "hello(string)string",
            "args": method_args,
        }), send_params=send_params)
        parsed_response = response
        return typing.cast(algokit_utils.SendAppTransactionResult[str], parsed_response)

    def give_me_root_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[RootStruct]:
    
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "give_me_root_struct()(((string,string)))",
        }), send_params=send_params)
        parsed_response = dataclasses.replace(response, abi_return=_init_dataclass(RootStruct, typing.cast(dict, response.abi_return))) # type: ignore
        return typing.cast(algokit_utils.SendAppTransactionResult[RootStruct], parsed_response)

    def give_me_struct_with_name_variations(
        self,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[StructWithNameVariations]:
    
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "give_me_struct_with_name_variations()(string,string,string)",
        }), send_params=send_params)
        parsed_response = dataclasses.replace(response, abi_return=_init_dataclass(StructWithNameVariations, typing.cast(dict, response.abi_return))) # type: ignore
        return typing.cast(algokit_utils.SendAppTransactionResult[StructWithNameVariations], parsed_response)

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
    my_struct: Vector
    my_nested_struct: RootStruct
    struct_with_name_variations: StructWithNameVariations

class LocalStateValue(typing.TypedDict):
    """Shape of local_state state key values"""
    my_localstate_struct: Vector
    my_nested_localstate_struct: RootStruct

class BoxStateValue(typing.TypedDict):
    """Shape of box state key values"""
    my_box_struct: Vector
    my_nested_box_struct: RootStruct

class StructsState:
    """Methods to access state for the current Structs app"""

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
            "Vector": Vector,
            "RootStruct": RootStruct,
            "Struct_WithNameVariations": StructWithNameVariations
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
    def my_struct(self) -> Vector:
        """Get the current value of the my_struct key in global_state state"""
        value = self.app_client.state.global_state.get_value("my_struct")
        if isinstance(value, dict) and "Vector" in self._struct_classes:
            return _init_dataclass(self._struct_classes["Vector"], value)  # type: ignore
        return typing.cast(Vector, value)

    @property
    def my_nested_struct(self) -> RootStruct:
        """Get the current value of the my_nested_struct key in global_state state"""
        value = self.app_client.state.global_state.get_value("my_nested_struct")
        if isinstance(value, dict) and "RootStruct" in self._struct_classes:
            return _init_dataclass(self._struct_classes["RootStruct"], value)  # type: ignore
        return typing.cast(RootStruct, value)

    @property
    def struct_with_name_variations(self) -> StructWithNameVariations:
        """Get the current value of the struct_with_name_variations key in global_state state"""
        value = self.app_client.state.global_state.get_value("struct_with_name_variations")
        if isinstance(value, dict) and "Struct_WithNameVariations" in self._struct_classes:
            return _init_dataclass(self._struct_classes["Struct_WithNameVariations"], value)  # type: ignore
        return typing.cast(StructWithNameVariations, value)

class _LocalState:
    def __init__(self, app_client: algokit_utils.AppClient, address: str):
        self.app_client = app_client
        self.address = address
        # Pre-generated mapping of value types to their struct classes
        self._struct_classes: dict[str, typing.Type[typing.Any]] = {
            "Vector": Vector,
            "RootStruct": RootStruct
        }

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
    def my_localstate_struct(self) -> Vector:
        """Get the current value of the my_localstate_struct key in local_state state"""
        value = self.app_client.state.local_state(self.address).get_value("my_localstate_struct")
        if isinstance(value, dict) and "Vector" in self._struct_classes:
            return _init_dataclass(self._struct_classes["Vector"], value)  # type: ignore
        return typing.cast(Vector, value)

    @property
    def my_nested_localstate_struct(self) -> RootStruct:
        """Get the current value of the my_nested_localstate_struct key in local_state state"""
        value = self.app_client.state.local_state(self.address).get_value("my_nested_localstate_struct")
        if isinstance(value, dict) and "RootStruct" in self._struct_classes:
            return _init_dataclass(self._struct_classes["RootStruct"], value)  # type: ignore
        return typing.cast(RootStruct, value)

class _BoxState:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client
        
        # Pre-generated mapping of value types to their struct classes
        self._struct_classes: dict[str, typing.Type[typing.Any]] = {
            "Vector": Vector,
            "RootStruct": RootStruct
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
    def my_box_struct(self) -> Vector:
        """Get the current value of the my_box_struct key in box state"""
        value = self.app_client.state.box.get_value("my_box_struct")
        if isinstance(value, dict) and "Vector" in self._struct_classes:
            return _init_dataclass(self._struct_classes["Vector"], value)  # type: ignore
        return typing.cast(Vector, value)

    @property
    def my_nested_box_struct(self) -> RootStruct:
        """Get the current value of the my_nested_box_struct key in box state"""
        value = self.app_client.state.box.get_value("my_nested_box_struct")
        if isinstance(value, dict) and "RootStruct" in self._struct_classes:
            return _init_dataclass(self._struct_classes["RootStruct"], value)  # type: ignore
        return typing.cast(RootStruct, value)

    @property
    def my_boxmap_struct(self) -> "_MapState[int, Vector]":
        """Get values from the my_boxmap_struct map in box state"""
        return _MapState(
            self.app_client.state.box,
            "my_boxmap_struct",
            self._struct_classes.get("Vector")
        )

    @property
    def my_nested_boxmap_struct(self) -> "_MapState[int, RootStruct]":
        """Get values from the my_nested_boxmap_struct map in box state"""
        return _MapState(
            self.app_client.state.box,
            "my_nested_boxmap_struct",
            self._struct_classes.get("RootStruct")
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


class StructsClient:
    """Client for interacting with Structs smart contract"""

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
    
        self.params = StructsParams(self.app_client)
        self.create_transaction = StructsCreateTransactionParams(self.app_client)
        self.send = StructsSend(self.app_client)
        self.state = StructsState(self.app_client)

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
    ) -> "StructsClient":
        return StructsClient(
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
    ) -> "StructsClient":
        return StructsClient(
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
    ) -> "StructsClient":
        return StructsClient(
            self.app_client.clone(
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                approval_source_map=approval_source_map,
                clear_source_map=clear_source_map,
            )
        )

    def new_group(self) -> "StructsComposer":
        return StructsComposer(self)

    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["hello(string)string"],
        return_value: algokit_utils.ABIReturn | None
    ) -> str | None: ...
    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["give_me_root_struct()(((string,string)))"],
        return_value: algokit_utils.ABIReturn | None
    ) -> RootStruct | None: ...
    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["give_me_struct_with_name_variations()(string,string,string)"],
        return_value: algokit_utils.ABIReturn | None
    ) -> StructWithNameVariations | None: ...
    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["opt_in()void"],
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
    ) -> algokit_utils.ABIValue | algokit_utils.ABIStruct | None | RootStruct | StructWithNameVariations | str:
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


class _StructsOptInComposer:
    def __init__(self, composer: "StructsComposer"):
        self.composer = composer
    def opt_in(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "StructsComposer":
        self.composer._composer.add_app_call_method_call(
            self.composer.client.params.opt_in.opt_in(
                
                params=params,
                
            )
        )
        self.composer._result_mappers.append(
            lambda v: self.composer.client.decode_return_value(
                "opt_in()void", v
            )
        )
        return self.composer


class StructsComposer:
    """Composer for creating transaction groups for Structs contract calls"""

    def __init__(self, client: "StructsClient"):
        self.client = client
        self._composer = client.algorand.new_group()
        self._result_mappers: list[typing.Callable[[algokit_utils.ABIReturn | None], object] | None] = []

    @property
    def opt_in(self) -> "_StructsOptInComposer":
        return _StructsOptInComposer(self)

    def hello(
        self,
        args: tuple[str] | HelloArgs,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "StructsComposer":
        self._composer.add_app_call_method_call(
            self.client.params.hello(
                args=args,
                params=params,
            )
        )
        self._result_mappers.append(
            lambda v: self.client.decode_return_value(
                "hello(string)string", v
            )
        )
        return self

    def give_me_root_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "StructsComposer":
        self._composer.add_app_call_method_call(
            self.client.params.give_me_root_struct(
                
                params=params,
            )
        )
        self._result_mappers.append(
            lambda v: self.client.decode_return_value(
                "give_me_root_struct()(((string,string)))", v
            )
        )
        return self

    def give_me_struct_with_name_variations(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "StructsComposer":
        self._composer.add_app_call_method_call(
            self.client.params.give_me_struct_with_name_variations(
                
                params=params,
            )
        )
        self._result_mappers.append(
            lambda v: self.client.decode_return_value(
                "give_me_struct_with_name_variations()(string,string,string)", v
            )
        )
        return self

    def clear_state(
        self,
        *,
        args: list[bytes] | None = None,
        params: algokit_utils.CommonAppCallParams | None = None,
    ) -> "StructsComposer":
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
    ) -> "StructsComposer":
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
