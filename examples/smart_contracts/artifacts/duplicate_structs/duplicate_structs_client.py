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

_APP_SPEC_JSON = r"""{"arcs": [], "bareActions": {"call": [], "create": ["NoOp"]}, "methods": [{"actions": {"call": ["NoOp"], "create": []}, "args": [], "name": "method_a_that_uses_struct", "returns": {"type": "(uint64,uint64)", "struct": "SomeStruct"}, "events": []}, {"actions": {"call": ["NoOp"], "create": []}, "args": [], "name": "method_b_that_uses_same_struct", "returns": {"type": "(uint64,uint64)", "struct": "SomeStruct"}, "events": []}], "name": "DuplicateStructs", "state": {"keys": {"box": {}, "global": {}, "local": {}}, "maps": {"box": {}, "global": {}, "local": {}}, "schema": {"global": {"bytes": 0, "ints": 0}, "local": {"bytes": 0, "ints": 0}}}, "structs": {"SomeStruct": [{"name": "a", "type": "uint64"}, {"name": "b", "type": "uint64"}]}, "desc": "\n    Used for snapshot testing to ensure no duplicate struct definitions in typed clients.\n    ", "source": {"approval": "I3ByYWdtYSB2ZXJzaW9uIDEwCiNwcmFnbWEgdHlwZXRyYWNrIGZhbHNlCgovLyBhbGdvcHkuYXJjNC5BUkM0Q29udHJhY3QuYXBwcm92YWxfcHJvZ3JhbSgpIC0+IHVpbnQ2NDoKbWFpbjoKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9kdXBsaWNhdGVfc3RydWN0cy9jb250cmFjdC5weToxMgogICAgLy8gY2xhc3MgRHVwbGljYXRlU3RydWN0cyhBUkM0Q29udHJhY3QpOgogICAgdHhuIE51bUFwcEFyZ3MKICAgIGJ6IG1haW5fYmFyZV9yb3V0aW5nQDcKICAgIHB1c2hieXRlc3MgMHg5ZjcyYWMwZiAweGE4NjE4NDQ5IC8vIG1ldGhvZCAibWV0aG9kX2FfdGhhdF91c2VzX3N0cnVjdCgpKHVpbnQ2NCx1aW50NjQpIiwgbWV0aG9kICJtZXRob2RfYl90aGF0X3VzZXNfc2FtZV9zdHJ1Y3QoKSh1aW50NjQsdWludDY0KSIKICAgIHR4bmEgQXBwbGljYXRpb25BcmdzIDAKICAgIG1hdGNoIG1haW5fbWV0aG9kX2FfdGhhdF91c2VzX3N0cnVjdF9yb3V0ZUAzIG1haW5fbWV0aG9kX2JfdGhhdF91c2VzX3NhbWVfc3RydWN0X3JvdXRlQDQKCm1haW5fYWZ0ZXJfaWZfZWxzZUAxMToKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9kdXBsaWNhdGVfc3RydWN0cy9jb250cmFjdC5weToxMgogICAgLy8gY2xhc3MgRHVwbGljYXRlU3RydWN0cyhBUkM0Q29udHJhY3QpOgogICAgcHVzaGludCAwIC8vIDAKICAgIHJldHVybgoKbWFpbl9tZXRob2RfYl90aGF0X3VzZXNfc2FtZV9zdHJ1Y3Rfcm91dGVANDoKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9kdXBsaWNhdGVfc3RydWN0cy9jb250cmFjdC5weToyNAogICAgLy8gQGFyYzQuYWJpbWV0aG9kCiAgICB0eG4gT25Db21wbGV0aW9uCiAgICAhCiAgICBhc3NlcnQgLy8gT25Db21wbGV0aW9uIGlzIG5vdCBOb09wCiAgICB0eG4gQXBwbGljYXRpb25JRAogICAgYXNzZXJ0IC8vIGNhbiBvbmx5IGNhbGwgd2hlbiBub3QgY3JlYXRpbmcKICAgIHB1c2hieXRlcyAweDE1MWY3Yzc1MDAwMDAwMDAwMDAwMDAwMzAwMDAwMDAwMDAwMDAwMDQKICAgIGxvZwogICAgcHVzaGludCAxIC8vIDEKICAgIHJldHVybgoKbWFpbl9tZXRob2RfYV90aGF0X3VzZXNfc3RydWN0X3JvdXRlQDM6CiAgICAvLyBzbWFydF9jb250cmFjdHMvZHVwbGljYXRlX3N0cnVjdHMvY29udHJhY3QucHk6MTcKICAgIC8vIEBhcmM0LmFiaW1ldGhvZAogICAgdHhuIE9uQ29tcGxldGlvbgogICAgIQogICAgYXNzZXJ0IC8vIE9uQ29tcGxldGlvbiBpcyBub3QgTm9PcAogICAgdHhuIEFwcGxpY2F0aW9uSUQKICAgIGFzc2VydCAvLyBjYW4gb25seSBjYWxsIHdoZW4gbm90IGNyZWF0aW5nCiAgICBwdXNoYnl0ZXMgMHgxNTFmN2M3NTAwMDAwMDAwMDAwMDAwMDEwMDAwMDAwMDAwMDAwMDAyCiAgICBsb2cKICAgIHB1c2hpbnQgMSAvLyAxCiAgICByZXR1cm4KCm1haW5fYmFyZV9yb3V0aW5nQDc6CiAgICAvLyBzbWFydF9jb250cmFjdHMvZHVwbGljYXRlX3N0cnVjdHMvY29udHJhY3QucHk6MTIKICAgIC8vIGNsYXNzIER1cGxpY2F0ZVN0cnVjdHMoQVJDNENvbnRyYWN0KToKICAgIHR4biBPbkNvbXBsZXRpb24KICAgIGJueiBtYWluX2FmdGVyX2lmX2Vsc2VAMTEKICAgIHR4biBBcHBsaWNhdGlvbklECiAgICAhCiAgICBhc3NlcnQgLy8gY2FuIG9ubHkgY2FsbCB3aGVuIGNyZWF0aW5nCiAgICBwdXNoaW50IDEgLy8gMQogICAgcmV0dXJuCg==", "clear": "I3ByYWdtYSB2ZXJzaW9uIDEwCiNwcmFnbWEgdHlwZXRyYWNrIGZhbHNlCgovLyBhbGdvcHkuYXJjNC5BUkM0Q29udHJhY3QuY2xlYXJfc3RhdGVfcHJvZ3JhbSgpIC0+IHVpbnQ2NDoKbWFpbjoKICAgIHB1c2hpbnQgMSAvLyAxCiAgICByZXR1cm4K"}}"""
APP_SPEC = algokit_utils.Arc56Contract.from_json(_APP_SPEC_JSON)

