# flake8: noqa
# fmt: off
# mypy: disable-error-code="no-any-return, no-untyped-call"
# This file was automatically generated by algokit-client-generator.
# DO NOT MODIFY IT BY HAND.
import base64
import dataclasses
import decimal
import typing
from abc import ABC, abstractmethod

import algokit_utils
import algosdk
from algosdk.atomic_transaction_composer import TransactionSigner, TransactionWithSigner

_APP_SPEC_JSON = r"""{
    "hints": {
        "hello(string)string": {
            "call_config": {
                "no_op": "CALL"
            }
        },
        "hello()string": {
            "call_config": {
                "no_op": "CALL"
            }
        },
        "create(string)string": {
            "call_config": {
                "no_op": "CREATE"
            }
        },
        "create(string,uint32)void": {
            "call_config": {
                "no_op": "CREATE"
            }
        }
    },
    "source": {
        "approval": "I3ByYWdtYSB2ZXJzaW9uIDgKaW50Y2Jsb2NrIDAgMSAxMApieXRlY2Jsb2NrIDB4IDB4NzQ2OTZkNjU3MyAweDY3NzI2NTY1NzQ2OTZlNjcgMHgxNTFmN2M3NQp0eG4gTnVtQXBwQXJncwppbnRjXzAgLy8gMAo9PQpibnogbWFpbl9sMTAKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMApwdXNoYnl0ZXMgMHgwMmJlY2UxMSAvLyAiaGVsbG8oc3RyaW5nKXN0cmluZyIKPT0KYm56IG1haW5fbDkKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMApwdXNoYnl0ZXMgMHhhYjA2YzFhOCAvLyAiaGVsbG8oKXN0cmluZyIKPT0KYm56IG1haW5fbDgKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMApwdXNoYnl0ZXMgMHg5N2YxZmMxMSAvLyAiY3JlYXRlKHN0cmluZylzdHJpbmciCj09CmJueiBtYWluX2w3CnR4bmEgQXBwbGljYXRpb25BcmdzIDAKcHVzaGJ5dGVzIDB4NjAxOTMyNjQgLy8gImNyZWF0ZShzdHJpbmcsdWludDMyKXZvaWQiCj09CmJueiBtYWluX2w2CmVycgptYWluX2w2Ogp0eG4gT25Db21wbGV0aW9uCmludGNfMCAvLyBOb09wCj09CnR4biBBcHBsaWNhdGlvbklECmludGNfMCAvLyAwCj09CiYmCmFzc2VydAp0eG5hIEFwcGxpY2F0aW9uQXJncyAxCnN0b3JlIDMKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMgppbnRjXzAgLy8gMApleHRyYWN0X3VpbnQzMgpzdG9yZSA0CmxvYWQgMwpsb2FkIDQKY2FsbHN1YiBjcmVhdGVfNwppbnRjXzEgLy8gMQpyZXR1cm4KbWFpbl9sNzoKdHhuIE9uQ29tcGxldGlvbgppbnRjXzAgLy8gTm9PcAo9PQp0eG4gQXBwbGljYXRpb25JRAppbnRjXzAgLy8gMAo9PQomJgphc3NlcnQKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMQpjYWxsc3ViIGNyZWF0ZV82CnN0b3JlIDIKYnl0ZWNfMyAvLyAweDE1MWY3Yzc1CmxvYWQgMgpjb25jYXQKbG9nCmludGNfMSAvLyAxCnJldHVybgptYWluX2w4Ogp0eG4gT25Db21wbGV0aW9uCmludGNfMCAvLyBOb09wCj09CnR4biBBcHBsaWNhdGlvbklECmludGNfMCAvLyAwCiE9CiYmCmFzc2VydApjYWxsc3ViIGhlbGxvXzQKc3RvcmUgMQpieXRlY18zIC8vIDB4MTUxZjdjNzUKbG9hZCAxCmNvbmNhdApsb2cKaW50Y18xIC8vIDEKcmV0dXJuCm1haW5fbDk6CnR4biBPbkNvbXBsZXRpb24KaW50Y18wIC8vIE5vT3AKPT0KdHhuIEFwcGxpY2F0aW9uSUQKaW50Y18wIC8vIDAKIT0KJiYKYXNzZXJ0CnR4bmEgQXBwbGljYXRpb25BcmdzIDEKY2FsbHN1YiBoZWxsb18zCnN0b3JlIDAKYnl0ZWNfMyAvLyAweDE1MWY3Yzc1CmxvYWQgMApjb25jYXQKbG9nCmludGNfMSAvLyAxCnJldHVybgptYWluX2wxMDoKdHhuIE9uQ29tcGxldGlvbgppbnRjXzAgLy8gTm9PcAo9PQpibnogbWFpbl9sMTYKdHhuIE9uQ29tcGxldGlvbgppbnRjXzEgLy8gT3B0SW4KPT0KYm56IG1haW5fbDE1CnR4biBPbkNvbXBsZXRpb24KcHVzaGludCA0IC8vIFVwZGF0ZUFwcGxpY2F0aW9uCj09CmJueiBtYWluX2wxNAplcnIKbWFpbl9sMTQ6CnR4biBBcHBsaWNhdGlvbklECmludGNfMCAvLyAwCiE9CmFzc2VydApjYWxsc3ViIHVwZGF0ZV8yCmludGNfMSAvLyAxCnJldHVybgptYWluX2wxNToKdHhuIEFwcGxpY2F0aW9uSUQKaW50Y18wIC8vIDAKPT0KYXNzZXJ0CmNhbGxzdWIgYmFyZWNyZWF0ZV81CmludGNfMSAvLyAxCnJldHVybgptYWluX2wxNjoKdHhuIEFwcGxpY2F0aW9uSUQKaW50Y18wIC8vIDAKPT0KYXNzZXJ0CmNhbGxzdWIgYmFyZWNyZWF0ZV81CmludGNfMSAvLyAxCnJldHVybgoKLy8gaW50X3RvX2FzY2lpCmludHRvYXNjaWlfMDoKcHJvdG8gMSAxCnB1c2hieXRlcyAweDMwMzEzMjMzMzQzNTM2MzczODM5IC8vICIwMTIzNDU2Nzg5IgpmcmFtZV9kaWcgLTEKaW50Y18xIC8vIDEKZXh0cmFjdDMKcmV0c3ViCgovLyBpdG9hCml0b2FfMToKcHJvdG8gMSAxCmZyYW1lX2RpZyAtMQppbnRjXzAgLy8gMAo9PQpibnogaXRvYV8xX2w1CmZyYW1lX2RpZyAtMQppbnRjXzIgLy8gMTAKLwppbnRjXzAgLy8gMAo+CmJueiBpdG9hXzFfbDQKYnl0ZWNfMCAvLyAiIgppdG9hXzFfbDM6CmZyYW1lX2RpZyAtMQppbnRjXzIgLy8gMTAKJQpjYWxsc3ViIGludHRvYXNjaWlfMApjb25jYXQKYiBpdG9hXzFfbDYKaXRvYV8xX2w0OgpmcmFtZV9kaWcgLTEKaW50Y18yIC8vIDEwCi8KY2FsbHN1YiBpdG9hXzEKYiBpdG9hXzFfbDMKaXRvYV8xX2w1OgpwdXNoYnl0ZXMgMHgzMCAvLyAiMCIKaXRvYV8xX2w2OgpyZXRzdWIKCi8vIHVwZGF0ZQp1cGRhdGVfMjoKcHJvdG8gMCAwCnR4biBTZW5kZXIKZ2xvYmFsIENyZWF0b3JBZGRyZXNzCj09Ci8vIHVuYXV0aG9yaXplZAphc3NlcnQKcHVzaGludCBUTVBMX1VQREFUQUJMRSAvLyBUTVBMX1VQREFUQUJMRQovLyBDaGVjayBhcHAgaXMgdXBkYXRhYmxlCmFzc2VydApyZXRzdWIKCi8vIGhlbGxvCmhlbGxvXzM6CnByb3RvIDEgMQpieXRlY18wIC8vICIiCmJ5dGVjXzAgLy8gIiIKc3RvcmUgNQppbnRjXzAgLy8gMApzdG9yZSA2CmhlbGxvXzNfbDE6CmxvYWQgNgpieXRlY18xIC8vICJ0aW1lcyIKYXBwX2dsb2JhbF9nZXQKPApieiBoZWxsb18zX2wzCmxvYWQgNQpieXRlY18yIC8vICJncmVldGluZyIKYXBwX2dsb2JhbF9nZXQKY29uY2F0CnB1c2hieXRlcyAweDJjMjAgLy8gIiwgIgpjb25jYXQKZnJhbWVfZGlnIC0xCmV4dHJhY3QgMiAwCmNvbmNhdApwdXNoYnl0ZXMgMHgwYSAvLyAiXG4iCmNvbmNhdApzdG9yZSA1CmxvYWQgNgppbnRjXzEgLy8gMQorCnN0b3JlIDYKYiBoZWxsb18zX2wxCmhlbGxvXzNfbDM6CmxvYWQgNQpmcmFtZV9idXJ5IDAKZnJhbWVfZGlnIDAKbGVuCml0b2IKZXh0cmFjdCA2IDAKZnJhbWVfZGlnIDAKY29uY2F0CmZyYW1lX2J1cnkgMApyZXRzdWIKCi8vIGhlbGxvCmhlbGxvXzQ6CnByb3RvIDAgMQpieXRlY18wIC8vICIiCmJ5dGVjXzAgLy8gIiIKc3RvcmUgNwppbnRjXzAgLy8gMApzdG9yZSA4CmhlbGxvXzRfbDE6CmxvYWQgOApieXRlY18xIC8vICJ0aW1lcyIKYXBwX2dsb2JhbF9nZXQKPApieiBoZWxsb180X2wzCmxvYWQgNwpieXRlY18yIC8vICJncmVldGluZyIKYXBwX2dsb2JhbF9nZXQKY29uY2F0CnB1c2hieXRlcyAweDJjMjA2ZDc5NzM3NDY1NzI3OTIwNzA2NTcyNzM2ZjZlMGEgLy8gIiwgbXlzdGVyeSBwZXJzb25cbiIKY29uY2F0CnN0b3JlIDcKbG9hZCA4CmludGNfMSAvLyAxCisKc3RvcmUgOApiIGhlbGxvXzRfbDEKaGVsbG9fNF9sMzoKbG9hZCA3CmZyYW1lX2J1cnkgMApmcmFtZV9kaWcgMApsZW4KaXRvYgpleHRyYWN0IDYgMApmcmFtZV9kaWcgMApjb25jYXQKZnJhbWVfYnVyeSAwCnJldHN1YgoKLy8gYmFyZV9jcmVhdGUKYmFyZWNyZWF0ZV81Ogpwcm90byAwIDAKYnl0ZWNfMiAvLyAiZ3JlZXRpbmciCnB1c2hieXRlcyAweDQ4NjU2YzZjNmYgLy8gIkhlbGxvIgphcHBfZ2xvYmFsX3B1dApieXRlY18xIC8vICJ0aW1lcyIKaW50Y18xIC8vIDEKYXBwX2dsb2JhbF9wdXQKaW50Y18xIC8vIDEKcmV0dXJuCgovLyBjcmVhdGUKY3JlYXRlXzY6CnByb3RvIDEgMQpieXRlY18wIC8vICIiCmJ5dGVjXzIgLy8gImdyZWV0aW5nIgpmcmFtZV9kaWcgLTEKZXh0cmFjdCAyIDAKYXBwX2dsb2JhbF9wdXQKYnl0ZWNfMSAvLyAidGltZXMiCmludGNfMSAvLyAxCmFwcF9nbG9iYWxfcHV0CmZyYW1lX2RpZyAtMQpleHRyYWN0IDIgMApwdXNoYnl0ZXMgMHg1ZiAvLyAiXyIKY29uY2F0CmJ5dGVjXzEgLy8gInRpbWVzIgphcHBfZ2xvYmFsX2dldApjYWxsc3ViIGl0b2FfMQpjb25jYXQKZnJhbWVfYnVyeSAwCmZyYW1lX2RpZyAwCmxlbgppdG9iCmV4dHJhY3QgNiAwCmZyYW1lX2RpZyAwCmNvbmNhdApmcmFtZV9idXJ5IDAKcmV0c3ViCgovLyBjcmVhdGUKY3JlYXRlXzc6CnByb3RvIDIgMApieXRlY18yIC8vICJncmVldGluZyIKZnJhbWVfZGlnIC0yCmV4dHJhY3QgMiAwCmFwcF9nbG9iYWxfcHV0CmJ5dGVjXzEgLy8gInRpbWVzIgpmcmFtZV9kaWcgLTEKYXBwX2dsb2JhbF9wdXQKaW50Y18xIC8vIDEKcmV0dXJu",
        "clear": "I3ByYWdtYSB2ZXJzaW9uIDgKaW50Y2Jsb2NrIDEKY2FsbHN1YiBjbGVhcl8wCmludGNfMCAvLyAxCnJldHVybgoKLy8gY2xlYXIKY2xlYXJfMDoKcHJvdG8gMCAwCmludGNfMCAvLyAxCnJldHVybg=="
    },
    "state": {
        "global": {
            "num_byte_slices": 1,
            "num_uints": 1
        },
        "local": {
            "num_byte_slices": 0,
            "num_uints": 0
        }
    },
    "schema": {
        "global": {
            "declared": {
                "greeting": {
                    "type": "bytes",
                    "key": "greeting",
                    "descr": ""
                },
                "times": {
                    "type": "uint64",
                    "key": "times",
                    "descr": ""
                }
            },
            "reserved": {}
        },
        "local": {
            "declared": {},
            "reserved": {}
        }
    },
    "contract": {
        "name": "LifeCycleApp",
        "methods": [
            {
                "name": "hello",
                "args": [
                    {
                        "type": "string",
                        "name": "name"
                    }
                ],
                "returns": {
                    "type": "string"
                }
            },
            {
                "name": "hello",
                "args": [],
                "returns": {
                    "type": "string"
                }
            },
            {
                "name": "create",
                "args": [
                    {
                        "type": "string",
                        "name": "greeting"
                    }
                ],
                "returns": {
                    "type": "string"
                },
                "desc": "ABI create method with 1 argument"
            },
            {
                "name": "create",
                "args": [
                    {
                        "type": "string",
                        "name": "greeting"
                    },
                    {
                        "type": "uint32",
                        "name": "times"
                    }
                ],
                "returns": {
                    "type": "void"
                },
                "desc": "ABI create method with 2 arguments"
            }
        ],
        "networks": {}
    },
    "bare_call_config": {
        "no_op": "CREATE",
        "opt_in": "CREATE",
        "update_application": "CALL"
    }
}"""
APP_SPEC = algokit_utils.ApplicationSpecification.from_json(_APP_SPEC_JSON)
_TReturn = typing.TypeVar("_TReturn")


