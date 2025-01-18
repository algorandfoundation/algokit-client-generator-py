# /generators/typed_client.py

from collections.abc import Generator, Iterator
from enum import Enum

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ContractMethod


class PropertyType(Enum):
    PARAMS = "params"
    CREATE_TRANSACTION = "create_transaction"
    SEND = "send"


OPERATION_TO_PARAMS_CLASS = {
    "update": "AppClientBareCallWithCompilationAndSendParams",
    "delete": "AppClientBareCallWithSendParams",
    "opt_in": "AppClientBareCallWithSendParams",
    "close_out": "AppClientBareCallWithSendParams",
}

CLEAR_STATE_PROPERTY_TO_RETURN_CLASS = {
    PropertyType.SEND: "SendAppTransactionResult[ABIReturn]",
    PropertyType.CREATE_TRANSACTION: "Transaction",
    PropertyType.PARAMS: "AppCallParams",
}

OPERATION_TO_RETURN_PARAMS_TYPE = {
    "update": "AppUpdateParams",
    "delete": "AppCallParams",
    "opt_in": "AppCallParams",
    "close_out": "AppCallParams",
}


def _generate_args_parser(*, include_args: bool = False) -> str:
    return f"""
    method_args = None
    {'''
    if isinstance(args, tuple):
        method_args = list(args)
    elif isinstance(args, dict):
        method_args = list(args.values())''' if include_args else ''}
    """


def _generate_common_method_params(
    method: ContractMethod,
    property_type: PropertyType,
    operation: str | None = None,
) -> str:
    """Generate the common method parameters shared across different generator methods"""
    if not method.abi:  # Add early return if no ABI
        return ""

    args_type = None
    if method.abi.args:
        # Make tuple args optional if they have defaults
        tuple_args = []
        for arg in method.abi.args:
            arg_type = arg.python_type
            if arg.has_default:
                arg_type = f"{arg_type} | None"
            tuple_args.append(arg_type)

        tuple_type = f"Tuple[{', '.join(tuple_args)}]"
        args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"
        # Make entire args parameter optional if all args have defaults
        if all(arg.has_default for arg in method.abi.args):
            args_type = f"{args_type} | None = None"

    def algokit_extra_args(operation: str | None = None) -> str:
        if operation == "update":
            return "updatable: bool | None, deletable: bool | None, deploy_time_params: TealTemplateParams | None"
        return ""

    # Remove the extra_params parameter since we handle return type differently
    params = f"""
def {method.abi.client_method_name}(
    self,
    {f'args: {args_type},\n    *,' if args_type else '    *,'}
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
    {algokit_extra_args(operation)}
)"""

    # Add return type annotation if needed
    return_type = method.abi.python_type
    if property_type == PropertyType.SEND:
        return_type = f"SendAppTransactionResult[{return_type}]"
    elif property_type == PropertyType.CREATE_TRANSACTION:
        return_type = "BuiltTransactions"
    elif property_type == PropertyType.PARAMS:
        return_type = "AppCallMethodCallParams" if method.abi else "AppCallParams"

    params += f" -> {return_type}:"

    return params


def _generate_method_body(
    context: GeneratorContext,
    method: ContractMethod,
    property_type: PropertyType,
    operation: str = "call",
) -> str:
    """Generate the common method body shared across different generator methods"""
    body = _generate_args_parser(include_args=bool(method.abi and method.abi.args))
    method_sig = method.abi.method.get_signature() if method.abi else ""

    def algokit_param_type(operation: str) -> str:
        return (
            "AppClientMethodCallWithCompilationAndSendParams"
            if operation == "update"
            else "AppClientMethodCallWithSendParams"
        )

    def alogkit_return_type(operation: str) -> str:
        return "SendAppUpdateTransactionResult" if operation == "update" else "SendAppTransactionResult"

    def algokit_extra_args(operation: str) -> str:
        if operation == "update":
            return "updatable=updatable, deletable=deletable, deploy_time_params=deploy_time_params"
        return ""

    call_params = f"""{algokit_param_type(operation)}(
            method="{method_sig}",
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
            {algokit_extra_args(operation)}
        )"""

    if property_type == PropertyType.PARAMS:
        return f"{body}\n    return self.app_client.params.{operation}({call_params})"
    elif property_type == PropertyType.CREATE_TRANSACTION:
        return f"{body}\n    return self.app_client.create_transaction.{operation}({call_params})"
    else:
        response_code = f"""
    response = self.app_client.send.{operation}({call_params})
    return {alogkit_return_type(operation)}(**asdict(replace(response, abi_return=response.abi_return.value))) # type: ignore[arg-type]
"""
        return f"{body}{response_code}"


