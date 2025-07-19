from collections.abc import Generator

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.generators.helpers import get_abi_method_operations
from algokit_client_generator.generators.typed_client import PropertyType, _generate_common_method_params
from algokit_client_generator.spec import ContractMethod

OPERATION_TO_METHOD_CALL_PREFIX = {
    "update": "update",
    "delete": "delete",
    "opt_in": "call",
    "call": "call",
    "close_out": "call",
}


def get_operation_composer_class_name(contract_name: str, operation: str) -> str:
    """Get the class name for a specific operation composer"""
    # Convert snake_case operation to PascalCase (e.g., close_out -> CloseOut)
    operation_pascal = utils.to_pascal_case(operation)
    return f"_{contract_name}{operation_pascal}Composer"


def generate_operation_composer(
    context: GeneratorContext,
    operation: str,
    methods: list[ContractMethod],
) -> Generator[DocumentParts, None, None]:
    """Generate a composer class for a specific operation"""
    if not methods:
        return

    class_name = get_operation_composer_class_name(context.contract_name, operation)

    yield utils.indented(f"""
class {class_name}:
    def __init__(self, composer: \"{context.contract_name}Composer\"):
        self.composer = composer
""")
    yield Part.IncIndent

    # Generate ABI methods for this operation
    for method in methods:
        if not method.abi:
            continue
        # Reuse the common method params generator but strip the return type
        method_params, _ = _generate_common_method_params(context, method, PropertyType.PARAMS, operation=operation)
        method_params = method_params.rsplit(" ->", 1)[0]
        method_params += f' -> "{context.contract_name}Composer":'
        compilation_params = "compilation_params=compilation_params" if operation == "update" else ""

        yield utils.indented(f"""
{method_params}
    self.composer._composer.add_app_{OPERATION_TO_METHOD_CALL_PREFIX[operation]}_method_call(
        self.composer.client.params.{operation}.{method.abi.client_method_name}(
            {"args=args," if method.abi.args else ""}
            params=params,
            {compilation_params}
        )
    )
    self.composer._result_mappers.append(
        lambda v: self.composer.client.decode_return_value(
            "{method.abi.method.get_signature()}", v
        )
    )
    return self.composer
""")

    yield Part.DecIndent


def generate_composer(context: GeneratorContext) -> DocumentParts:
    """Generate the composer class for creating transaction groups"""

    operations = get_abi_method_operations(context)

    operation_class_names: dict[str, str] = {}
    for operation, methods in operations.items():
        if methods:
            class_name = get_operation_composer_class_name(context.contract_name, operation)
            operation_class_names[operation] = class_name

            class_name_gen = generate_operation_composer(context, operation, methods)
            if class_name_gen:  # Only proceed if generator exists
                yield from class_name_gen
                yield Part.Gap2

    # Then generate main composer class
    yield utils.indented(f"""
class {context.contract_name}Composer:
    \"\"\"Composer for creating transaction groups for {context.contract_name} contract calls\"\"\"

    def __init__(self, client: "{context.contract_name}Client"):
        self.client = client
        self._composer = client.algorand.new_group()
        self._result_mappers: list[typing.Callable[[algokit_utils.ABIReturn | None], object] | None] = []
""")
    yield Part.IncIndent

    # Generate properties for operations
    for operation, class_name in operation_class_names.items():
        yield Part.Gap1
        yield utils.indented(f"""
@property
def {operation}(self) -> "{class_name}":
    return {class_name}(self)
""")

    # Generate methods for no_op ABI calls
    for method in context.methods.all_abi_methods:
        if not method.abi or "no_op" not in method.on_complete:
            continue

        if context.mode == "minimal" and (
            method.call_config == "create" or method.on_complete in (["update_application"], ["delete_application"])
        ):
            continue

        method_params, has_args = _generate_common_method_params(
            context, method, PropertyType.PARAMS, operation=operation
        )
        method_params = method_params.rsplit(" ->", 1)[0]

        method_params += f' -> "{context.contract_name}Composer":'

        yield Part.Gap1
        yield utils.indented(f"""
{method_params}
    self._composer.add_app_call_method_call(
        self.client.params.{method.abi.client_method_name}(
            {"args=args, " if method.abi.args else ""}
            params=params,
        )
    )
    self._result_mappers.append(
        lambda v: self.client.decode_return_value(
            "{method.abi.method.get_signature()}", v
        )
    )
    return self
""")

    # Add utility methods
    yield Part.Gap1
    yield utils.indented(f"""
def clear_state(
    self,
    *,
    args: list[bytes] | None = None,
    params: algokit_utils.CommonAppCallParams | None = None,
) -> \"{context.contract_name}Composer\":
    params=params or algokit_utils.CommonAppCallParams()
    self._composer.add_app_call(
        self.client.params.clear_state(
            algokit_utils.AppClientBareCallParams(
                **{{
                    **dataclasses.asdict(params),
                    "args": args
                }}
            )
        )
    )
    return self

def add_transaction(
    self, txn: Transaction, signer: TransactionSigner | None = None
) -> \"{context.contract_name}Composer\":
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
""")
    yield Part.DecIndent
