from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part


def generate_composer(context: GeneratorContext) -> DocumentParts:
    """Generate the composer class for creating transaction groups"""
    yield utils.indented(f"""
class {context.contract_name}Composer:
    \"\"\"Composer for creating transaction groups for {context.contract_name} contract calls\"\"\"

    def __init__(self, client: "{context.contract_name}Client"):
        self.client = client
        self._composer = client.algorand.new_group()
        self._result_mappers: list[Optional[Callable[[Optional[ABIReturn]], Any]]] = []

""")
    yield Part.IncIndent

    # Generate method for each ABI method
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi or method.call_config == "create":
            continue

        if not first:
            yield Part.Gap1
        first = False

        # Generate the type annotation for args parameter
        args_type = "Any"  # Default fallback
        if method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

        yield utils.indented(f"""
def {method.abi.client_method_name}(
    self,
    args: {args_type},
    *,
    account_references: Optional[list[str]] = None,
    app_references: Optional[list[int]] = None,
    asset_references: Optional[list[int]] = None,
    box_references: Optional[list[Union[BoxReference, BoxIdentifier]]] = None,
    extra_fee: Optional[AlgoAmount] = None,
    first_valid_round: Optional[int] = None,
    lease: Optional[bytes] = None,
    max_fee: Optional[AlgoAmount] = None,
    note: Optional[bytes] = None,
    rekey_to: Optional[str] = None,
    sender: Optional[str] = None,
    signer: Optional[TransactionSigner] = None,
    static_fee: Optional[AlgoAmount] = None,
    validity_window: Optional[int] = None,
    last_valid_round: Optional[int] = None,
) -> "{context.contract_name}Composer":
    if isinstance(args, tuple):
        method_args = args
    else:
        method_args = tuple(args.values())

    self._composer.add_app_call_method_call(
        self.client.params.{method.abi.client_method_name}(
            args=method_args, # type: ignore
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

    yield Part.Gap1

    # Add clear state method
    yield utils.indented(f"""
def clear_state(
    self,
    *,
    account_references: Optional[list[str]] = None,
    app_references: Optional[list[int]] = None,
    asset_references: Optional[list[int]] = None,
    box_references: Optional[list[Union[BoxReference, BoxIdentifier]]] = None,
    extra_fee: Optional[AlgoAmount] = None,
    first_valid_round: Optional[int] = None,
    lease: Optional[bytes] = None,
    max_fee: Optional[AlgoAmount] = None,
    note: Optional[bytes] = None,
    rekey_to: Optional[str] = None,
    sender: Optional[str] = None,
    signer: Optional[TransactionSigner] = None,
    static_fee: Optional[AlgoAmount] = None,
    validity_window: Optional[int] = None,
    last_valid_round: Optional[int] = None,
) -> "{context.contract_name}Composer":
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
) -> "{context.contract_name}Composer":
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
