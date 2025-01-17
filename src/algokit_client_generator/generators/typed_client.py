# /generators/typed_client.py

from collections.abc import Iterator

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ContractMethod


def _generate_operation_methods(
    *,
    context: GeneratorContext,
    description: str,
    methods: list[ContractMethod],
    verb: str,
    type_name: str,
) -> Iterator[DocumentParts]:
    """Generate operation methods (update, delete, etc)"""
    if not methods:
        return

    # Generate method for each ABI method
    for method in methods:
        if not method.abi:
            continue

        if any(
            m.abi and m.abi.client_method_name == method.abi.client_method_name
            for m in context.methods.all_abi_methods
            if m.call_config != "create"
        ):
            continue

        args_type = None
        if method.abi and method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

            yield utils.indented(f"""
        def {method.abi.client_method_name}(
            self,
            {f'args: {args_type},\n*,' if args_type else '*,'}
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
        ) -> {{
            \"\"\"{description}\"\"\"
            method_args = None
            {'''
            if isinstance(args, tuple):
                method_args = list(args)
            elif isinstance(args, dict):
                method_args = list(args.values())
            else:
                method_args = args
            ''' if args_type else ''}

            return self.app_client.{type_name}.{verb}(
                AppClientMethodCallParams(
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
        }},
    """)


def _generate_op_methods(context: GeneratorContext, type_name: str) -> Iterator[DocumentParts]:
    """Generate all operation methods"""

    # Update methods
    yield from _generate_operation_methods(
        context=context,
        description=f"Updates an existing instance of the {context.app_spec.name} smart contract",
        methods=context.methods.update_application,
        verb="update",
        type_name=type_name,
    )

    # Delete methods
    yield from _generate_operation_methods(
        context=context,
        description=f"Deletes an existing instance of the {context.app_spec.name} smart contract",
        methods=context.methods.delete_application,
        verb="delete",
        type_name=type_name,
    )

    # Opt-in methods
    yield from _generate_operation_methods(
        context=context,
        description=f"Opts the user into an existing instance of the {context.app_spec.name} smart contract",
        methods=context.methods.opt_in,
        verb="opt_in",
        type_name=type_name,
    )

    # Close out methods
    yield from _generate_operation_methods(
        context=context,
        description=f"Makes a close out call to an existing instance of the {context.app_spec.name} smart contract",
        methods=context.methods.close_out,
        verb="close_out",
        type_name=type_name,
    )


