from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part


def generate_composer(context: GeneratorContext) -> DocumentParts:
    """Generate the composer class for creating transaction groups"""
    yield utils.indented(f"""
class {context.client_name}Composer:
    \"\"\"Composer for creating transaction groups for {context.client_name} contract calls\"\"\"
    
    def __init__(self, client: "{context.client_name}"):
        self.client = client
        self._composer = client.algorand.new_group()
        self._result_mappers: list[Optional[Callable[[Optional[ABIReturn]], Any]]] = []

""")
    yield Part.IncIndent

    # Generate method for each ABI method
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue

        if not first:
            yield Part.Gap1
        first = False

        yield utils.indented(f"""
def {method.abi.client_method_name}(self, params: {context.client_name}CallArgs.{method.abi.client_method_name}) -> "{context.client_name}Composer":
    self._composer.add_app_call_method_call(self.client.params.{method.abi.client_method_name}(**vars(params)))
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
    self, params: AppClientBareCallWithSendParams
) -> "{context.client_name}Composer":
    self._composer.add_app_call(self.client.params.clear_state(params))
    return self

def add_transaction(
    self, txn: Transaction, signer: Optional[TransactionSigner] = None
) -> "{context.client_name}Composer":
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
