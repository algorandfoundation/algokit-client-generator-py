# /generators/typed_client.py
from enum import Enum

from algokit_abi import abi, arc56

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.generators.helpers import get_abi_method_operations
from algokit_client_generator.spec import ContractMethod

APPL_TYPE_TXNS = [arc56.TransactionType.APPL, arc56.TransactionType.ANY]


class PropertyType(Enum):
    PARAMS = "params"
    CREATE_TRANSACTION = "create_transaction"
    SEND = "send"


OPERATION_TO_PARAMS_CLASS = {
    "update": "algokit_utils.AppClientBareCallWithCompilationAndSendParams",
    "delete": "algokit_utils.AppClientBareCallWithSendParams",
    "opt_in": "algokit_utils.AppClientBareCallWithSendParams",
    "close_out": "algokit_utils.AppClientBareCallWithSendParams",
}

CLEAR_STATE_PROPERTY_TO_RETURN_CLASS = {
    PropertyType.SEND: "algokit_utils.SendAppTransactionResult[algokit_utils.ABIReturn]",
    PropertyType.CREATE_TRANSACTION: "Transaction",
    PropertyType.PARAMS: "algokit_utils.AppCallParams",
}

OPERATION_TO_RETURN_PARAMS_TYPE = {
    "update": "algokit_utils.AppUpdateParams",
    "delete": "algokit_utils.AppCallParams",
    "opt_in": "algokit_utils.AppCallParams",
    "close_out": "algokit_utils.AppCallParams",
}

OPERATION_TO_METHOD_CALL_PARAMS_TYPE = {
    "update": "algokit_utils.AppUpdateMethodCallParams",
    "delete": "algokit_utils.AppDeleteMethodCallParams",
    "opt_in": "algokit_utils.AppCallMethodCallParams",
    "close_out": "algokit_utils.AppCallMethodCallParams",
    "call": "algokit_utils.AppCallMethodCallParams",
}


def _generate_common_method_params(  # noqa: C901
    context: GeneratorContext,
    method: ContractMethod,
    property_type: PropertyType,
    operation: str | None = None,
) -> tuple[str, bool]:
    """Generate the common method parameters shared across different generator methods"""
    if not method.abi:  # Add early return if no ABI
        return "", False

    args_type = None
    if method.abi.args:
        # Track if we've seen an appl arg to make previous txn args optional
        has_appl_to_right = False

        # Scan args from right to left
        args_meta = []
        for arg in reversed(method.abi.args):
            # Make arg optional if it has default or is a transaction with appl to right
            is_txn_type = isinstance(arg.abi_type, arc56.TransactionType)
            is_appl_type = is_txn_type and arg.abi_type in APPL_TYPE_TXNS
            is_optional = arg.has_default or (has_appl_to_right and is_txn_type)

            arg_type = arg.python_type
            if is_optional:
                arg_type = f"{arg_type} | None"
            args_meta.append(arg_type)

            if not has_appl_to_right and is_appl_type:
                has_appl_to_right = True

        # Reverse back to original order
        args_meta.reverse()

        tuple_type = f"tuple[{', '.join(args_meta)}]"
        args_type = f"{tuple_type} | {context.sanitizer.make_safe_type_identifier(method.abi.client_method_name)}Args"

        # Make entire args parameter optional if all args have defaults
        if all(arg.has_default for arg in method.abi.args):
            args_type = f"{args_type} | None = None"

    # Build parameters list
    params = []
    if args_type:
        params.append(f"args: {args_type}")
    params.append("params: algokit_utils.CommonAppCallParams | None = None")

    if property_type == PropertyType.SEND:
        params.append("send_params: algokit_utils.SendParams | None = None")
    if operation == "update":
        params.append("compilation_params: algokit_utils.AppClientCompilationParams | None = None")

    # Join parameters with proper indentation and line breaks
    params_str = ",\n    ".join(params)
    params_def = f"""
def {method.abi.client_method_name}(
    self,
    {params_str}
)"""

    # Add return type annotation if needed
    return_type = method.abi.python_type
    if property_type == PropertyType.SEND:
        return_type = f"algokit_utils.SendAppTransactionResult[{return_type}]"
    elif property_type == PropertyType.CREATE_TRANSACTION:
        return_type = "algokit_utils.BuiltTransactions"
    elif property_type == PropertyType.PARAMS:
        return_type = (
            OPERATION_TO_METHOD_CALL_PARAMS_TYPE[operation or "call"] if method.abi else "algokit_utils.AppCallParams"
        )

    params_def += f" -> {return_type}:"

    return params_def, args_type is not None