class _ArgsBase(ABC, typing.Generic[_TReturn]):
    @staticmethod
    @abstractmethod
    def method() -> str:
        ...


_TArgs = typing.TypeVar("_TArgs", bound=_ArgsBase[typing.Any])


@dataclasses.dataclass(kw_only=True)
class _TArgsHolder(typing.Generic[_TArgs]):
    args: _TArgs


@dataclasses.dataclass(kw_only=True)
class DeployCreate(algokit_utils.DeployCreateCallArgs, _TArgsHolder[_TArgs], typing.Generic[_TArgs]):
    pass


def _filter_none(value: dict | typing.Any) -> dict | typing.Any:
    if isinstance(value, dict):
        return {k: _filter_none(v) for k, v in value.items() if v is not None}
    return value


def _as_dict(data: typing.Any, *, convert_all: bool = True) -> dict[str, typing.Any]:
    if data is None:
        return {}
    if not dataclasses.is_dataclass(data):
        raise TypeError(f"{data} must be a dataclass")
    if convert_all:
        result = dataclasses.asdict(data)
    else:
        result = {f.name: getattr(data, f.name) for f in dataclasses.fields(data)}
    return _filter_none(result)


def _convert_transaction_parameters(
    transaction_parameters: algokit_utils.TransactionParameters | None,
) -> algokit_utils.CommonCallParametersDict:
    return typing.cast(algokit_utils.CommonCallParametersDict, _as_dict(transaction_parameters))


