# /generators/typed_client.py

from collections.abc import Generator, Iterator
from enum import Enum

import algosdk

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ABIStruct, ABIStructField, ContractMethod

APPL_TYPE_TXNS = [algosdk.abi.ABITransactionType.APPL, algosdk.abi.ABITransactionType.ANY]


class PropertyType(Enum):
    PARAMS = "params"
    CREATE_TRANSACTION = "create_transaction"
    SEND = "send"


OPERATION_TO_PARAMS_CLASS = {
    "update": "applications.AppClientBareCallWithCompilationAndSendParams",
    "delete": "applications.AppClientBareCallWithSendParams",
    "opt_in": "applications.AppClientBareCallWithSendParams",
    "close_out": "applications.AppClientBareCallWithSendParams",
}

CLEAR_STATE_PROPERTY_TO_RETURN_CLASS = {
    PropertyType.SEND: "transactions.SendAppTransactionResult[applications_abi.ABIReturn]",
    PropertyType.CREATE_TRANSACTION: "Transaction",
    PropertyType.PARAMS: "transactions.AppCallParams",
}

OPERATION_TO_RETURN_PARAMS_TYPE = {
    "update": "transactions.AppUpdateParams",
    "delete": "transactions.AppCallParams",
    "opt_in": "transactions.AppCallParams",
    "close_out": "transactions.AppCallParams",
}