def _parse_abi_args(args: typing.Any | None = None) -> list[typing.Any] | None:
    """Helper to parse ABI args into the format expected by underlying client"""
    if args is None:
        return None

    def convert_dataclass(value: typing.Any) -> typing.Any:
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
            field_values[field.name] = _init_dataclass(field.type, field_value)
        else:
            field_values[field.name] = field_value
    return cls(**field_values)

@dataclasses.dataclass(frozen=True)
class SomeStruct:
    """Struct for SomeStruct"""
    a: int
    b: int


class DuplicateStructsParams:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def method_a_that_uses_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "method_a_that_uses_struct()(uint64,uint64)",
        }))

    def method_b_that_uses_same_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.AppCallMethodCallParams:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.params.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "method_b_that_uses_same_struct()(uint64,uint64)",
        }))

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        
    ) -> algokit_utils.AppCallParams:
        return self.app_client.params.bare.clear_state(
            params,
            
        )


class DuplicateStructsCreateTransactionParams:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def method_a_that_uses_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "method_a_that_uses_struct()(uint64,uint64)",
        }))

    def method_b_that_uses_same_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> algokit_utils.BuiltTransactions:
    
        params = params or algokit_utils.CommonAppCallParams()
        return self.app_client.create_transaction.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "method_b_that_uses_same_struct()(uint64,uint64)",
        }))

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        
    ) -> Transaction:
        return self.app_client.create_transaction.bare.clear_state(
            params,
            
        )