def generate_params(context: GeneratorContext) -> DocumentParts:
    """Generate params class"""
    yield utils.indented(f"""
class {context.contract_name}Params:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.Gap1
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
        args_type = None  # Default fallback
        if method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

        yield utils.indented(f"""
def {method.abi.client_method_name}(
    self,
    {f'args: {args_type},\n*,' if args_type else '*,'}
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
    method_args = None
    {'''
    if isinstance(args, tuple):
        method_args = list(args)
    elif isinstance(args, dict):
        method_args = list(args.values())
    else:
        method_args = args
    ''' if args_type else ''}

    return self.app_client.params.call(AppClientMethodCallParams(
        method="{method.abi.method.get_signature()}",
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
    ))
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
class {context.contract_name}CreateTransactionParams:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.Gap1
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
        args_type = None  # Default fallback
        if method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

        yield utils.indented(f"""
def {method.abi.client_method_name}(
    self,
    {f'args: {args_type},\n*,' if args_type else '*,'}
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
    method_args = None
    {'''
    if isinstance(args, tuple):
        method_args = list(args)
    elif isinstance(args, dict):
        method_args = list(args.values())
    else:
        method_args = args
    ''' if args_type else ''}

    return self.app_client.create_transaction.call(
        AppClientMethodCallWithSendParams(
            method="{method.abi.method.get_signature()}",
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
class {context.contract_name}Send:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.Gap1
    yield Part.IncIndent

    # Generate operation methods
    yield from _generate_op_methods(context, "send")

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

        return_type = method.abi.python_type
        # Generate the method with typed args parameter
        yield utils.indented(f"""
def {method.abi.client_method_name}(
    self,
    {f'args: {args_type},\n*,' if args_type else '*,'}
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
) -> SendAppTransactionResult[{return_type}]:
    method_args = None
    {'''
    if isinstance(args, tuple):
        method_args = list(args)
    elif isinstance(args, dict):
        method_args = list(args.values())
    else:
        method_args = args
    ''' if args_type else ''}

    response = self.app_client.send.call(
        AppClientMethodCallWithSendParams(
            method="{method.abi.method.get_signature()}",
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

    return SendAppTransactionResult[{return_type}](**asdict(replace(response, abi_return=response.abi_return.value))) # type: ignore[arg-type]
""")

    yield Part.Gap1

    if context.methods.delete_application:
        yield utils.indented("""
def delete_bare(
    self,
    *,
    sender: str | None = None,
    signer: TransactionSigner | None = None,
    **kwargs
) -> SendAppTransactionResult:
    \"\"\"Delete the application using a bare call\"\"\"
    return self.app_client.send.bare.delete(
        AppClientBareCallWithSendParams(
            sender=sender,
            signer=signer,
            **kwargs
        )
    )
""")

    yield Part.Gap1

    # Generate bare update method if available
    if context.methods.update_application:
        yield utils.indented("""
def update_bare(
    self,
    *,
    sender: str | None = None,
    signer: TransactionSigner | None = None,
    **kwargs
) -> SendAppTransactionResult:
    \"\"\"Update the application using a bare call\"\"\"
    return self.app_client.send.bare.update(
        AppClientBareCallWithCompilationAndSendParams(
            sender=sender,
            signer=signer,
            **kwargs
        )
    )
""")

    yield Part.Gap1

    # Add clear state method
    yield utils.indented("""
def clear_state_bare(self, params: AppClientBareCallWithSendParams) -> SendAppTransactionResult:
    return self.app_client.send.bare.clear_state(params)
""")
    yield Part.DecIndent


## Main app client


def generate_class_definition(context: GeneratorContext) -> DocumentParts:
    """Generate the class definition and docstring"""
    yield utils.indented(f"""
class {context.contract_name}Client:
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

    self.params = {context.contract_name}Params(self.app_client)
    self.create_transaction = {context.contract_name}CreateTransactionParams(self.app_client)
    self.send = {context.contract_name}Send(self.app_client)
    self.state = {context.contract_name}State(self.app_client)
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
) -> \"{context.contract_name}Client\":
    return {context.contract_name}Client(
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
) -> \"{context.contract_name}Client\":
    return {context.contract_name}Client(
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
) -> \"{context.contract_name}Client\":
    return {context.contract_name}Client(
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
def new_group(self) -> "{context.contract_name}Composer":
    return {context.contract_name}Composer(self)
""")


def generate_structs(context: GeneratorContext) -> DocumentParts:
    """Generate struct classes for ABI structs"""
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue

        # Get all structs from method args and return type
        all_structs = method.abi.structs or []
        if method.abi.result_struct:
            all_structs.append(method.abi.result_struct)

        for struct in all_structs:
            if not first:
                yield Part.Gap1
            first = False

            yield utils.indented(f"""
@dataclass
class {struct.struct_class_name}:
    \"\"\"Struct for {struct.abi_name}\"\"\"
""")
            yield Part.IncIndent

            for field in struct.fields:
                yield f"{field.name}: {field.python_type}"

            yield Part.DecIndent


def generate_state_methods(context: GeneratorContext) -> DocumentParts:
    """Generate state methods for accessing global, local and box state"""

    # Skip if no state defined
    if not context.app_spec.state:
        return ""

    # Generate state class
    yield utils.indented(f"""
class {context.contract_name}State:
    \"\"\"Methods to access state for the current {context.app_spec.name} app\"\"\"

    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.Gap1
    yield Part.IncIndent

    # Generate global state methods if any global state keys/maps defined
    if context.app_spec.state.keys.global_state or context.app_spec.state.maps.global_state:
        yield utils.indented("""
@property
def global_state(self) -> "_GlobalState":
    \"\"\"Methods to access global state for the current app\"\"\"
    return _GlobalState(self.app_client)
""")

    # Generate local state methods if any local state keys/maps defined
    if context.app_spec.state.keys.local_state or context.app_spec.state.maps.local_state:
        yield utils.indented("""
def local_state(self, address: str) -> "_LocalState":
    \"\"\"Methods to access local state for the current app\"\"\"
    return _LocalState(self.app_client, address)
""")

    # Generate box state methods if any box state keys/maps defined
    if context.app_spec.state.keys.box or context.app_spec.state.maps.box:
        yield utils.indented("""
@property
def box(self) -> "_BoxState":
    \"\"\"Methods to access box state for the current app\"\"\"
    return _BoxState(self.app_client)
""")

    yield Part.DecIndent

    # Generate helper classes for each state type
    for state_type in ["global_state", "local_state", "box"]:
        keys = getattr(context.app_spec.state.keys, f"{state_type}" if state_type != "box" else state_type)
        maps = getattr(context.app_spec.state.maps, f"{state_type}" if state_type != "box" else state_type)

        if not keys and not maps:
            continue

        class_title = state_type if state_type != "box" else "box_state"
        class_name = f"_{class_title.replace('_', ' ').title().replace(' ', '')}"

        yield Part.Gap1
        yield utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: AppClient{', address: str' if state_type == 'local_state' else ''}):
        self.app_client = app_client
        {'self.address = address' if state_type == 'local_state' else ''}

    def get_all(self) -> dict[str, Any]:
        \"\"\"Get all current keyed values from {state_type} state\"\"\"
        result = self.app_client.state.{state_type}{'(self.address)' if state_type == 'local_state' else ''}.get_all()
        return result
""")

        # Generate methods for individual keys
        for key_name, key_info in keys.items():
            python_type = utils.map_abi_type_to_python(key_info.value_type)
            yield Part.Gap1
            yield Part.IncIndent
            yield utils.indented(f"""
    def {utils.get_method_name(key_name)}(self) -> {python_type}:
    \"\"\"Get the current value of the {key_name} key in {state_type} state\"\"\"
    return cast({python_type}, self.app_client.state.{state_type}{'(self.address)' if state_type == 'local_state' else ''}.get_value("{key_name}"))
""")
            yield Part.DecIndent

        # Generate methods for maps
        if maps:
            for map_name, map_info in maps.items():
                yield utils.indented(f"""
    @property
    def {utils.get_method_name(map_name)}(self) -> "_MapState[{utils.map_abi_type_to_python(map_info.key_type)}, {utils.map_abi_type_to_python(map_info.value_type)}]":
        \"\"\"Get values from the {map_name} map in {state_type} state\"\"\"
        return _MapState(
            self.app_client.state.{state_type}{'(self.address)' if state_type == 'local_state' else ''}, 
            "{map_name}"
        )
""")

    # Only generate _MapState if there are any maps
    has_maps = any(
        bool(getattr(context.app_spec.state.maps, f"{state_type}" if state_type != "box" else state_type))
        for state_type in ["global_state", "local_state", "box"]
    )

    if has_maps:
        yield utils.indented("""
class _MapState(Generic[KeyType, ValueType]):
    \"\"\"Generic class for accessing state maps with strongly typed keys and values\"\"\"

    def __init__(self, state_accessor: _AppClientStateMethodsProtocol, map_name: str):
        self._state_accessor = state_accessor
        self._map_name = map_name

    def get_map(self) -> dict[KeyType, ValueType]:
        \"\"\"Get all current values in the map\"\"\"
        return cast(dict[KeyType, ValueType], self._state_accessor.get_map(self._map_name))

    def get_value(self, key: KeyType) -> ValueType | None:
        \"\"\"Get a value from the map by key\"\"\"
        return cast(ValueType | None, self._state_accessor.get_map_value(self._map_name, key))
""")


def generate_typed_client(context: GeneratorContext) -> DocumentParts:
    """Generate the complete typed client class"""

    # Generate structs first
    yield Part.Gap2
    yield generate_structs(context)

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
    yield generate_state_methods(context)
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