def _generate_method_body(
    context: GeneratorContext,
    method: ContractMethod,
    property_type: PropertyType,
    operation: str = "call",
    *,
    include_args: bool = False,
) -> str:
    """Generate the common method body shared across different generator methods"""
    body = "    params = params or algokit_utils.CommonAppCallParams()"
    if operation == "update":
        body += "\n    compilation_params = compilation_params or algokit_utils.AppClientCompilationParams()"
    method_sig = method.abi.method.get_signature() if method.abi else ""

    def alogkit_return_type(operation: str, method: ContractMethod) -> str:
        return_type = method.abi.python_type if method.abi else ""
        if operation == "update":
            return_type = f"algokit_utils.SendAppUpdateTransactionResult[{return_type}]"
        else:
            return_type = f"algokit_utils.SendAppTransactionResult[{return_type}]"
        return return_type

    call_params = f"""_extend(
        algokit_utils.AppClientMethodCallParams,
        params,
        method="{method_sig}",{
        '''
        args=_unpack_args(args), '''
        if include_args
        else ""
    }
    )"""
    send_params = ", send_params=send_params" if property_type == PropertyType.SEND else ""
    compilation_params = ", compilation_params=compilation_params" if operation == "update" else ""

    if property_type == PropertyType.PARAMS:
        return f"{body}\n    return self.app_client.params.{operation}({call_params})"
    elif property_type == PropertyType.CREATE_TRANSACTION:
        return f"{body}\n    return self.app_client.create_transaction.{operation}({call_params})"
    else:
        response_code = f"""
    response = self.app_client.send.{operation}({call_params}{send_params}{compilation_params})
    return typing.cast({alogkit_return_type(operation, method)}, response)
"""
        return f"{body}{response_code}"


def generate_operation_class(
    context: GeneratorContext,
    class_name: str,
    property_type: PropertyType,
    operation: str,
    methods: list[ContractMethod],
) -> DocumentParts:
    """Generate a class for a specific operation (update, delete, etc)"""
    if not methods:
        return
    yield from utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client
""")
    yield Part.IncIndent

    # Generate bare method if available
    if any(not method.abi for method in methods):
        yield Part.Gap1
        if property_type == PropertyType.PARAMS:
            yield from utils.indented(f"""
def bare(
    self, params: algokit_utils.AppClientBareCallParams | None = None
) -> {OPERATION_TO_RETURN_PARAMS_TYPE[operation]}:
    return self.app_client.params.bare.{operation}(params)
""")
        elif property_type == PropertyType.CREATE_TRANSACTION:
            yield from utils.indented(f"""
def bare(self, params: algokit_utils.AppClientBareCallParams | None = None) -> Transaction:
    return self.app_client.create_transaction.bare.{operation}(params)
""")
        else:  # SEND
            yield from utils.indented(f"""
def bare(
    self,
    params: algokit_utils.AppClientBareCallParams | None = None,
    send_params: algokit_utils.SendParams | None = None,
    {"compilation_params: algokit_utils.AppClientCompilationParams | None = None" if operation == "update" else ""}
) -> algokit_utils.SendAppTransactionResult:
    return self.app_client.send.bare.{operation}(
        params=params,
        send_params=send_params,
        {"compilation_params=compilation_params" if operation == "update" else ""}
    )
