from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts


def generate_imports(context: GeneratorContext) -> DocumentParts:
    yield from utils.lines("""
# common
import dataclasses
import typing
# algokit utils
from algokit_abi import arc56
import algokit_utils
from algokit_utils import AlgorandClient as _AlgoKitAlgorandClient
from algokit_common.source_map import ProgramSourceMap as SourceMap
from algokit_transact.models.common import OnApplicationComplete
from algokit_transact.models.transaction import Transaction
from algokit_utils.protocols.signer import TransactionSigner
from algokit_algod_client.models import SimulateTraceConfig
""")