class DuplicateStructsSend:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

    def method_a_that_uses_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[SomeStruct]:
    
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "method_a_that_uses_struct()(uint64,uint64)",
        }), send_params=send_params)
        parsed_response = dataclasses.replace(response, abi_return=_init_dataclass(SomeStruct, typing.cast(dict, response.abi_return))) # type: ignore
        return typing.cast(algokit_utils.SendAppTransactionResult[SomeStruct], parsed_response)

    def method_b_that_uses_same_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[SomeStruct]:
    
        params = params or algokit_utils.CommonAppCallParams()
        response = self.app_client.send.call(algokit_utils.AppClientMethodCallParams(**{
            **dataclasses.asdict(params),
            "method": "method_b_that_uses_same_struct()(uint64,uint64)",
        }), send_params=send_params)
        parsed_response = dataclasses.replace(response, abi_return=_init_dataclass(SomeStruct, typing.cast(dict, response.abi_return))) # type: ignore
        return typing.cast(algokit_utils.SendAppTransactionResult[SomeStruct], parsed_response)

    def clear_state(
        self,
        params: algokit_utils.AppClientBareCallParams | None = None,
        send_params: algokit_utils.SendParams | None = None
    ) -> algokit_utils.SendAppTransactionResult[algokit_utils.ABIReturn]:
        return self.app_client.send.bare.clear_state(
            params,
            send_params=send_params,
        )


class DuplicateStructsState:
    """Methods to access state for the current DuplicateStructs app"""

    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client

class DuplicateStructsClient:
    """Client for interacting with DuplicateStructs smart contract"""

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
    
        self.params = DuplicateStructsParams(self.app_client)
        self.create_transaction = DuplicateStructsCreateTransactionParams(self.app_client)
        self.send = DuplicateStructsSend(self.app_client)
        self.state = DuplicateStructsState(self.app_client)

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
    ) -> "DuplicateStructsClient":
        return DuplicateStructsClient(
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
    ) -> "DuplicateStructsClient":
        return DuplicateStructsClient(
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
    ) -> "DuplicateStructsClient":
        return DuplicateStructsClient(
            self.app_client.clone(
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                approval_source_map=approval_source_map,
                clear_source_map=clear_source_map,
            )
        )

    def new_group(self) -> "DuplicateStructsComposer":
        return DuplicateStructsComposer(self)

    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["method_a_that_uses_struct()(uint64,uint64)"],
        return_value: algokit_utils.ABIReturn | None
    ) -> SomeStruct | None: ...
    @typing.overload
    def decode_return_value(
        self,
        method: typing.Literal["method_b_that_uses_same_struct()(uint64,uint64)"],
        return_value: algokit_utils.ABIReturn | None
    ) -> SomeStruct | None: ...
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
    ) -> algokit_utils.ABIValue | algokit_utils.ABIStruct | None | SomeStruct:
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


@dataclasses.dataclass(frozen=True)
class DuplicateStructsBareCallCreateParams(algokit_utils.AppClientBareCallCreateParams):
    """Parameters for creating DuplicateStructs contract with bare calls"""
    on_complete: typing.Literal[OnComplete.NoOpOC] | None = None

    def to_algokit_utils_params(self) -> algokit_utils.AppClientBareCallCreateParams:
        return algokit_utils.AppClientBareCallCreateParams(**self.__dict__)