def generate_operation_class(
    context: GeneratorContext,
    property_type: PropertyType,
    operation: str,
    methods: list[ContractMethod],
) -> Generator[DocumentParts, None, str | None]:
    """Generate a class for a specific operation (update, delete, etc)"""
    if not methods:
        return None

    # Generate the operation class with a unique name based on property_type
    class_name = f"_{context.contract_name}{utils.to_camel_case(operation).capitalize()}"
    if property_type == PropertyType.CREATE_TRANSACTION:
        class_name += "Transaction"
    elif property_type == PropertyType.SEND:
        class_name += "Send"

    yield utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.IncIndent

    # Generate bare method if available
    if any(not method.abi for method in methods):
        yield Part.Gap1
        if property_type == PropertyType.PARAMS:
            yield utils.indented(f"""
def bare(self, params: {OPERATION_TO_PARAMS_CLASS[operation]} | None = None) -> {OPERATION_TO_RETURN_PARAMS_TYPE[operation]}:
    return self.app_client.params.bare.{operation}(params)
""")
        elif property_type == PropertyType.CREATE_TRANSACTION:
            yield utils.indented(f"""
def bare(self, params: {OPERATION_TO_PARAMS_CLASS[operation]} | None = None) -> Transaction:
    return self.app_client.create_transaction.bare.{operation}(params)
""")
        else:  # SEND
            yield utils.indented(f"""
def bare(self, params: {OPERATION_TO_PARAMS_CLASS[operation]} | None = None) -> SendAppTransactionResult:
    return self.app_client.send.bare.{operation}(params)
""")

    # Generate ABI methods
    for method in methods:
        if not method.abi:
            continue

        yield Part.Gap1
        method_params = _generate_common_method_params(
            method,
            property_type,
            operation=operation,
        )
        method_body = _generate_method_body(
            context,
            method,
            property_type,
            operation=operation,
        )
        yield utils.indented(f"{method_params}\n{method_body}")

    yield Part.DecIndent
    return class_name


def _generate_class_methods(  # noqa: C901
    context: GeneratorContext,
    class_name: str,
    property_type: PropertyType,
) -> Iterator[DocumentParts]:
    """Generate methods for a given class type"""

    # Generate operation classes first
    operations = {
        "update": [
            m for m in context.methods.all_methods if m.call_config == "call" and "update_application" in m.on_complete
        ],
        "delete": [
            m for m in context.methods.all_methods if m.call_config == "call" and "delete_application" in m.on_complete
        ],
        "opt_in": [m for m in context.methods.all_methods if m.call_config == "call" and "opt_in" in m.on_complete],
        "close_out": [
            m for m in context.methods.all_methods if m.call_config == "call" and "close_out" in m.on_complete
        ],
    }

    # Generate all operation classes first
    operation_class_names = {}
    for operation, methods in operations.items():
        if methods:
            class_name_gen = generate_operation_class(context, property_type, operation, methods)
            for part in class_name_gen:
                if isinstance(part, str):
                    operation_class_names[operation] = part
                yield part
            yield Part.Gap2

    # Then generate the main class with properties
    yield utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.IncIndent

    # Generate properties for each operation
    postfix = (
        "Transaction"
        if property_type == PropertyType.CREATE_TRANSACTION
        else "Send"
        if property_type == PropertyType.SEND
        else ""
    )

    first = True
    for operation, methods in operations.items():
        if not methods:
            continue

        if not first:
            yield Part.Gap1

        first = False

        default_class_name = f"_{context.contract_name}{utils.to_camel_case(operation).capitalize()}{postfix}"
        operation_class = operation_class_names.get(operation, default_class_name)

        yield utils.indented(f"""
@property
def {operation}(self) -> "{operation_class}":
    return {operation_class}(self.app_client)
""")

    # Generate method for each ABI method
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi or "no_op" not in method.on_complete:
            continue

        if not first:
            yield Part.Gap1
        first = False

        method_params = _generate_common_method_params(
            method,
            property_type=property_type,
        )

        method_body = _generate_method_body(
            context,
            method,
            property_type,
        )

        yield utils.indented(f"{method_params}\n{method_body}")

    # Add clear_state method
    yield Part.Gap1
    yield utils.indented(f"""
def clear_state(self, params: AppClientBareCallWithSendParams | None = None) -> {CLEAR_STATE_PROPERTY_TO_RETURN_CLASS[property_type]}:
    return self.app_client.{property_type.value}.bare.clear_state(params)
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
            # Use None as default for optional args
            python_type = f"{arg.python_type} | None" if arg.has_default else arg.python_type
            yield f"{arg.name}: {python_type}"

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


def _generate_state_typeddict(state_type: str, keys: dict, class_name: str) -> Iterator[DocumentParts]:
    """Generate a TypedDict for a specific state type"""
    if not keys:
        return

    yield utils.indented(f"""
class {class_name}(TypedDict):
    \"\"\"Shape of {state_type} state key values\"\"\"
""")
    yield Part.IncIndent
    for key_name, key_info in keys.items():
        python_type = utils.map_abi_type_to_python(key_info.value_type)
        yield f"{key_name}: {python_type}"
    yield Part.DecIndent


def _generate_state_class(
    state_type: str,
    class_name: str,
    keys: dict,
    maps: dict,
    value_type_name: str | None = None,
    extra_params: str = "",
) -> Iterator[DocumentParts]:
    """Generate a state access class with typed methods"""
    yield utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: AppClient{extra_params}):
        self.app_client = app_client
        {'self.address = address' if extra_params else ''}

    def get_all(self) -> {value_type_name or 'dict[str, Any]'}:
        \"\"\"Get all current keyed values from {state_type} state\"\"\"
        result = self.app_client.state.{state_type}{'(self.address)' if extra_params else ''}.get_all()
        return {'cast(' + value_type_name + ', result)' if value_type_name else 'result'}
""")

    # Generate methods for individual keys
    if keys:
        for key_name, key_info in keys.items():
            python_type = utils.map_abi_type_to_python(key_info.value_type)
            yield Part.Gap1
            yield Part.IncIndent
            yield utils.indented(f"""
    def {utils.get_method_name(key_name)}(self) -> {python_type}:
        \"\"\"Get the current value of the {key_name} key in {state_type} state\"\"\"
        return cast({python_type}, self.app_client.state.{state_type}{'(self.address)' if extra_params else ''}.get_value("{key_name}"))
""")
            yield Part.DecIndent

    # Generate methods for maps
    if maps:
        for map_name, map_info in maps.items():
            key_type = utils.map_abi_type_to_python(map_info.key_type)
            value_type = utils.map_abi_type_to_python(map_info.value_type)
            yield utils.indented(f"""
    @property
    def {utils.get_method_name(map_name)}(self) -> "_MapState[{key_type}, {value_type}]":
        \"\"\"Get values from the {map_name} map in {state_type} state\"\"\"
        return _MapState(
            self.app_client.state.{state_type}{'(self.address)' if extra_params else ''}, 
            "{map_name}"
        )
""")


