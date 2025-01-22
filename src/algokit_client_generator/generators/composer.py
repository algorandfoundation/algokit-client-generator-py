from collections.abc import Generator

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.generators.typed_client import PropertyType, _generate_common_method_params
from algokit_client_generator.spec import ContractMethod

OPERATION_TO_METHOD_CALL_PREFIX = {
    "update": "update",
    "delete": "delete",
    "opt_in": "call",
    "call": "call",
}


def get_operation_composer_class_name(contract_name: str, operation: str) -> str:
    """Get the class name for a specific operation composer"""
    return f"_{contract_name}{operation.capitalize()}Composer"


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

        yield utils.indented(f"""
{method_params}
    self.composer._composer.add_app_{OPERATION_TO_METHOD_CALL_PREFIX[operation]}_method_call(
        self.composer.client.params.{operation}.{method.abi.client_method_name}(
            {'args=args,' if method.abi.args else ''}
            account_references=account_references,
            app_references=app_references,
            asset_references=asset_references,
            box_references=box_references,
            extra_fee=extra_fee,
            first_valid_round=first_valid_round,
            lease=lease,
            max_fee=max_fee,
            note=note,
            rekey_to=rekey_to,
            sender=sender,
            signer=signer,
            static_fee=static_fee,
            validity_window=validity_window,
            last_valid_round=last_valid_round,
            populate_app_call_resources=populate_app_call_resources,
            {'updatable=updatable, deletable=deletable, deploy_time_params=deploy_time_params'
             if operation == 'update'
             else ''}
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

    # First generate operation classes
    operations = {
        "update": [
            m for m in context.methods.all_methods if m.call_config == "call" and "update_application" in m.on_complete
        ],
        "delete": [
            m for m in context.methods.all_methods if m.call_config == "call" and "delete_application" in m.on_complete
        ],
        "opt_in": [m for m in context.methods.all_methods if m.call_config == "call" and "opt_in" in m.on_complete],
    }

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
        self._result_mappers: list[typing.Callable[[applications_abi.ABIReturn | None], typing.Any] | None] = []
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
            {'args=args, ' if method.abi.args else ''}
            account_references=account_references,
            app_references=app_references,
            asset_references=asset_references,
            box_references=box_references,
            extra_fee=extra_fee,
            first_valid_round=first_valid_round,
            lease=lease,
            max_fee=max_fee,
            note=note,
            rekey_to=rekey_to,
            sender=sender,
            signer=signer,
            static_fee=static_fee,
            validity_window=validity_window,
            last_valid_round=last_valid_round,
            populate_app_call_resources=populate_app_call_resources,
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
    account_references: list[str] | None = None,
    app_references: list[int] | None = None,
    asset_references: list[int] | None = None,
    box_references: list[models.BoxReference | models.BoxIdentifier] | None = None,
    extra_fee: models.AlgoAmount | None = None,
    lease: bytes | None = None,
    max_fee: models.AlgoAmount | None = None,
    note: bytes | None = None,
    rekey_to: str | None = None,
    sender: str | None = None,
    signer: TransactionSigner | None = None,
    static_fee: models.AlgoAmount | None = None,
    validity_window: int | None = None,
    first_valid_round: int | None = None,
    last_valid_round: int | None = None,
    populate_app_call_resources: bool = False,
) -> \"{context.contract_name}Composer\":
    self._composer.add_app_call(
        self.client.params.clear_state(
            applications.AppClientBareCallWithSendParams(
                account_references=account_references,
                app_references=app_references,
                asset_references=asset_references,
                box_references=box_references,
                extra_fee=extra_fee,
                first_valid_round=first_valid_round,
                lease=lease,
                max_fee=max_fee,
                note=note,
                rekey_to=rekey_to,
                sender=sender,
                signer=signer,
                static_fee=static_fee,
                validity_window=validity_window,
                last_valid_round=last_valid_round,
                populate_app_call_resources=populate_app_call_resources,
            )
        )
    )
    return self

def add_transaction(
    self, txn: Transaction, signer: TransactionSigner | None = None
) -> \"{context.contract_name}Composer\":
    self._composer.add_transaction(txn, signer)
    return self

def composer(self) -> transactions.TransactionComposer:
    return self._composer

def simulate(
    self,
    allow_more_logs: bool | None = None,
    allow_empty_signatures: bool | None = None,
    allow_unnamed_resources: bool | None = None,
    extra_opcode_budget: int | None = None,
    exec_trace_config: SimulateTraceConfig | None = None,
    simulation_round: int | None = None,
    skip_signatures: int | None = None,
) -> transactions.SendAtomicTransactionComposerResults:
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
    max_rounds_to_wait: int | None = None,
    suppress_log: bool | None = None,
    populate_app_call_resources: bool | None = None,
) -> transactions.SendAtomicTransactionComposerResults:
    return self._composer.send(
        max_rounds_to_wait=max_rounds_to_wait,
        suppress_log=suppress_log,
        populate_app_call_resources=populate_app_call_resources,
    )
""")
    yield Part.DecIndent