""")

    # Generate ABI methods
    for method in methods:
        if not method.abi:
            continue

        yield Part.Gap1
        method_params, include_args = _generate_common_method_params(
            context,
            method,
            property_type,
            operation=operation,
        )
        method_body = _generate_method_body(
            context,
            method,
            property_type,
            operation=operation,
            include_args=include_args,
        )
        yield from utils.indented(f"{method_params}\n{method_body}")

    yield Part.DecIndent


def _generate_class_methods(
    context: GeneratorContext,
    class_name: str,
    property_type: PropertyType,
) -> DocumentParts:
    """Generate methods for a given class type"""

    operations = get_abi_method_operations(context)

    # Generate all operation classes first
    operation_class_names = {}
    for operation, methods in operations.items():
        if methods:
            # Generate the operation class with a unique name based on property_type
            operation_class_name = f"_{context.contract_name}{context.sanitizer.make_safe_type_identifier(operation)}"
            if property_type == PropertyType.CREATE_TRANSACTION:
                operation_class_name += "Transaction"
            elif property_type == PropertyType.SEND:
                operation_class_name += "Send"
            operation_class_names[operation] = operation_class_name
            yield from generate_operation_class(context, operation_class_name, property_type, operation, methods)
            yield Part.Gap2

    # Then generate the main class with properties
    yield from utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: algokit_utils.AppClient):
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

    for operation, methods in operations.items():
        if not methods:
            continue

        yield Part.Gap1

        default_class_name = (
            f"_{context.contract_name}{context.sanitizer.make_safe_type_identifier(operation)}{postfix}"
        )
        operation_class = operation_class_names.get(operation, default_class_name)

        yield from utils.indented(f"""
@property
def {operation}(self) -> "{operation_class}":
    return {operation_class}(self.app_client)
""")

    # Generate method for each ABI method
    for method in context.methods.all_abi_methods:
        if not method.abi or "no_op" not in method.on_complete:
            continue

        if context.mode == "minimal" and (
            method.call_config == "create" or method.on_complete in (["update_application"], ["delete_application"])
        ):
            continue

        yield Part.Gap1

        method_params, include_args = _generate_common_method_params(
            context,
            method,
            property_type=property_type,
        )

        method_body = _generate_method_body(
            context,
            method,
            property_type,
            include_args=include_args,
        )

        yield from utils.indented(f"{method_params}\n{method_body}")

    # Add clear_state method
    yield Part.Gap1
    yield from utils.indented(f"""
def clear_state(
    self,
    params: algokit_utils.AppClientBareCallParams | None = None,
    {"send_params: algokit_utils.SendParams | None = None" if property_type == PropertyType.SEND else ""}
) -> {CLEAR_STATE_PROPERTY_TO_RETURN_CLASS[property_type]}:
    return self.app_client.{property_type.value}.bare.clear_state(
        params,
        {"send_params=send_params," if property_type == PropertyType.SEND else ""}
    )
""")

    yield Part.DecIndent


def generate_structs_for_args(context: GeneratorContext) -> DocumentParts:
    """Generate dataclasses for each method's arguments"""
    for method in context.methods.all_abi_methods:
        if not method.abi or not method.abi.args:
            continue

        yield Part.Gap1

        # Track appl args from right to left like in TypeScript
        has_appl_to_right = False
        optional_args = set()

        # Scan right to left to determine which args should be optional
        for arg in reversed(method.abi.args):
            is_txn_type = isinstance(arg.abi_type, arc56.TransactionType)
            is_appl_type = is_txn_type and arg.abi_type in APPL_TYPE_TXNS

            if is_txn_type and has_appl_to_right:
                optional_args.add(arg.name)

            if not has_appl_to_right and is_appl_type:
                has_appl_to_right = True

        data_class_name = f"{context.sanitizer.make_safe_type_identifier(method.abi.client_method_name)}Args"

        yield from utils.indented(f"""
@dataclasses.dataclass(frozen=True, kw_only=True)
class {data_class_name}:
    \"\"\"Dataclass for {method.abi.client_method_name} arguments\"\"\"
""")
        yield Part.IncIndent

        for arg in method.abi.args:
            # Make arg optional if it has default or is in optional_args set
            is_optional = arg.has_default or arg.name in optional_args
            python_type = f"{arg.python_type} | None = None" if is_optional else arg.python_type
            yield f"{arg.name}: {python_type}"
        yield Part.Gap1
        yield f"""@property
    def abi_method_signature(self) -> str:
        return "{method.abi.method.get_signature()}"
"""
        yield Part.DecIndent


## Main app client


def generate_class_definition(context: GeneratorContext) -> DocumentParts:
    """Generate the class definition and docstring"""
    yield from utils.indented(f"""
class {context.contract_name}Client:
    \"\"\"Client for interacting with {context.app_spec.name} smart contract\"\"\"
""")