class DuplicateStructsFactory(algokit_utils.TypedAppFactoryProtocol[DuplicateStructsBareCallCreateParams, None, None]):
    """Factory for deploying and managing DuplicateStructsClient smart contracts"""

    def __init__(
        self,
        algorand: _AlgoKitAlgorandClient,
        *,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        version: str | None = None,
        compilation_params: algokit_utils.AppClientCompilationParams | None = None,
    ):
        self.app_factory = algokit_utils.AppFactory(
            params=algokit_utils.AppFactoryParams(
                algorand=algorand,
                app_spec=APP_SPEC,
                app_name=app_name,
                default_sender=default_sender,
                default_signer=default_signer,
                version=version,
                compilation_params=compilation_params,
            )
        )
        self.params = DuplicateStructsFactoryParams(self.app_factory)
        self.create_transaction = DuplicateStructsFactoryCreateTransaction(self.app_factory)
        self.send = DuplicateStructsFactorySend(self.app_factory)

    @property
    def app_name(self) -> str:
        return self.app_factory.app_name
    
    @property
    def app_spec(self) -> algokit_utils.Arc56Contract:
        return self.app_factory.app_spec
    
    @property
    def algorand(self) -> _AlgoKitAlgorandClient:
        return self.app_factory.algorand

    def deploy(
        self,
        *,
        on_update: algokit_utils.OnUpdate | None = None,
        on_schema_break: algokit_utils.OnSchemaBreak | None = None,
        create_params: DuplicateStructsBareCallCreateParams | None = None,
        update_params: None = None,
        delete_params: None = None,
        existing_deployments: algokit_utils.ApplicationLookup | None = None,
        ignore_cache: bool = False,
        app_name: str | None = None,
        compilation_params: algokit_utils.AppClientCompilationParams | None = None,
        send_params: algokit_utils.SendParams | None = None,
    ) -> tuple[DuplicateStructsClient, algokit_utils.AppFactoryDeployResult]:
        """Deploy the application"""
        deploy_response = self.app_factory.deploy(
            on_update=on_update,
            on_schema_break=on_schema_break,
            create_params=create_params.to_algokit_utils_params() if create_params else None,
            update_params=update_params,
            delete_params=delete_params,
            existing_deployments=existing_deployments,
            ignore_cache=ignore_cache,
            app_name=app_name,
            compilation_params=compilation_params,
            send_params=send_params,
        )

        return DuplicateStructsClient(deploy_response[0]), deploy_response[1]

    def get_app_client_by_creator_and_name(
        self,
        creator_address: str,
        app_name: str,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: algokit_utils.ApplicationLookup | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> DuplicateStructsClient:
        """Get an app client by creator address and name"""
        return DuplicateStructsClient(
            self.app_factory.get_app_client_by_creator_and_name(
                creator_address,
                app_name,
                default_sender,
                default_signer,
                ignore_cache,
                app_lookup_cache,
                approval_source_map,
                clear_source_map,
            )
        )

    def get_app_client_by_id(
        self,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> DuplicateStructsClient:
        """Get an app client by app ID"""
        return DuplicateStructsClient(
            self.app_factory.get_app_client_by_id(
                app_id,
                app_name,
                default_sender,
                default_signer,
                approval_source_map,
                clear_source_map,
            )
        )


class DuplicateStructsFactoryParams:
    """Parameters for creating transactions for DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory
        self.create = DuplicateStructsFactoryCreateParams(app_factory)
        self.update = DuplicateStructsFactoryUpdateParams(app_factory)
        self.delete = DuplicateStructsFactoryDeleteParams(app_factory)

class DuplicateStructsFactoryCreateParams:
    """Parameters for 'create' operations of DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        params: algokit_utils.CommonAppCallCreateParams | None = None,
        compilation_params: algokit_utils.AppClientCompilationParams | None = None
    ) -> algokit_utils.AppCreateParams:
        """Creates an instance using a bare call"""
        params = params or algokit_utils.CommonAppCallCreateParams()
        return self.app_factory.params.bare.create(
            algokit_utils.AppFactoryCreateParams(**dataclasses.asdict(params)),
            compilation_params=compilation_params)

    def method_a_that_uses_struct(
        self,
        *,
        params: algokit_utils.CommonAppCallCreateParams | None = None,
        compilation_params: algokit_utils.AppClientCompilationParams | None = None
    ) -> algokit_utils.AppCreateMethodCallParams:
        """Creates a new instance using the method_a_that_uses_struct()(uint64,uint64) ABI method"""
        params = params or algokit_utils.CommonAppCallCreateParams()
        return self.app_factory.params.create(
            algokit_utils.AppFactoryCreateMethodCallParams(
                **{
                **dataclasses.asdict(params),
                "method": "method_a_that_uses_struct()(uint64,uint64)",
                "args": None,
                }
            ),
            compilation_params=compilation_params
        )

    def method_b_that_uses_same_struct(
        self,
        *,
        params: algokit_utils.CommonAppCallCreateParams | None = None,
        compilation_params: algokit_utils.AppClientCompilationParams | None = None
    ) -> algokit_utils.AppCreateMethodCallParams:
        """Creates a new instance using the method_b_that_uses_same_struct()(uint64,uint64) ABI method"""
        params = params or algokit_utils.CommonAppCallCreateParams()
        return self.app_factory.params.create(
            algokit_utils.AppFactoryCreateMethodCallParams(
                **{
                **dataclasses.asdict(params),
                "method": "method_b_that_uses_same_struct()(uint64,uint64)",
                "args": None,
                }
            ),
            compilation_params=compilation_params
        )

class DuplicateStructsFactoryUpdateParams:
    """Parameters for 'update' operations of DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        params: algokit_utils.CommonAppCallCreateParams | None = None,
        
    ) -> algokit_utils.AppUpdateParams:
        """Updates an instance using a bare call"""
        params = params or algokit_utils.CommonAppCallCreateParams()
        return self.app_factory.params.bare.deploy_update(
            algokit_utils.AppFactoryCreateParams(**dataclasses.asdict(params)),
            )

class DuplicateStructsFactoryDeleteParams:
    """Parameters for 'delete' operations of DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        params: algokit_utils.CommonAppCallCreateParams | None = None,
        
    ) -> algokit_utils.AppDeleteParams:
        """Deletes an instance using a bare call"""
        params = params or algokit_utils.CommonAppCallCreateParams()
        return self.app_factory.params.bare.deploy_delete(
            algokit_utils.AppFactoryCreateParams(**dataclasses.asdict(params)),
            )