def _convert_call_transaction_parameters(
    transaction_parameters: algokit_utils.TransactionParameters | None,
) -> algokit_utils.OnCompleteCallParametersDict:
    return typing.cast(algokit_utils.OnCompleteCallParametersDict, _as_dict(transaction_parameters))


def _convert_create_transaction_parameters(
    transaction_parameters: algokit_utils.TransactionParameters | None,
    on_complete: algokit_utils.OnCompleteActionName,
) -> algokit_utils.CreateCallParametersDict:
    result = typing.cast(algokit_utils.CreateCallParametersDict, _as_dict(transaction_parameters))
    on_complete_enum = on_complete.replace("_", " ").title().replace(" ", "") + "OC"
    result["on_complete"] = getattr(algosdk.transaction.OnComplete, on_complete_enum)
    return result


def _convert_deploy_args(
    deploy_args: algokit_utils.DeployCallArgs | None,
) -> algokit_utils.ABICreateCallArgsDict | None:
    if deploy_args is None:
        return None

    deploy_args_dict = typing.cast(algokit_utils.ABICreateCallArgsDict, _as_dict(deploy_args))
    if isinstance(deploy_args, _TArgsHolder):
        deploy_args_dict["args"] = _as_dict(deploy_args.args)
        deploy_args_dict["method"] = deploy_args.args.method()

    return deploy_args_dict