def generate_constructor_overloads(context: GeneratorContext) -> DocumentParts:
    """Generate constructor overloads"""
    yield from utils.indented("""
@typing.overload
def __init__(self, app_client: algokit_utils.AppClient) -> None: ...

@typing.overload
def __init__(
    self,
    *,
    algorand: _AlgoKitAlgorandClient,
    app_id: int,
    app_name: str | None = None,
    default_sender: str | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> None: ...
""")


def generate_constructor(context: GeneratorContext) -> DocumentParts:
    """Generate the actual constructor implementation"""
    yield from utils.indented(f"""
def __init__(
    self,
    app_client: algokit_utils.AppClient | None = None,
    *,
    algorand: _AlgoKitAlgorandClient | None = None,
    app_id: int | None = None,
    app_name: str | None = None,
    default_sender: str | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> None:
    if app_client:
        self.app_client = app_client
    elif algorand and app_id:
        self.app_client = algokit_utils.AppClient(
            algokit_utils.AppClientParams(
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
    yield from utils.indented(f"""
@staticmethod
def from_creator_and_name(
    creator_address: str,
    app_name: str,
    algorand: _AlgoKitAlgorandClient,
    default_sender: str | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
    ignore_cache: bool | None = None,
    app_lookup_cache: algokit_utils.ApplicationLookup | None = None,
) -> \"{context.contract_name}Client\":
    return {context.contract_name}Client(
        algokit_utils.AppClient.from_creator_and_name(
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
    algorand: _AlgoKitAlgorandClient,
    app_name: str | None = None,
    default_sender: str | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> \"{context.contract_name}Client\":
    return {context.contract_name}Client(
        algokit_utils.AppClient.from_network(
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
    yield from utils.indented("""
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
def app_spec(self) -> arc56.Arc56Contract:
    return self.app_client.app_spec

@property
def algorand(self) -> _AlgoKitAlgorandClient:
    return self.app_client.algorand
""")


def generate_clone_method(context: GeneratorContext) -> DocumentParts:
    """Generate clone method"""
    yield from utils.indented(f"""
def clone(
    self,
    app_name: str | None = None,
    default_sender: str | None = None,
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
    """Generate decode_return_value method with proper overloads"""
    # First generate the overloads for each method
    overloads = []
    return_types = set()  # Track all possible return types

    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue

        return_type = method.abi.python_type
        signature = method.abi.method.get_signature()

        # For void methods, return type should be None | None to match implementation
        if return_type == "None":
            overload_return = "None"
            return_types.add("None")
        else:
            overload_return = f"{return_type} | None"
            return_types.add(return_type)

        overloads.append(f"""

    @typing.overload
def decode_return_value(
    self,
    method: typing.Literal["{signature}"],
    return_value: algokit_utils.ABIReturn | None
) -> {overload_return}: ...
""")

    # Create union of all possible return types
    base_union = "algokit_utils.ABIValue | algokit_utils.ABIStruct"
    return_union = f"{base_union}{' | None' if 'None' not in return_types else ''}" + (
        f" | {' | '.join(sorted(return_types))}" if return_types else ""
    )

    if len(overloads) > 0:
        overloads.append(f"""
    @typing.overload
def decode_return_value(
    self,
    method: str,
    return_value: algokit_utils.ABIReturn | None
) -> {base_union} | None: ...
""")

    # Then generate the actual implementation
    implementation = f"""
def decode_return_value(
    self,
    method: str,
    return_value: algokit_utils.ABIReturn | None
) -> {return_union}:
    \"\"\"Decode ABI return value for the given method.\"\"\"
    if return_value is None:
        return None

    return return_value.value
"""

    # Yield all the overloads first
    for overload in overloads:
        yield from utils.indented(overload)

    if len(overloads) > 0:
        yield Part.Gap1

    # Then yield the implementation
    yield from utils.indented(implementation)


def generate_new_group(context: GeneratorContext) -> DocumentParts:
    """Generate new_group method for creating transaction groups"""
    yield from utils.indented(f"""
def new_group(self) -> "{context.contract_name}Composer":
    return {context.contract_name}Composer(self)
""")


def generate_structs(context: GeneratorContext) -> DocumentParts:
    """Generate struct classes for ABI structs"""
    structs_done = set[str]()
    for struct in context.app_spec.structs.values():
        yield from _generate_struct(context, structs_done, struct)


def _generate_struct(context: GeneratorContext, structs_done: set[str], struct: abi.StructType) -> DocumentParts:
    spec_struct_name = struct.struct_name
    if spec_struct_name in structs_done:
        return
    structs_done.add(spec_struct_name)
    # ensure any other referenced structs have been generated before this struct
    for field_type in struct.fields.values():
        if isinstance(field_type, abi.StructType):
            yield from _generate_struct(context, structs_done, field_type)
    yield Part.Gap1
    yield from utils.indented(f"""
@dataclasses.dataclass(frozen=True)
class {context.generated_structs[spec_struct_name]}:
    \"\"\"Struct for {spec_struct_name}\"\"\"
""")
    yield Part.IncIndent
    for field_name, field_type in struct.fields.items():
        yield f"{field_name}: {utils.abi_type_to_python(field_type)}"
    yield Part.DecIndent
    yield Part.Gap1


def _generate_state_typeddict(state_type: str, keys: dict, class_name: str) -> DocumentParts:
    """Generate a TypedDict for a specific state type"""
    if not keys:
        return

    yield from utils.indented(f"""
class {class_name}(typing.TypedDict):
    \"\"\"Shape of {state_type} state key values\"\"\"
""")
    yield Part.IncIndent
    for key_name, key_info in keys.items():
        python_type = utils.map_arc56_type_to_python(key_info.value_type)
        yield f"{key_name}: {python_type}"
    yield Part.DecIndent


def _generate_state_class(  # noqa: PLR0913
    context: GeneratorContext,
    state_type: str,
    class_name: str,
    keys: dict,
    maps: dict,
    value_type_name: str,
    extra_params: str = "",
) -> DocumentParts:
    """Generate a state access class with typed methods"""

    yield from utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: algokit_utils.AppClient{extra_params}):
        self.app_client = app_client
        {"self.address = address" if extra_params else ""}
        # Pre-generated mapping of value types to their struct classes

    def get_all(self) -> {value_type_name}:
        \"\"\"Get all current keyed values from {state_type} state\"\"\"
        result = self.app_client.state.{state_type}{"(self.address)" if extra_params else ""}.get_all()
        return typing.cast({value_type_name}, result)
""")

    # Generate methods for individual keys
    if keys:
        for key_name, key_info in keys.items():
            python_type = utils.map_arc56_type_to_python(key_info.value_type, utils.IOType.OUTPUT)
            yield Part.Gap1
            yield Part.IncIndent
            yield (
                f"""@property
    def {utils.get_method_name(key_name)}(self) -> {python_type}:
        \"\"\"Get the current value of the {key_name} key in {state_type} state\"\"\"
        value = self.app_client.state.{state_type}{"(self.address)" if extra_params else ""}.get_value("{key_name}")
        return typing.cast({python_type}, value)
"""
            )
            yield Part.DecIndent

    # Generate methods for maps
    if maps:
        for map_name, map_info in maps.items():
            key_type = utils.map_arc56_type_to_python(map_info.key_type, utils.IOType.INPUT)
            value_type = utils.map_arc56_type_to_python(map_info.value_type, utils.IOType.OUTPUT)
            yield Part.Gap1
            yield Part.IncIndent
            yield from utils.indented(f"""
@property
def {utils.get_method_name(map_name)}(self) -> "_MapState[{key_type}, {value_type}]":
    \"\"\"Get values from the {map_name} map in {state_type} state\"\"\"
    return _MapState(
        self.app_client.state.{state_type}{"(self.address)" if extra_params else ""},
        "{map_name}",
    )
""")
            yield Part.DecIndent


def generate_state_methods(context: GeneratorContext) -> DocumentParts:
    """Generate state methods for accessing global, local and box state"""
    if not context.app_spec.state:
        return

    state_configs = [
        ("global_state", "GlobalStateValue", "_GlobalState", ""),
        ("local_state", "LocalStateValue", "_LocalState", ", address: str"),
        ("box", "BoxStateValue", "_BoxState", ""),
    ]

    # Generate TypedDicts for state shapes
    for state_type, value_type, _, _ in state_configs:
        keys = getattr(context.app_spec.state.keys, state_type)
        if keys:
            yield from _generate_state_typeddict(state_type, keys, value_type)
            yield Part.Gap1

    # Generate main state class
    yield from utils.indented(f"""
class {context.contract_name}State:
    \"\"\"Methods to access state for the current {context.app_spec.name} app\"\"\"

    def __init__(self, app_client: algokit_utils.AppClient):
        self.app_client = app_client
""")
    yield Part.IncIndent

    # Generate state accessors
    for state_type, _, class_name, _ in state_configs:
        keys = getattr(context.app_spec.state.keys, state_type)
        maps = getattr(context.app_spec.state.maps, state_type)

        if not keys and not maps:
            continue

        yield Part.Gap1
        decorator = "@property" if state_type != "local_state" else ""
        yield from utils.indented(f"""
    {decorator}
def {state_type.split("_")[0]}{"_state" if state_type != "box" else ""}(
    self{", address: str" if state_type == "local_state" else ""}
) -> "{class_name}":
        \"\"\"Methods to access {state_type} for the current app\"\"\"
        return {class_name}(self.app_client{", address" if state_type == "local_state" else ""})
""")

    yield Part.DecIndent
    yield Part.Gap1

    # Generate state helper classes
    for state_type, value_type, class_name, extra_params in state_configs:
        keys = getattr(context.app_spec.state.keys, state_type)
        maps = getattr(context.app_spec.state.maps, state_type)

        if not keys and not maps:
            continue

        yield from _generate_state_class(
            context=context,
            state_type=state_type,
            class_name=class_name,
            keys=keys,
            maps=maps,
            value_type_name=value_type if keys else "dict[str, typing.Any]",
            extra_params=extra_params,
        )
        yield Part.Gap1

    # Generate MapState class if needed
    if any(bool(getattr(context.app_spec.state.maps, t)) for t in ["global_state", "local_state", "box"]):
        yield from utils.indented("""
_KeyType = typing.TypeVar("_KeyType")
_ValueType = typing.TypeVar("_ValueType")

class _AppClientStateMethodsProtocol(typing.Protocol):
    def get_map(self, map_name: str) -> dict[typing.Any, typing.Any]:
        ...
    def get_map_value(self, map_name: str, key: typing.Any) -> typing.Any | None:
        ...

class _MapState(typing.Generic[_KeyType, _ValueType]):
    \"\"\"Generic class for accessing state maps with strongly typed keys and values\"\"\"

    def __init__(self, state_accessor: _AppClientStateMethodsProtocol, map_name: str) -> None:
        self._state_accessor = state_accessor
        self._map_name = map_name

    def get_map(self) -> dict[_KeyType, _ValueType]:
        \"\"\"Get all current values in the map\"\"\"
        result = self._state_accessor.get_map(self._map_name)
        return typing.cast(dict[_KeyType, _ValueType], result or {})

    def get_value(self, key: _KeyType) -> _ValueType | None:
        \"\"\"Get a value from the map by key\"\"\"
        value = self._state_accessor.get_map_value(self._map_name, key)
        return typing.cast(_ValueType | None, value)
""")


def generate_typed_client(context: GeneratorContext) -> DocumentParts:
    """Generate the complete typed client class"""

    # Generate structs
    yield Part.Gap2
    yield from generate_structs(context)

    # Generate supporting classes
    yield Part.Gap2
    yield from generate_structs_for_args(context)
    yield Part.Gap2
    yield from _generate_class_methods(context, f"{context.contract_name}Params", PropertyType.PARAMS)
    yield Part.Gap2
    yield from _generate_class_methods(
        context, f"{context.contract_name}CreateTransactionParams", PropertyType.CREATE_TRANSACTION
    )
    yield Part.Gap2
    yield from _generate_class_methods(context, f"{context.contract_name}Send", PropertyType.SEND)
    yield Part.Gap2
    yield from generate_state_methods(context)
    yield Part.Gap2

    # Generate main client class
    yield from generate_class_definition(context)
    yield Part.Gap1
    yield Part.IncIndent
    yield from generate_constructor_overloads(context)
    yield Part.Gap1
    yield from generate_constructor(context)
    yield Part.Gap1
    yield from generate_static_methods(context)
    yield Part.Gap1
    yield from generate_properties(context)
    yield Part.Gap1
    yield from generate_clone_method(context)
    yield Part.Gap1
    yield from generate_new_group(context)
    yield Part.Gap1
    yield from generate_decode_return_value(context)
    yield Part.DecIndent
