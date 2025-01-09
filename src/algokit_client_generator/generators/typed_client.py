# /generators/typed_client.py

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part


def generate_params(context: GeneratorContext) -> DocumentParts:
    """Generate params class"""
    yield utils.indented(f"""
class {context.client_name}Params:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.Gap1
    yield Part.IncIndent

    # Generate method for each ABI method
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi:
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
) -> AppCallMethodCallParams:
    if isinstance(args, tuple):
        method_args = list(args)
    else:
        method_args = list(args.values())
    arc56_method = self.app_client.app_spec.get_arc56_method("{method.abi.method.get_signature()}").to_abi_method()

    return AppCallMethodCallParams(
        method=arc56_method,
        args=method_args,
        app_id=self.app_client.app_id,
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
""")

    yield Part.Gap1

    # Add clear state method
    yield utils.indented("""
def clear_state(self, params: AppClientBareCallWithSendParams) -> AppCallParams:
    return self.app_client.params.bare.clear_state(params)
""")
    yield Part.DecIndent


def generate_create_transaction_params(context: GeneratorContext) -> DocumentParts:
    """Generate create transaction params class"""
    yield utils.indented(f"""
class {context.client_name}CreateTransactionParams:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.Gap1
    yield Part.IncIndent

    # Generate method for each ABI method
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi:
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
) -> BuiltTransactions:
    if isinstance(args, tuple):
        method_args = list(args)
    else:
        method_args = list(args.values())

    return self.app_client.create_transaction.call(
        AppClientMethodCallWithSendParams(
            method="{method.abi.method.get_signature()}",
            args=method_args,
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
""")

    yield Part.Gap1

    # Add clear state method
    yield utils.indented("""
def clear_state(self, params: AppClientBareCallWithSendParams) -> Transaction:
    return self.app_client.create_transaction.bare.clear_state(params)
""")
    yield Part.DecIndent


def generate_method_typed_dict(context: GeneratorContext) -> DocumentParts:
    """Generate TypedDict classes for each method's arguments"""
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi or not method.abi.args:
            continue

        if not first:
            yield Part.Gap1
        first = False

        # Convert to camelcase using utility function
        typed_dict_name = f"{utils.to_camel_case(method.abi.client_method_name)}Args"

        yield utils.indented(f"""
class {typed_dict_name}(TypedDict):
    \"\"\"TypedDict for {method.abi.client_method_name} arguments\"\"\"
""")
        yield Part.IncIndent

        for arg in method.abi.args:
            yield f"{arg.name}: {arg.python_type}"

        yield Part.DecIndent


def generate_send(context: GeneratorContext) -> DocumentParts:
    """Generate send class"""
    yield utils.indented(f"""
class {context.client_name}Send:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.Gap1
    yield Part.IncIndent

    # Generate method for each ABI method
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue

        if not first:
            yield Part.Gap1
        first = False

        # Generate the type annotation for args parameter
        args_type = "Any"  # Default fallback
        if method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

        # Generate the method with typed args parameter
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
) -> SendAppTransactionResult:
    if isinstance(args, tuple):
        method_args = list(args)
    else:
        method_args = list(args.values())

    return self.app_client.send.call(
        AppClientMethodCallWithSendParams(
            method="{method.abi.method.get_signature()}",
            args=method_args,
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
""")

    yield Part.Gap1

    # Add clear state method
    yield utils.indented("""
def clear_state(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult:
    return self.app_client.send.bare.clear_state(params)
""")
    yield Part.DecIndent


## Main app client


def generate_class_definition(context: GeneratorContext) -> DocumentParts:
    """Generate the class definition and docstring"""
    yield utils.indented(f"""
class {context.client_name}:
    \"\"\"Client for interacting with {context.app_spec.name} smart contract\"\"\"
""")


def generate_constructor_overloads(context: GeneratorContext) -> DocumentParts:
    """Generate constructor overloads"""
    yield utils.indented("""
@overload
def __init__(self, app_client: AppClient) -> None: ...

@overload
def __init__(
    self,
    *,
    algorand: AlgorandClientProtocol,
    app_id: int,
    app_name: str | None = None,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> None: ...
""")