def generate_state_methods(context: GeneratorContext) -> DocumentParts:
    """Generate state methods for accessing global, local and box state"""
    if not context.app_spec.state:
        return ""

    state_configs = [
        ("global_state", "GlobalStateValue", "_GlobalState", ""),
        ("local_state", "LocalStateValue", "_LocalState", ", address: str"),
        ("box", "BoxStateValue", "_BoxState", ""),
    ]

    # Generate TypedDicts for state shapes
    for state_type, value_type, _, _ in state_configs:
        keys = getattr(context.app_spec.state.keys, state_type if state_type != "box" else "box")
        if keys:
            yield from _generate_state_typeddict(state_type, keys, value_type)
            yield Part.Gap1

    # Generate main state class
    yield utils.indented(f"""
class {context.contract_name}State:
    \"\"\"Methods to access state for the current {context.app_spec.name} app\"\"\"

    def __init__(self, app_client: AppClient):
        self.app_client = app_client
""")
    yield Part.IncIndent

    # Generate state accessors
    for state_type, _, class_name, _ in state_configs:
        keys = getattr(context.app_spec.state.keys, state_type if state_type != "box" else "box")
        maps = getattr(context.app_spec.state.maps, state_type if state_type != "box" else "box")

        if not keys and not maps:
            continue

        yield Part.Gap1
        decorator = "@property" if state_type != "local_state" else ""
        yield utils.indented(f"""
    {decorator}
def {state_type.split('_')[0]}{'_state' if state_type != 'box' else ''}(self{', address: str' if state_type == 'local_state' else ''}) -> "{class_name}":
        \"\"\"Methods to access {state_type} for the current app\"\"\"
        return {class_name}(self.app_client{', address' if state_type == 'local_state' else ''})
""")

    yield Part.DecIndent
    yield Part.Gap1

    # Generate state helper classes
    for state_type, value_type, class_name, extra_params in state_configs:
        keys = getattr(context.app_spec.state.keys, state_type if state_type != "box" else "box")
        maps = getattr(context.app_spec.state.maps, state_type if state_type != "box" else "box")

        if not keys and not maps:
            continue

        yield from _generate_state_class(
            state_type=state_type,
            class_name=class_name,
            keys=keys,
            maps=maps,
            value_type_name=value_type if keys else None,
            extra_params=extra_params,
        )
        yield Part.Gap1

    # Generate MapState class if needed
    if any(
        bool(getattr(context.app_spec.state.maps, t if t != "box" else "box"))
        for t in ["global_state", "local_state", "box"]
    ):
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

    # Generate structs
    yield Part.Gap2
    yield generate_structs(context)

    # Generate supporting classes
    yield Part.Gap2
    yield generate_method_typed_dict(context)
    yield Part.Gap2
    yield from _generate_class_methods(context, f"{context.contract_name}Params", PropertyType.PARAMS)
    yield Part.Gap2
    yield from _generate_class_methods(
        context, f"{context.contract_name}CreateTransactionParams", PropertyType.CREATE_TRANSACTION
    )
    yield Part.Gap2
    yield from _generate_class_methods(context, f"{context.contract_name}Send", PropertyType.SEND)
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