OPERATION_TO_METHOD_CALL_PARAMS_TYPE = {
    "update": "transactions.AppUpdateMethodCallParams",
    "delete": "transactions.AppDeleteMethodCallParams",
    "opt_in": "transactions.AppCallMethodCallParams",
    "close_out": "transactions.AppCallMethodCallParams",
    "call": "transactions.AppCallMethodCallParams",
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
            is_txn_type = algosdk.abi.is_abi_transaction_type(arg.abi_type)
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

    def algokit_extra_args(operation: str | None = None) -> str:
        if operation == "update":
            return (
                "updatable: bool | None, deletable: bool | None, deploy_time_params: models.TealTemplateParams | None"
            )
        return ""

    # Remove the extra_params parameter since we handle return type differently
    params = f"""
def {method.abi.client_method_name}(
    self,
    {f'args: {args_type},    *,' if args_type else '    *,'}
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
    {algokit_extra_args(operation)}
)"""

    # Add return type annotation if needed
    return_type = method.abi.python_type
    if property_type == PropertyType.SEND:
        return_type = f"transactions.SendAppTransactionResult[{return_type}]"
    elif property_type == PropertyType.CREATE_TRANSACTION:
        return_type = "transactions.BuiltTransactions"
    elif property_type == PropertyType.PARAMS:
        return_type = (
            OPERATION_TO_METHOD_CALL_PARAMS_TYPE[operation or "call"] if method.abi else "transactions.AppCallParams"
        )

    params += f" -> {return_type}:"

    return params, args_type is not None


def _generate_method_body(
    context: GeneratorContext,
    method: ContractMethod,
    property_type: PropertyType,
    operation: str = "call",
    *,
    include_args: bool = False,
) -> str:
    """Generate the common method body shared across different generator methods"""
    body = "    method_args = _parse_abi_args(args)" if include_args else ""
    method_sig = method.abi.method.get_signature() if method.abi else ""

    def algokit_param_type(operation: str) -> str:
        return (
            "applications.AppClientMethodCallWithCompilationAndSendParams"
            if operation == "update"
            else "applications.AppClientMethodCallWithSendParams"
        )

    def alogkit_return_type(operation: str, method: ContractMethod) -> str:
        return_type = f"{method.abi.python_type}" if method.abi else ""
        if operation == "update":
            return_type = f"transactions.SendAppUpdateTransactionResult[{return_type}]"
        else:
            return_type = f"transactions.SendAppTransactionResult[{return_type}]"
        return return_type

    def parse_struct_if_needed(method: ContractMethod) -> str:
        if method.abi and method.abi.result_struct:
            return (
                f"dataclasses.replace(response, "
                f"abi_return={method.abi.result_struct.struct_class_name}(**typing.cast(dict, response.abi_return))) # type: ignore"
            )
        return "response"

    def algokit_extra_args(operation: str) -> str:
        if operation == "update":
            return "updatable=updatable, deletable=deletable, deploy_time_params=deploy_time_params"
        return ""

    call_params = f"""{algokit_param_type(operation)}(
            method="{method_sig}",{'''
            args=method_args, ''' if include_args else ''}
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
            {algokit_extra_args(operation)}
        )"""

    if property_type == PropertyType.PARAMS:
        return f"{body}\n    return self.app_client.params.{operation}({call_params})"
    elif property_type == PropertyType.CREATE_TRANSACTION:
        return f"{body}\n    return self.app_client.create_transaction.{operation}({call_params})"
    else:
        response_code = f"""
    response = self.app_client.send.{operation}({call_params})
    parsed_response = {parse_struct_if_needed(method)}
    return typing.cast({alogkit_return_type(operation, method)}, parsed_response)
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
    class_name = f"_{context.contract_name}{context.sanitizer.make_safe_type_identifier(operation)}"
    if property_type == PropertyType.CREATE_TRANSACTION:
        class_name += "Transaction"
    elif property_type == PropertyType.SEND:
        class_name += "Send"

    yield utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: applications.AppClient):
        self.app_client = app_client
""")
    yield Part.IncIndent

    # Generate bare method if available
    if any(not method.abi for method in methods):
        yield Part.Gap1
        if property_type == PropertyType.PARAMS:
            yield utils.indented(f"""
def bare(
    self, params: {OPERATION_TO_PARAMS_CLASS[operation]} | None = None
) -> {OPERATION_TO_RETURN_PARAMS_TYPE[operation]}:
    return self.app_client.params.bare.{operation}(params)
""")
        elif property_type == PropertyType.CREATE_TRANSACTION:
            yield utils.indented(f"""
def bare(self, params: {OPERATION_TO_PARAMS_CLASS[operation]} | None = None) -> Transaction:
    return self.app_client.create_transaction.bare.{operation}(params)
""")
        else:  # SEND
            yield utils.indented(f"""
def bare(self, params: {OPERATION_TO_PARAMS_CLASS[operation]} | None = None) -> transactions.SendAppTransactionResult:
    return self.app_client.send.bare.{operation}(params)
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
    def __init__(self, app_client: applications.AppClient):
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

        default_class_name = (
            f"_{context.contract_name}{context.sanitizer.make_safe_type_identifier(operation)}{postfix}"
        )
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

        yield utils.indented(f"{method_params}\n{method_body}")

    # Add clear_state method
    yield Part.Gap1
    yield utils.indented(f"""
def clear_state(
    self,
    params: applications.AppClientBareCallWithSendParams | None = None
) -> {CLEAR_STATE_PROPERTY_TO_RETURN_CLASS[property_type]}:
    return self.app_client.{property_type.value}.bare.clear_state(params)
""")

    yield Part.DecIndent


def generate_structs_for_args(context: GeneratorContext) -> DocumentParts:
    """Generate dataclasses for each method's arguments"""
    first = True
    for method in context.methods.all_abi_methods:
        if not method.abi or not method.abi.args:
            continue

        if not first:
            yield Part.Gap1
        first = False

        # Track appl args from right to left like in TypeScript
        has_appl_to_right = False
        optional_args = set()

        # Scan right to left to determine which args should be optional
        for arg in reversed(method.abi.args):
            is_txn_type = algosdk.abi.is_abi_transaction_type(arg.abi_type)
            is_appl_type = is_txn_type and arg.abi_type in APPL_TYPE_TXNS

            if is_txn_type and has_appl_to_right:
                optional_args.add(arg.name)

            if not has_appl_to_right and is_appl_type:
                has_appl_to_right = True

        typed_dict_name = f"{context.sanitizer.make_safe_type_identifier(method.abi.client_method_name)}Args"

        yield utils.indented(f"""
@dataclasses.dataclass(frozen=True, kw_only=True)
class {typed_dict_name}:
    \"\"\"Dataclass for {method.abi.client_method_name} arguments\"\"\"
""")
        yield Part.IncIndent

        for arg in method.abi.args:
            # Make arg optional if it has default or is in optional_args set
            is_optional = arg.has_default or arg.name in optional_args
            python_type = f"{arg.python_type} | None = None" if is_optional else arg.python_type
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
@typing.overload
def __init__(self, app_client: applications.AppClient) -> None: ...

@typing.overload
def __init__(
    self,
    *,
    algorand: protocols.AlgorandClientProtocol,
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
    app_client: applications.AppClient | None = None,
    *,
    algorand: protocols.AlgorandClientProtocol | None = None,
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
        self.app_client = applications.AppClient(
            applications.AppClientParams(
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
    algorand: protocols.AlgorandClientProtocol,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
    ignore_cache: bool | None = None,
    app_lookup_cache: applications.AppLookup | None = None,
) -> \"{context.contract_name}Client\":
    return {context.contract_name}Client(
        applications.AppClient.from_creator_and_name(
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
    algorand: protocols.AlgorandClientProtocol,
    app_name: str | None = None,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> \"{context.contract_name}Client\":
    return {context.contract_name}Client(
        applications.AppClient.from_network(
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
def app_spec(self) -> applications.Arc56Contract:
    return self.app_client.app_spec

@property
def algorand(self) -> protocols.AlgorandClientProtocol:
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
    return_value: applications_abi.ABIReturn | None
) -> {overload_return}: ...
""")

    # Create union of all possible return types
    base_union = "applications_abi.ABIValue | applications_abi.ABIStruct"
    return_union = f"{base_union}{' | None' if 'None' not in return_types else ''}" + (
        f" | {' | '.join(sorted(return_types))}" if return_types else ""
    )

    if len(overloads) > 0:
        overloads.append(f"""
    @typing.overload
def decode_return_value(
    self,
    method: str,
    return_value: applications_abi.ABIReturn | None
) -> {base_union} | None: ...
""")

    # Then generate the actual implementation
    implementation = f"""
def decode_return_value(
    self,
    method: str,
    return_value: applications_abi.ABIReturn | None
) -> {return_union}:
    \"\"\"Decode ABI return value for the given method.\"\"\"
    if return_value is None:
        return None

    arc56_method = self.app_spec.get_arc56_method(method)
    decoded = return_value.get_arc56_value(arc56_method, self.app_spec.structs)

    # If method returns a struct, convert the dict to appropriate dataclass
    if (arc56_method and
        arc56_method.returns and
        arc56_method.returns.struct and
        isinstance(decoded, dict)):
        struct_class = globals().get(arc56_method.returns.struct)
        if struct_class:
            return struct_class(**typing.cast(dict, decoded))
    return decoded
"""

    # Yield all the overloads first
    for overload in overloads:
        yield utils.indented(overload)

    if len(overloads) > 0:
        yield Part.Gap1

    # Then yield the implementation
    yield utils.indented(implementation)


def generate_new_group(context: GeneratorContext) -> DocumentParts:
    """Generate new_group method for creating transaction groups"""
    yield utils.indented(f"""
def new_group(self) -> "{context.contract_name}Composer":
    return {context.contract_name}Composer(self)
""")


def generate_structs(context: GeneratorContext) -> DocumentParts:  # noqa: C901, PLR0912
    """Generate struct classes for ABI structs"""
    first = True
    # Track generated structs by their class name to avoid duplicates
    generated_structs: set[str] = set()

    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue

        # Get all structs from method args and return type
        all_structs = list(context.structs.values())
        for struct in all_structs:
            # First generate any nested struct classes
            for field in struct.fields:
                if field.is_nested:
                    assert isinstance(field.abi_type, list)
                    nested_struct = ABIStruct(
                        abi_name=f"{struct.abi_name}_{field.name}",
                        struct_class_name=f"{struct.struct_class_name}{field.name.title()}",
                        fields=[
                            ABIStructField(
                                name=f.name,
                                abi_type=f.abi_type,
                                python_type=f.python_type,
                                is_nested=isinstance(f.abi_type, list),
                            )
                            for f in field.abi_type
                        ],
                    )
                    # Only generate if we haven't seen this nested struct before
                    if nested_struct.struct_class_name not in generated_structs:
                        if not first:
                            yield Part.Gap1
                        first = False
                        generated_structs.add(nested_struct.struct_class_name)
                        yield utils.indented(f"""
@dataclasses.dataclass(frozen=True)
class {nested_struct.struct_class_name}:
    \"\"\"Struct for {nested_struct.abi_name}\"\"\"
""")
                        yield Part.IncIndent
                        for nested_field in nested_struct.fields:
                            yield f"{nested_field.name}: {nested_field.python_type}"
                        yield Part.DecIndent
                        yield Part.Gap1

            # Then generate the main struct class if we haven't already
            if struct.struct_class_name not in generated_structs:
                if not first:
                    yield Part.Gap1
                first = False
                generated_structs.add(struct.struct_class_name)
                yield utils.indented(f"""
@dataclasses.dataclass(frozen=True)
class {struct.struct_class_name}:
    \"\"\"Struct for {struct.abi_name}\"\"\"
""")
                yield Part.IncIndent
                for field in struct.fields:
                    if field.is_nested:
                        yield f"{field.name}: {field.python_type}"
                    else:
                        yield f"{field.name}: {field.python_type}"
                yield Part.DecIndent


def _generate_state_typeddict(
    state_type: str, keys: dict, class_name: str, structs: dict[str, "ABIStruct"]
) -> Iterator[DocumentParts]:
    """Generate a TypedDict for a specific state type"""
    if not keys:
        return

    yield utils.indented(f"""
class {class_name}(typing.TypedDict):
    \"\"\"Shape of {state_type} state key values\"\"\"
""")
    yield Part.IncIndent
    for key_name, key_info in keys.items():
        python_type = utils.map_abi_type_to_python(key_info.value_type, structs=structs)
        yield f"{key_name}: {python_type}"
    yield Part.DecIndent


def _generate_state_class(  # noqa: PLR0913
    context: GeneratorContext,
    state_type: str,
    class_name: str,
    keys: dict,
    maps: dict,
    value_type_name: str | None = None,
    extra_params: str = "",
) -> Iterator[DocumentParts]:
    """Generate a state access class with typed methods"""

    # Pre-generate the struct mapping for this state type
    struct_mapping = {}

    # Check keys for structs
    for key_info in keys.values():
        if key_info.value_type in context.structs:
            struct_mapping[key_info.value_type] = context.structs[key_info.value_type].struct_class_name

    # Check maps for structs
    for map_info in maps.values():
        if map_info.value_type in context.structs:
            struct_mapping[map_info.value_type] = context.structs[map_info.value_type].struct_class_name

    # Generate the struct mapping as a class variable
    struct_mapping_str = (
        "{\n            " + ",\n            ".join(f'"{k}": {v}' for k, v in struct_mapping.items()) + "\n        }"
        if struct_mapping
        else "{}"
    )

    yield utils.indented(f"""
class {class_name}:
    def __init__(self, app_client: applications.AppClient{extra_params}):
        self.app_client = app_client
        {'self.address = address' if extra_params else ''}
        # Pre-generated mapping of value types to their struct classes
        self._struct_classes: dict[str, typing.Type[typing.Any]] = {struct_mapping_str}

    def get_all(self) -> {value_type_name or 'dict[str, typing.Any]'}:
        \"\"\"Get all current keyed values from {state_type} state\"\"\"
        result = self.app_client.state.{state_type}{'(self.address)' if extra_params else ''}.get_all()
        if not result:
            return {'typing.cast(' + value_type_name + ', {})' if value_type_name else '{}'}

        converted = {{}}
        for key, value in result.items():
            key_info = self.app_client.app_spec.state.keys.{state_type}.get(key)
            struct_class = self._struct_classes.get(key_info.value_type) if key_info else None
            converted[key] = (
                struct_class(**value) if struct_class and isinstance(value, dict)
                else value
            )
        return {'typing.cast(' + value_type_name + ', converted)' if value_type_name else 'converted'}
""")

    # Generate methods for individual keys
    if keys:
        for key_name, key_info in keys.items():
            python_type = utils.map_abi_type_to_python(key_info.value_type, utils.IOType.OUTPUT, context.structs)
            yield Part.Gap1
            yield Part.IncIndent
            yield utils.indented(f"""
    def {utils.get_method_name(key_name)}(self) -> {python_type}:
        \"\"\"Get the current value of the {key_name} key in {state_type} state\"\"\"
        value = self.app_client.state.{state_type}{'(self.address)' if extra_params else ''}.get_value("{key_name}")
        if isinstance(value, dict) and "{key_info.value_type}" in self._struct_classes:
            return self._struct_classes["{key_info.value_type}"](**value)  # type: ignore
        return typing.cast({python_type}, value)
""")
            yield Part.DecIndent

    # Generate methods for maps
    if maps:
        for map_name, map_info in maps.items():
            key_type = utils.map_abi_type_to_python(map_info.key_type, utils.IOType.INPUT, context.structs)
            value_type = utils.map_abi_type_to_python(map_info.value_type, utils.IOType.OUTPUT, context.structs)
            is_value_struct = map_info.value_type in context.structs
            yield Part.Gap1
            yield Part.IncIndent
            yield utils.indented(f"""
@property
def {utils.get_method_name(map_name)}(self) -> "_MapState[{key_type}, {value_type}]":
    \"\"\"Get values from the {map_name} map in {state_type} state\"\"\"
    return _MapState(
        self.app_client.state.{state_type}{'(self.address)' if extra_params else ''},
        "{map_name}",
        {f'self._struct_classes.get("{map_info.value_type}")' if is_value_struct else 'None'}
    )
""")
            yield Part.DecIndent


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
        keys = getattr(context.app_spec.state.keys, state_type)
        if keys:
            yield from _generate_state_typeddict(state_type, keys, value_type, context.structs)
            yield Part.Gap1

    # Generate main state class
    yield utils.indented(f"""
class {context.contract_name}State:
    \"\"\"Methods to access state for the current {context.app_spec.name} app\"\"\"

    def __init__(self, app_client: applications.AppClient):
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
        yield utils.indented(f"""
    {decorator}
def {state_type.split('_')[0]}{'_state' if state_type != 'box' else ''}(
    self{', address: str' if state_type == 'local_state' else ''}
) -> "{class_name}":
        \"\"\"Methods to access {state_type} for the current app\"\"\"
        return {class_name}(self.app_client{', address' if state_type == 'local_state' else ''})
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
            value_type_name=value_type if keys else None,
            extra_params=extra_params,
        )
        yield Part.Gap1

    # Generate MapState class if needed
    if any(bool(getattr(context.app_spec.state.maps, t)) for t in ["global_state", "local_state", "box"]):
        yield utils.indented("""
KeyType = typing.TypeVar("KeyType")
ValueType = typing.TypeVar("ValueType")

class _AppClientStateMethodsProtocol(typing.Protocol):
    def get_map(self, map_name: str) -> dict[typing.Any, typing.Any]:
        ...
    def get_map_value(self, map_name: str, key: typing.Any) -> typing.Any | None:
        ...

class _MapState(typing.Generic[KeyType, ValueType]):
    \"\"\"Generic class for accessing state maps with strongly typed keys and values\"\"\"

    def __init__(self, state_accessor: _AppClientStateMethodsProtocol, map_name: str,
                 struct_class: typing.Type[ValueType] | None = None):
        self._state_accessor = state_accessor
        self._map_name = map_name
        self._struct_class = struct_class

    def get_map(self) -> dict[KeyType, ValueType]:
        \"\"\"Get all current values in the map\"\"\"
        result = self._state_accessor.get_map(self._map_name)
        if self._struct_class and result:
            return {k: self._struct_class(**v) if isinstance(v, dict) else v
                    for k, v in result.items()}
        return typing.cast(dict[KeyType, ValueType], result or {})

    def get_value(self, key: KeyType) -> ValueType | None:
        \"\"\"Get a value from the map by key\"\"\"
        key_value = dataclasses.asdict(key) if dataclasses.is_dataclass(key) else key  # type: ignore
        value = self._state_accessor.get_map_value(self._map_name, key_value)
        if value is not None and self._struct_class and isinstance(value, dict):
            return self._struct_class(**value)
        return typing.cast(ValueType | None, value)
""")


def generate_typed_client(context: GeneratorContext) -> DocumentParts:
    """Generate the complete typed client class"""

    # Generate structs
    yield Part.Gap2
    yield generate_structs(context)

    # Generate supporting classes
    yield Part.Gap2
    yield generate_structs_for_args(context)
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