@dataclasses.dataclass(kw_only=True)
class HelloStringStringArgs(_ArgsBase[str]):
    name: str

    @staticmethod
    def method() -> str:
        return "hello(string)string"


@dataclasses.dataclass(kw_only=True)
class HelloStringArgs(_ArgsBase[str]):
    @staticmethod
    def method() -> str:
        return "hello()string"


@dataclasses.dataclass(kw_only=True)
class CreateStringStringArgs(_ArgsBase[str]):
    """ABI create method with 1 argument"""

    greeting: str

    @staticmethod
    def method() -> str:
        return "create(string)string"


@dataclasses.dataclass(kw_only=True)
class CreateStringUint32VoidArgs(_ArgsBase[None]):
    """ABI create method with 2 arguments"""

    greeting: str
    times: int

    @staticmethod
    def method() -> str:
        return "create(string,uint32)void"


class ByteReader:
    def __init__(self, data: bytes):
        self._data = data

    @property
    def as_bytes(self) -> bytes:
        return self._data

    @property
    def as_str(self) -> str:
        return self._data.decode("utf8")

    @property
    def as_base64(self) -> str:
        return base64.b64encode(self._data).decode("utf8")

    @property
    def as_hex(self) -> str:
        return self._data.hex()


class GlobalState:
    def __init__(self, data: dict[bytes, bytes | int]):
        self.greeting = ByteReader(typing.cast(bytes, data.get(b"greeting")))
        self.times = typing.cast(int, data.get(b"times"))


