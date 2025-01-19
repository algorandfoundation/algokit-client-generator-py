from collections.abc import Generator

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.generators.typed_client import PropertyType, _generate_common_method_params
from algokit_client_generator.spec import ContractMethod


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
        method_params = _generate_common_method_params(method, PropertyType.PARAMS, operation=operation).rsplit(
            " ->", 1
        )[0]

        method_params += f' -> "{context.contract_name}Composer":'

        args_handling = ""
        if method.abi.args:
            args_handling = f"""
    method_args = None
    if {'args is not None and ' if all(arg.has_default for arg in method.abi.args) else ''}isinstance(args, tuple):
        method_args = args
    elif {'args is not None and ' if all(arg.has_default for arg in method.abi.args) else ''}isinstance(args, dict):
        method_args = tuple(args.values())
    if method_args:
        method_args = [astuple(arg) if is_dataclass(arg) else arg for arg in method_args] # type: ignore
"""

        yield utils.indented(f"""
{method_params}{args_handling}
    self.composer._composer.add_app_call_method_call(
        self.composer.client.params.{operation}.{method.abi.client_method_name}(
            {'args=method_args, # type: ignore' if method.abi.args else ''}
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
        self._result_mappers: list[Optional[Callable[[Optional[ABIReturn]], Any]]] = []
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

        method_params = _generate_common_method_params(method, PropertyType.PARAMS).rsplit(" ->", 1)[0]

        method_params += f' -> "{context.contract_name}Composer":'

        args_handling = ""
        if method.abi.args:
            args_handling = f"""
    method_args = None
    if {'args is not None and ' if all(arg.has_default for arg in method.abi.args) else ''}isinstance(args, tuple):
        method_args = args
    elif {'args is not None and ' if all(arg.has_default for arg in method.abi.args) else ''}isinstance(args, dict):
        method_args = tuple(args.values())
"""

        yield Part.Gap1
        yield utils.indented(f"""
{method_params}{args_handling}
    self._composer.add_app_call_method_call(
        self.client.params.{method.abi.client_method_name}(
            {'args=method_args, # type: ignore' if method.abi.args else ''}
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
    account_references: Optional[list[str]] = None,
    app_references: Optional[list[int]] = None,
    asset_references: Optional[list[int]] = None,
    box_references: Optional[list[Union[BoxReference, BoxIdentifier]]] = None,
    extra_fee: Optional[AlgoAmount] = None,
    lease: Optional[bytes] = None,
    max_fee: Optional[AlgoAmount] = None,
    note: Optional[bytes] = None,
    rekey_to: Optional[str] = None,
    sender: Optional[str] = None,
    signer: Optional[TransactionSigner] = None,
    static_fee: Optional[AlgoAmount] = None,
    validity_window: Optional[int] = None,
    first_valid_round: Optional[int] = None,
    last_valid_round: Optional[int] = None,
) -> \"{context.contract_name}Composer\":
    self._composer.add_app_call(
        self.client.params.clear_state(
            AppClientBareCallWithSendParams(
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
            )
        )
    )
    return self

def add_transaction(
    self, txn: Transaction, signer: Optional[TransactionSigner] = None
) -> \"{context.contract_name}Composer\":
    self._composer.add_transaction(txn, signer)
    return self

def composer(self) -> TransactionComposer:
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
) -> SendAtomicTransactionComposerResults:
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
) -> SendAtomicTransactionComposerResults:
    return self._composer.send(
        max_rounds_to_wait=max_rounds_to_wait,
        suppress_log=suppress_log,
        populate_app_call_resources=populate_app_call_resources,
    )
""")
    yield Part.DecIndent
