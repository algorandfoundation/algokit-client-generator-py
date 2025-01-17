from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts


def generate_imports(context: GeneratorContext) -> DocumentParts:
    yield utils.lines("""
from dataclasses import dataclass, asdict, replace
from typing import (
    Any,
    Callable,
    Optional,
    Protocol,
    Union,
    overload,
    Generic,
    Tuple,
    TypedDict,
    runtime_checkable,
    cast,
    Literal,
)
import algosdk
from algosdk.transaction import OnComplete
from algokit_utils.applications import AppFactoryCreateParams, AppFactoryCreateMethodCallResult, AppFactoryCreateWithSendParams, AppFactoryCreateMethodCallParams
from algokit_utils.applications import (
    AppClient,
    AppClientBareCallWithSendParams,
    AppClientMethodCallWithSendParams,
    AppClientMethodCallParams,
    AppClientParams,
    AppFactory,
    AppFactoryParams,
    Arc56Contract,
    AppClientBareCallWithCompilationAndSendParams,
    AppClientBareCallParams,
    AppClientCreateSchema,
    BaseOnCompleteParams,
    AppClientMethodCallParams,
    AppClientBareCallParams,
    AppClientBareCallCreateParams,
    AppClientMethodCallCreateParams,
    BaseAppClientMethodCallParams,
)
from algokit_utils.transactions import SendAppCreateTransactionResult, AppCallParams, AppCreateParams, AppDeleteParams, AppUpdateParams
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algokit_utils.applications.abi import ABIReturn, ABIStruct, ABIValue
from algokit_utils.applications.app_deployer import AppLookup, OnSchemaBreak, OnUpdate
from algokit_utils.applications.app_factory import (
    AppFactoryDeployResponse,
    TypedAppFactoryProtocol,
)
from algokit_utils.models import AlgoAmount, BoxIdentifier, BoxReference
from algokit_utils.models.state import TealTemplateParams
from algokit_utils.protocols import AlgorandClientProtocol
from algokit_utils.transactions import (
    AppCallMethodCallParams,
    AppCallParams,
    SendAppTransactionResult,
    SendAtomicTransactionComposerResults,
    TransactionComposer,
)
from algokit_utils.transactions.transaction_composer import BuiltTransactions
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.source_map import SourceMap
from algosdk.transaction import Transaction
from algosdk.v2client.models import SimulateTraceConfig
""")