class DuplicateStructsFactoryCreateTransaction:
    """Create transactions for DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory
        self.create = DuplicateStructsFactoryCreateTransactionCreate(app_factory)


class DuplicateStructsFactoryCreateTransactionCreate:
    """Create new instances of DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        params: algokit_utils.CommonAppCallCreateParams | None = None,
    ) -> Transaction:
        """Creates a new instance using a bare call"""
        params = params or algokit_utils.CommonAppCallCreateParams()
        return self.app_factory.create_transaction.bare.create(
            algokit_utils.AppFactoryCreateParams(**dataclasses.asdict(params)),
        )


class DuplicateStructsFactorySend:
    """Send calls to DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory
        self.create = DuplicateStructsFactorySendCreate(app_factory)


class DuplicateStructsFactorySendCreate:
    """Send create calls to DuplicateStructs contract"""

    def __init__(self, app_factory: algokit_utils.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        params: algokit_utils.CommonAppCallCreateParams | None = None,
        send_params: algokit_utils.SendParams | None = None,
        compilation_params: algokit_utils.AppClientCompilationParams | None = None,
    ) -> tuple[DuplicateStructsClient, algokit_utils.SendAppCreateTransactionResult]:
        """Creates a new instance using a bare call"""
        params = params or algokit_utils.CommonAppCallCreateParams()
        result = self.app_factory.send.bare.create(
            algokit_utils.AppFactoryCreateParams(**dataclasses.asdict(params)),
            send_params=send_params,
            compilation_params=compilation_params
        )
        return DuplicateStructsClient(result[0]), result[1]


class DuplicateStructsComposer:
    """Composer for creating transaction groups for DuplicateStructs contract calls"""

    def __init__(self, client: "DuplicateStructsClient"):
        self.client = client
        self._composer = client.algorand.new_group()
        self._result_mappers: list[typing.Callable[[algokit_utils.ABIReturn | None], typing.Any] | None] = []

    def method_a_that_uses_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "DuplicateStructsComposer":
        self._composer.add_app_call_method_call(
            self.client.params.method_a_that_uses_struct(
                
                params=params,
            )
        )
        self._result_mappers.append(
            lambda v: self.client.decode_return_value(
                "method_a_that_uses_struct()(uint64,uint64)", v
            )
        )
        return self

    def method_b_that_uses_same_struct(
        self,
        params: algokit_utils.CommonAppCallParams | None = None
    ) -> "DuplicateStructsComposer":
        self._composer.add_app_call_method_call(
            self.client.params.method_b_that_uses_same_struct(
                
                params=params,
            )
        )
        self._result_mappers.append(
            lambda v: self.client.decode_return_value(
                "method_b_that_uses_same_struct()(uint64,uint64)", v
            )
        )
        return self

    def clear_state(
        self,
        *,
        args: list[bytes] | None = None,
        params: algokit_utils.CommonAppCallParams | None = None,
    ) -> "DuplicateStructsComposer":
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
    ) -> "DuplicateStructsComposer":
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