class LifeCycleAppClient:
    @typing.overload
    def __init__(
        self,
        algod_client: algosdk.v2client.algod.AlgodClient,
        *,
        app_id: int = 0,
        signer: TransactionSigner | algokit_utils.Account | None = None,
        sender: str | None = None,
        suggested_params: algosdk.transaction.SuggestedParams | None = None,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ) -> None:
        ...

    @typing.overload
    def __init__(
        self,
        algod_client: algosdk.v2client.algod.AlgodClient,
        *,
        creator: str | algokit_utils.Account,
        indexer_client: algosdk.v2client.indexer.IndexerClient | None = None,
        existing_deployments: algokit_utils.AppLookup | None = None,
        signer: TransactionSigner | algokit_utils.Account | None = None,
        sender: str | None = None,
        suggested_params: algosdk.transaction.SuggestedParams | None = None,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ) -> None:
        ...

    def __init__(
        self,
        algod_client: algosdk.v2client.algod.AlgodClient,
        *,
        creator: str | algokit_utils.Account | None = None,
        indexer_client: algosdk.v2client.indexer.IndexerClient | None = None,
        existing_deployments: algokit_utils.AppLookup | None = None,
        app_id: int = 0,
        signer: TransactionSigner | algokit_utils.Account | None = None,
        sender: str | None = None,
        suggested_params: algosdk.transaction.SuggestedParams | None = None,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ) -> None:
        self.app_spec = APP_SPEC

        # calling full __init__ signature, so ignoring mypy warning about overloads
        self.app_client = algokit_utils.ApplicationClient(  # type: ignore[call-overload, misc]
            algod_client=algod_client,
            app_spec=self.app_spec,
            app_id=app_id,
            creator=creator,
            indexer_client=indexer_client,
            existing_deployments=existing_deployments,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            template_values=template_values,
            app_name=app_name,
        )

    @property
    def algod_client(self) -> algosdk.v2client.algod.AlgodClient:
        return self.app_client.algod_client
    
    @property
    def app_id(self) -> int:
        return self.app_client.app_id
    
    @app_id.setter
    def app_id(self, value: int) -> None:
        self.app_client.app_id = value
    
    @property
    def app_address(self) -> str:
        return self.app_client.app_address
    
    @property
    def sender(self) -> str | None:
        return self.app_client.sender
    
    @sender.setter
    def sender(self, value: str) -> None:
        self.app_client.sender = value
    
    @property
    def signer(self) -> TransactionSigner | None:
        return self.app_client.signer
    
    @signer.setter
    def signer(self, value: TransactionSigner) -> None:
        self.app_client.signer = value
    
    @property
    def suggested_params(self) -> algosdk.transaction.SuggestedParams | None:
        return self.app_client.suggested_params
    
    @suggested_params.setter
    def suggested_params(self, value: algosdk.transaction.SuggestedParams | None) -> None:
        self.app_client.suggested_params = value

    def get_global_state(self) -> GlobalState:
        """Returns the application's global state wrapped in a strongly typed class with options to format the stored value"""

        state = typing.cast(dict[bytes, bytes | int], self.app_client.get_global_state(raw=True))
        return GlobalState(state)

    def hello_string_string(
        self,
        *,
        name: str,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> algokit_utils.ABITransactionResponse[str]:
        """Calls `hello(string)string` ABI method
        
        :param str name: The `name` ABI parameter
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.ABITransactionResponse[str]: The result of the transaction"""

        args = HelloStringStringArgs(
            name=name,
        )
        result = self.app_client.call(
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return result

    def hello_string(
        self,
        *,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> algokit_utils.ABITransactionResponse[str]:
        """Calls `hello()string` ABI method
        
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.ABITransactionResponse[str]: The result of the transaction"""

        args = HelloStringArgs()
        result = self.app_client.call(
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return result

    def create_bare(
        self,
        *,
        on_complete: typing.Literal["no_op", "opt_in"] = "no_op",
        transaction_parameters: algokit_utils.CreateTransactionParameters | None = None,
    ) -> algokit_utils.TransactionResponse:
        """Creates an application using one of the no_op, opt_in bare methods
        
        :param typing.Literal[no_op, opt_in] on_complete: On completion type to use
        :param algokit_utils.CreateTransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.TransactionResponse: The result of the transaction"""

        result = self.app_client.create(
            call_abi_method=False,
            transaction_parameters=_convert_create_transaction_parameters(transaction_parameters, on_complete),
        )
        return result

    def create_create_string_string(
        self,
        *,
        greeting: str,
        on_complete: typing.Literal["no_op"] = "no_op",
        transaction_parameters: algokit_utils.CreateTransactionParameters | None = None,
    ) -> algokit_utils.ABITransactionResponse[str]:
        """ABI create method with 1 argument
        
        Calls `create(string)string` ABI method
        
        :param str greeting: The `greeting` ABI parameter
        :param typing.Literal[no_op] on_complete: On completion type to use
        :param algokit_utils.CreateTransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.ABITransactionResponse[str]: The result of the transaction"""

        args = CreateStringStringArgs(
            greeting=greeting,
        )
        result = self.app_client.create(
            call_abi_method=args.method(),
            transaction_parameters=_convert_create_transaction_parameters(transaction_parameters, on_complete),
            **_as_dict(args, convert_all=True),
        )
        return result

    def create_create_string_uint32_void(
        self,
        *,
        greeting: str,
        times: int,
        on_complete: typing.Literal["no_op"] = "no_op",
        transaction_parameters: algokit_utils.CreateTransactionParameters | None = None,
    ) -> algokit_utils.ABITransactionResponse[None]:
        """ABI create method with 2 arguments
        
        Calls `create(string,uint32)void` ABI method
        
        :param str greeting: The `greeting` ABI parameter
        :param int times: The `times` ABI parameter
        :param typing.Literal[no_op] on_complete: On completion type to use
        :param algokit_utils.CreateTransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.ABITransactionResponse[None]: The result of the transaction"""

        args = CreateStringUint32VoidArgs(
            greeting=greeting,
            times=times,
        )
        result = self.app_client.create(
            call_abi_method=args.method(),
            transaction_parameters=_convert_create_transaction_parameters(transaction_parameters, on_complete),
            **_as_dict(args, convert_all=True),
        )
        return result

    def update_bare(
        self,
        *,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> algokit_utils.TransactionResponse:
        """Calls the update_application bare method
        
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.TransactionResponse: The result of the transaction"""

        result = self.app_client.update(
            call_abi_method=False,
            transaction_parameters=_convert_transaction_parameters(transaction_parameters),
        )
        return result

    def clear_state(
        self,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
        app_args: list[bytes] | None = None,
    ) -> algokit_utils.TransactionResponse:
        return self.app_client.clear_state(_convert_transaction_parameters(transaction_parameters), app_args)

    def deploy(
        self,
        version: str | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        allow_update: bool | None = None,
        allow_delete: bool | None = None,
        on_update: algokit_utils.OnUpdate = algokit_utils.OnUpdate.Fail,
        on_schema_break: algokit_utils.OnSchemaBreak = algokit_utils.OnSchemaBreak.Fail,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        create_args: DeployCreate[CreateStringStringArgs | CreateStringUint32VoidArgs] | algokit_utils.DeployCallArgs | None = None,
        update_args: algokit_utils.DeployCallArgs | None = None,
        delete_args: algokit_utils.DeployCallArgs | None = None,
    ) -> algokit_utils.DeployResponse:
        return self.app_client.deploy(
            version,
            signer=signer,
            sender=sender,
            allow_update=allow_update,
            allow_delete=allow_delete,
            on_update=on_update,
            on_schema_break=on_schema_break,
            template_values=template_values,
            create_args=_convert_deploy_args(create_args),
            update_args=_convert_deploy_args(update_args),
            delete_args=_convert_deploy_args(delete_args),
        )