def generate_constructor(context: GeneratorContext) -> DocumentParts:
    """Generate the actual constructor implementation"""
    yield utils.indented(f"""
def __init__(
    self,
    app_client: AppClient | None = None,
    *,
    algorand: AlgorandClientProtocol | None = None,
    app_id: int | None = None,
    app_name: str | None = None,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> None:
    if app_client:
        self.app_client = app_client
    elif algorand and app_id:
        self.app_client = AppClient(
            AppClientParams(
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

    self.params = {context.client_name}Params(self.app_client)
    self.create_transaction = {context.client_name}CreateTransactionParams(self.app_client)
    self.send = {context.client_name}Send(self.app_client)
""")


def generate_static_methods(context: GeneratorContext) -> DocumentParts:
    """Generate static factory methods"""
    yield utils.indented(f"""
@staticmethod
def from_creator_and_name(
    creator_address: str,
    app_name: str,
    algorand: AlgorandClientProtocol,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
    ignore_cache: bool | None = None,
    app_lookup_cache: AppLookup | None = None,
) -> \"{context.client_name}\":
    return {context.client_name}(
        AppClient.from_creator_and_name(
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
    algorand: AlgorandClientProtocol,
    app_name: str | None = None,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> \"{context.client_name}\":
    return {context.client_name}(
        AppClient.from_network(
            app_spec=APP_SPEC,
            algorand=algorand,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            approval_source_map=approval_source_map,
            clear_source_map=clear_source_map,
        )
    )
""")


def generate_properties(context: GeneratorContext) -> DocumentParts:
    """Generate property accessors"""
    yield utils.indented("""
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
def app_spec(self) -> Arc56Contract:
    return self.app_client.app_spec

@property
def algorand(self) -> AlgorandClientProtocol:
    return self.app_client.algorand
""")


def generate_clone_method(context: GeneratorContext) -> DocumentParts:
    """Generate clone method"""
    yield utils.indented(f"""
def clone(
    self,
    app_name: str | None = None,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> \"{context.client_name}\":
    return {context.client_name}(
        self.app_client.clone(
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            approval_source_map=approval_source_map,
            clear_source_map=clear_source_map,
        )
    )
""")


def generate_decode_return_value(context: GeneratorContext) -> DocumentParts:
    """Generate decode_return_value method"""
    yield utils.indented("""
def decode_return_value(
    self,
    method: str,
    return_value: ABIReturn | None
) -> ABIValue | ABIStruct | None:
    if return_value is None:
        return None

    arc56_method = self.app_spec.get_arc56_method(method)
    return return_value.get_arc56_value(arc56_method, self.app_spec.structs)
""")


def generate_new_group(context: GeneratorContext) -> DocumentParts:
    """Generate new_group method for creating transaction groups"""
    yield utils.indented(f"""
def new_group(self) -> "{context.client_name}Composer":
    return {context.client_name}Composer(self)
""")


def generate_typed_client(context: GeneratorContext) -> DocumentParts:
    """Generate the complete typed client class"""

    # Generate supporting classes first
    yield Part.Gap2
    yield generate_method_typed_dict(context)
    yield Part.Gap2
    yield generate_params(context)
    yield Part.Gap2
    yield generate_create_transaction_params(context)
    yield Part.Gap2
    yield generate_send(context)
    yield Part.Gap2

    # Generate main client class
    yield generate_class_definition(context)
    yield Part.Gap1
    yield Part.IncIndent
    yield generate_constructor_overloads(context)
    yield Part.Gap1
    yield generate_constructor(context)
    yield Part.Gap1
    yield generate_static_methods(context)
    yield Part.Gap1
    yield generate_properties(context)
    yield Part.Gap1
    yield generate_clone_method(context)
    yield Part.Gap1
    yield generate_new_group(context)
    yield Part.Gap1
    yield generate_decode_return_value(context)
    yield Part.DecIndent
