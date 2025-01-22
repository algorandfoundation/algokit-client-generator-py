from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ContractMethod

# Constants
OPERATION_PREFIXES = {"create": "create", "update_application": "update", "delete_application": "delete"}
OPERATION_SUFFIXES = {"create": "Create", "update_application": "Update", "delete_application": "Delete"}


@dataclass
class TypeNames:
    create: list[str]
    update: list[str]
    delete: list[str]


def _generate_method_args_type(context: GeneratorContext, method: ContractMethod) -> str:
    """Generate the args type for a method"""
    if not method.abi or not method.abi.args:
        return "None"

    arg_types = [arg.python_type for arg in method.abi.args]
    tuple_type = f"tuple[{', '.join(arg_types)}]"
    args_type = f"{tuple_type} | {context.sanitizer.make_safe_type_identifier(method.abi.client_method_name)}Args"

    if all(arg.has_default for arg in method.abi.args):
        args_type = f"{args_type} | None = None"

    return args_type


def _generate_method_params(method_name: str, args_type: str) -> str:
    """Generate method parameters with proper indentation"""
    args_param = f"args: {args_type},{utils.NEW_LINE}         *," if args_type != "None" else "*,"

    return f"""
def {method_name}(
    self,
    {args_param}
    account_references: list[str] | None = None,
    app_references: list[int] | None = None,
    asset_references: list[int] | None = None,
    box_references: list[models.BoxReference | models.BoxIdentifier] | None = None,
    extra_fee: models.AlgoAmount | None = None,
    first_valid_round: int | None = None,
    lease: bytes | None = None,
    max_fee: models.AlgoAmount | None = None,
    note: bytes | None = None,
    rekey_to: str | None = None,
    sender: str | None = None,
    signer: TransactionSigner | None = None,
    static_fee: models.AlgoAmount | None = None,
    validity_window: int | None = None,
    last_valid_round: int | None = None,
    extra_program_pages: int | None = None,
    schema: transactions.AppCreateSchema | None = None,
    deploy_time_params: models.TealTemplateParams | None = None,
    updatable: bool | None = None,
    deletable: bool | None = None,
    on_complete: (ON_COMPLETE_TYPES | None) = None
)"""


def _generate_abi_method(context: GeneratorContext, method: ContractMethod, operation: str) -> DocumentParts:
    """Generate an ABI method with proper indentation"""
    if not method.abi:
        return ""

    args_type = _generate_method_args_type(context, method)
    method_params = _generate_method_params(method.abi.client_method_name, args_type)
    method_sig = method.abi.method.get_signature()

    yield Part.IncIndent
    yield utils.indented(f"""
{method_params} -> transactions.App{operation.title()}{'MethodCall' if method.abi else ''}Params:
    \"\"\"Creates a new instance using the {method_sig} ABI method\"\"\"
    params = {{
        k: v for k, v in locals().items()
        if k != 'self' and v is not None
    }}
    return self.app_factory.params.{operation}(
        applications.AppFactoryCreateMethodCallParams(
            **{{
            **params,
            "method": "{method_sig}",
            "args": {'_parse_abi_args(args)' if args_type != 'None' else 'None'}, # type: ignore
            }}
        )
    )
""")
    yield Part.DecIndent


def _generate_abi_send_method(method: ContractMethod, context: GeneratorContext) -> Iterator[DocumentParts]:
    """Generate an ABI send method"""
    if not method.abi:
        return

    args_type = _generate_method_args_type(context, method)
    return_type = method.abi.python_type
    method_name = method.abi.client_method_name

    # Handle multiple create methods case
    create_methods = [m for m in context.methods.all_abi_methods if m.call_config == "create"]
    if len(create_methods) > 1:
        signature = method.abi.method.get_signature()
        cleaned_sig = signature.replace("[]", "").replace(",", "_")
        method_name = utils.to_snake_case(cleaned_sig.replace("(", "_").replace(")", "_"))

    method_params = _generate_method_params(method_name, args_type)

    yield utils.indented(f"""
    {method_params} -> tuple[{context.contract_name}Client, applications.AppFactoryCreateMethodCallResult[{return_type}]]:
        \"\"\"Creates and sends a transaction using the {method.abi.method.get_signature()} ABI method\"\"\"
        params = {{
            k: v for k, v in locals().items()
            if k != 'self' and v is not None
        }}
        client, result = self.app_factory.send.create(
            applications.AppFactoryCreateMethodCallParams(
                **{{
                **params,
                "method": "{method.abi.method.get_signature()}",
                "args": {'_parse_abi_args(args)' if args_type != 'None' else 'None'}, # type: ignore
                }}
            )
        )
        return_value = None if result.abi_return is None else typing.cast({return_type}, result.abi_return)

        return {context.contract_name}Client(client), applications.AppFactoryCreateMethodCallResult[{return_type}](
            **{{
                **result.__dict__,
                "app_id": result.app_id,
                "abi_return": return_value,
                "transaction": result.transaction,
                "confirmation": result.confirmation,
                "group_id": result.group_id,
                "tx_ids": result.tx_ids,
                "transactions": result.transactions,
                "confirmations": result.confirmations,
                "app_address": result.app_address,
            }}
        )
""")  # noqa: E501


def _generate_operation_params_class(context: GeneratorContext, operation: str) -> Iterator[DocumentParts]:
    """Generate params class for a specific operation"""
    class_name = f"{context.contract_name}Factory{operation.title()}Params"
    method_name = "create" if operation == "create" else f"deploy_{operation}"

    yield utils.indented(f"""
class {class_name}:
    \"\"\"Parameters for '{operation}' operations of {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: applications.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        extra_program_pages: int | None = None,
        schema: transactions.AppCreateSchema | None = None,
        signer: TransactionSigner | None = None,
        rekey_to: str | None = None,
        lease: bytes | None = None,
        static_fee: models.AlgoAmount | None = None,
        extra_fee: models.AlgoAmount | None = None,
        max_fee: models.AlgoAmount | None = None,
        validity_window: int | None = None,
        first_valid_round: int | None = None,
        last_valid_round: int | None = None,
        sender: str | None = None,
        note: bytes | None = None,
        account_references: list[str] | None = None,
        app_references: list[int] | None = None,
        asset_references: list[int] | None = None,
        box_references: list[models.BoxReference | models.BoxIdentifier] | None = None,
        deploy_time_params: models.TealTemplateParams | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
        on_complete: (ON_COMPLETE_TYPES | None) = None,
    ) -> transactions.App{operation.title()}Params:
        \"\"\"{operation.title()}s an instance using a bare call\"\"\"
        params = {{
            k: v for k, v in locals().items()
            if k != 'self' and v is not None
        }}
        return self.app_factory.params.bare.{method_name}(
            applications.AppFactoryCreateParams(**params)
        )
""")

    if operation == "create":
        for method in context.methods.all_abi_methods:
            if method.abi:
                yield Part.Gap1
                yield _generate_abi_method(context, method, operation)


def _generate_deploy_params(context: GeneratorContext) -> tuple[list[str], list[str], TypeNames]:
    """Generate deploy parameters and their forwarding code"""
    deploy_param_types = []
    argument_forwarding = []
    type_names = TypeNames(create=[], update=[], delete=[])

    # Helper function to process each method type
    def get_and_process_method_type(method_type: str, prefix: str) -> list[str]:
        methods = getattr(context.methods, method_type) or []

        type_names = []
        if any(m.abi for m in methods):
            type_names.append(f"{context.contract_name}MethodCall{prefix}Params")
        if any(not m.abi for m in methods):
            type_names.append(f"{context.contract_name}BareCall{prefix}Params")

        param_name = f"{method_type.split('_')[0]}_params"
        deploy_param_types.append(
            f"{param_name}: {(' | '.join(type_names) + ' | None') if type_names else 'None'} = None"
        )
        argument_forwarding.append(
            f"{param_name}={param_name}{f'.to_algokit_utils_params() if {param_name} else None' if type_names else ''}"
            if param_name
            else "None"
        )

        return type_names

    # Process each method type
    type_names.create = get_and_process_method_type("create", "Create")
    type_names.update = get_and_process_method_type("update_application", "Update")
    type_names.delete = get_and_process_method_type("delete_application", "Delete")

    return deploy_param_types, argument_forwarding, type_names


def generate_factory_deploy_types(
    context: GeneratorContext,
    param_type: Literal["create", "update_application", "delete_application"],
    deploy_params: list[str],
) -> Iterator[DocumentParts]:
    """Generate factory deploy types with proper indentation"""
    methods = getattr(context.methods, param_type)
    if not methods:
        return

    # Check if type is used in deploy params
    param_prefix = OPERATION_PREFIXES[param_type]
    if not any(param.startswith(f"{param_prefix}_params:") for param in deploy_params):
        return

    is_create = param_type == "create"
    type_suffix = OPERATION_SUFFIXES[param_type]

    # Split methods
    abi_methods = [m for m in methods if m.abi]
    bare_methods = [m for m in methods if not m.abi]

    # Generate ABI method params class
    if abi_methods:
        yield Part.Gap1
        yield from _generate_abi_params_class(
            context=context,
            abi_methods=abi_methods,
            is_create=is_create,
            type_suffix=type_suffix,
        )

    # Generate bare method params class
    if bare_methods:
        yield Part.Gap1
        yield from _generate_bare_params_class(
            context=context, bare_methods=bare_methods, is_create=is_create, type_suffix=type_suffix
        )


def _generate_abi_params_class(
    *, context: GeneratorContext, abi_methods: list[ContractMethod], is_create: bool, type_suffix: str
) -> Iterator[DocumentParts]:
    """Generate ABI params class with proper indentation"""
    # Build method signature and args unions
    method_data = []
    for method in abi_methods:
        if method.abi and method.abi.args:
            args_type = f"tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_union = (
                f"{args_type} | {context.sanitizer.make_safe_type_identifier(method.abi.client_method_name)}Args"
            )
            method_sig = f'typing.Literal["{method.abi.method.get_signature()}"]'
            method_data.append((args_union, method_sig))

    args_unions: tuple[str, ...] = ()
    method_signatures: tuple[str, ...] = ()
    if method_data:
        args_unions, method_signatures = zip(*method_data, strict=False)

    # Get unique on_complete values
    on_completes = {
        f"OnComplete.{on_complete.replace('_', ' ').title().replace(' ', '')}OC"
        for method in abi_methods
        for on_complete in method.on_complete
    }

    class_name = f"{context.contract_name}MethodCall{type_suffix}Params"
    create_schema = "applications.AppClientCreateSchema, " if is_create else ""
    args_union_str = " | ".join(args_unions) if args_unions else "typing.Any"
    method_sig_str = " | ".join(method_signatures) if method_signatures else "typing.Any"
    on_complete_str = ", ".join(sorted(on_completes))

    yield utils.indented(f"""
@dataclasses.dataclass(frozen=True)
class {class_name}(
    {create_schema}applications.BaseAppClientMethodCallParams[
        {args_union_str},
        {method_sig_str},
        typing.Literal[{on_complete_str}]
    ]
):
    \"\"\"Parameters for {'creating' if is_create else 'calling'} {context.contract_name} contract using ABI\"\"\"

    def to_algokit_utils_params(self) -> applications.AppClientMethodCall{'Create' if is_create else ''}Params:
        method_args = _parse_abi_args(self.args)
        return applications.AppClientMethodCall{'Create' if is_create else ''}Params(
            **{{
                **self.__dict__,
                "args": method_args,
            }}
        )
""")


def _generate_bare_params_class(
    *, context: GeneratorContext, bare_methods: list[ContractMethod], is_create: bool, type_suffix: str
) -> Iterator[DocumentParts]:
    """Generate bare params class with proper indentation"""
    on_complete_options = {
        f"OnComplete.{on_complete.replace('_', ' ').title().replace(' ', '')}OC"
        for method in bare_methods
        for on_complete in method.on_complete
    }

    base_classes = []
    if is_create:
        base_classes.append("applications.AppClientCreateSchema")
    base_classes.append("applications.AppClientBareCallParams")
    if is_create and on_complete_options:
        base_classes.append(
            f"applications.BaseOnCompleteParams[typing.Literal[{', '.join(sorted(on_complete_options))}]]"
        )

    class_name = f"{context.contract_name}BareCall{type_suffix}Params"

    yield utils.indented(f"""
@dataclasses.dataclass(frozen=True)
class {class_name}({', '.join(base_classes)}):
    \"\"\"Parameters for {'creating' if is_create else 'calling'} {context.contract_name} contract with bare calls\"\"\"

    def to_algokit_utils_params(self) -> applications.AppClientBareCall{'Create' if is_create else ''}Params:
        return applications.AppClientBareCall{'Create' if is_create else ''}Params(**self.__dict__)
""")


def generate_factory_class(  # noqa: PLR0915
    context: GeneratorContext, deploy_params: list[str], argument_forwarding: list[str], type_names: TypeNames
) -> Iterator[DocumentParts]:
    """Generate the main factory class"""
    create_type_names = " | ".join(type_names.create)
    update_type_names = " | ".join(type_names.update)
    delete_type_names = " | ".join(type_names.delete)
    yield (
        f"class {context.contract_name}Factory("
        f"applications.TypedAppFactoryProtocol["
        f"{create_type_names or 'None'}, "
        f"{update_type_names or 'None'}, "
        f"{delete_type_names or 'None'}]):"
    )
    yield Part.IncIndent

    # Class docstring
    yield utils.docstring(f"Factory for deploying and managing {context.contract_name}Client smart contracts")
    yield Part.NewLine

    # __init__ method with all parameters
    yield utils.indented(f"""
def __init__(
    self,
    algorand: protocols.AlgorandClientProtocol,
    *,
    app_name: str | None = None,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    version: str | None = None,
    updatable: bool | None = None,
    deletable: bool | None = None,
    deploy_time_params: models.TealTemplateParams | None = None,
):
    self.app_factory = applications.AppFactory(
        params=applications.AppFactoryParams(
            algorand=algorand,
            app_spec=APP_SPEC,
            app_name=app_name,
            default_sender=default_sender,
            default_signer=default_signer,
            version=version,
            updatable=updatable,
            deletable=deletable,
            deploy_time_params=deploy_time_params,
        )
    )
    self.params = {context.contract_name}FactoryParams(self.app_factory)
    self.create_transaction = {context.contract_name}FactoryCreateTransaction(self.app_factory)
    self.send = {context.contract_name}FactorySend(self.app_factory)
""")

    # Properties
    yield Part.Gap1
    yield utils.indented("""
@property
def app_name(self) -> str:
    return self.app_factory.app_name

@property
def app_spec(self) -> applications.Arc56Contract:
    return self.app_factory.app_spec

@property
def algorand(self) -> protocols.AlgorandClientProtocol:
    return self.app_factory.algorand
""")

    # Deploy method with all parameters
    yield Part.Gap1
    yield "def deploy("
    yield Part.IncIndent
    yield "self,"
    yield "*,"
    yield "deploy_time_params: models.TealTemplateParams | None = None,"
    yield "on_update: applications.OnUpdate = applications.OnUpdate.Fail,"
    yield "on_schema_break: applications.OnSchemaBreak = applications.OnSchemaBreak.Fail,"
    for param in deploy_params:
        yield f"{param},"
    yield "existing_deployments: applications.AppLookup | None = None,"
    yield "ignore_cache: bool = False,"
    yield "updatable: bool | None = None,"
    yield "deletable: bool | None = None,"
    yield "app_name: str | None = None,"
    yield "max_rounds_to_wait: int | None = None,"
    yield "suppress_log: bool = False,"
    yield "populate_app_call_resources: bool = False,"
    yield Part.DecIndent
    yield f") -> tuple[{context.contract_name}Client, applications.AppFactoryDeployResponse]:"

    yield Part.IncIndent
    yield utils.docstring("Deploy the application")

    yield "deploy_response = self.app_factory.deploy("
    yield Part.IncIndent
    yield "deploy_time_params=deploy_time_params,"
    yield "on_update=on_update,"
    yield "on_schema_break=on_schema_break,"
    for arg in argument_forwarding:
        yield f"{arg},"
    yield "existing_deployments=existing_deployments,"
    yield "ignore_cache=ignore_cache,"
    yield "updatable=updatable,"
    yield "deletable=deletable,"
    yield "app_name=app_name,"
    yield "max_rounds_to_wait=max_rounds_to_wait,"
    yield "suppress_log=suppress_log,"
    yield "populate_app_call_resources=populate_app_call_resources,"
    yield Part.DecIndent
    yield ")"
    yield Part.NewLine
    yield f"return {context.contract_name}Client(deploy_response[0]), deploy_response[1]"
    yield Part.DecIndent

    # Get app client methods
    yield Part.Gap1
    yield utils.indented(f"""
def get_app_client_by_creator_and_name(
    self,
    creator_address: str,
    app_name: str,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    ignore_cache: bool | None = None,
    app_lookup_cache: applications.AppLookup | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> {context.contract_name}Client:""")
    yield Part.IncIndent
    yield utils.docstring("Get an app client by creator address and name")
    yield utils.indented(f"""
return {context.contract_name}Client(
    self.app_factory.get_app_client_by_creator_and_name(
        creator_address,
        app_name,
        default_sender,
        default_signer,
        ignore_cache,
        app_lookup_cache,
        approval_source_map,
        clear_source_map,
    )
)
""")
    yield Part.DecIndent

    yield Part.Gap1
    yield utils.indented(f"""
def get_app_client_by_id(
    self,
    app_id: int,
    app_name: str | None = None,
    default_sender: str | bytes | None = None,
    default_signer: TransactionSigner | None = None,
    approval_source_map: SourceMap | None = None,
    clear_source_map: SourceMap | None = None,
) -> {context.contract_name}Client:""")
    yield Part.IncIndent
    yield utils.docstring("Get an app client by app ID")
    yield utils.indented(
        f"""
return {context.contract_name}Client(
    self.app_factory.get_app_client_by_id(
        app_id,
        app_name,
        default_sender,
        default_signer,
        approval_source_map,
        clear_source_map,
    )
)
"""
    )
    yield Part.DecIndent
    yield Part.DecIndent


def generate_factory_params(context: GeneratorContext) -> Iterator[DocumentParts]:
    """Generate factory params classes"""
    yield utils.indented(f"""
class {context.contract_name}FactoryParams:
    \"\"\"Parameters for creating transactions for {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: applications.AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactoryCreateParams(app_factory)
        self.update = {context.contract_name}FactoryUpdateParams(app_factory)
        self.delete = {context.contract_name}FactoryDeleteParams(app_factory)
""")

    # Generate params classes for create/update/delete
    for operation in ["create", "update", "delete"]:
        yield Part.Gap1
        yield from _generate_operation_params_class(context, operation)


def _generate_factory_create_transaction(context: GeneratorContext) -> Iterator[DocumentParts]:
    """Generate factory create transaction classes"""
    yield utils.indented(f"""
class {context.contract_name}FactoryCreateTransaction:
    \"\"\"Create transactions for {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: applications.AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactoryCreateTransactionCreate(app_factory)
""")


def _generate_factory_send(context: GeneratorContext) -> Iterator[DocumentParts]:
    """Generate factory send classes"""
    yield utils.indented(f"""
class {context.contract_name}FactorySend:
    \"\"\"Send calls to {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: applications.AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactorySendCreate(app_factory)
""")


def _generate_create_transaction_class(context: GeneratorContext) -> Iterator[DocumentParts]:
    """Generate the create transaction class"""
    yield utils.indented(f"""
class {context.contract_name}FactoryCreateTransactionCreate:
    \"\"\"Create new instances of {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: applications.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: (ON_COMPLETE_TYPES | None) = None,
        extra_program_pages: int | None = None,
        schema: transactions.AppCreateSchema | None = None,
        signer: TransactionSigner | None = None,
        rekey_to: str | None = None,
        lease: bytes | None = None,
        static_fee: models.AlgoAmount | None = None,
        extra_fee: models.AlgoAmount | None = None,
        max_fee: models.AlgoAmount | None = None,
        validity_window: int | None = None,
        first_valid_round: int | None = None,
        last_valid_round: int | None = None,
        sender: str | None = None,
        note: bytes | None = None,
        args: list[bytes] | None = None,
        account_references: list[str] | None = None,
        app_references: list[int] | None = None,
        asset_references: list[int] | None = None,
        box_references: list[models.BoxReference | models.BoxIdentifier] | None = None,
        deploy_time_params: models.TealTemplateParams | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
    ) -> Transaction:
        \"\"\"Creates a new instance using a bare call\"\"\"
        params = {{
            k: v for k, v in locals().items()
            if k != 'self' and v is not None
        }}
        return self.app_factory.create_transaction.bare.create(
            applications.AppFactoryCreateParams(**params)
        )
""")


def _generate_send_class(context: GeneratorContext) -> Iterator[DocumentParts]:
    """Generate the send class"""
    yield utils.indented(f"""
class {context.contract_name}FactorySendCreate:
    \"\"\"Send create calls to {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: applications.AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: (ON_COMPLETE_TYPES | None) = None,
        extra_program_pages: int | None = None,
        schema: transactions.AppCreateSchema | None = None,
        max_rounds_to_wait: int | None = None,
        suppress_log: bool | None = None,
        populate_app_call_resources: bool | None = None,
        signer: TransactionSigner | None = None,
        rekey_to: str | None = None,
        lease: bytes | None = None,
        static_fee: models.AlgoAmount | None = None,
        extra_fee: models.AlgoAmount | None = None,
        max_fee: models.AlgoAmount | None = None,
        validity_window: int | None = None,
        first_valid_round: int | None = None,
        last_valid_round: int | None = None,
        sender: str | None = None,
        note: bytes | None = None,
        args: list[bytes] | None = None,
        account_references: list[str] | None = None,
        app_references: list[int] | None = None,
        asset_references: list[int] | None = None,
        box_references: list[models.BoxReference | models.BoxIdentifier] | None = None,
        deploy_time_params: models.TealTemplateParams | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
    ) -> tuple[{context.contract_name}Client, transactions.SendAppCreateTransactionResult]:
        \"\"\"Creates a new instance using a bare call\"\"\"
        params = {{
            k: v for k, v in locals().items()
            if k != 'self' and v is not None
        }}
        result = self.app_factory.send.bare.create(
            applications.AppFactoryCreateWithSendParams(**params)
        )
        return {context.contract_name}Client(result[0]), result[1]
""")

    for method in [m for m in context.methods.all_abi_methods if m.call_config == "create"]:
        if method.abi:
            yield Part.Gap1
            yield Part.IncIndent
            yield from _generate_abi_send_method(method, context)
            yield Part.DecIndent


def generate_typed_factory(context: GeneratorContext) -> DocumentParts:
    """Generate the complete typed factory with proper structure"""
    deploy_param_types, argument_forwarding, type_names = _generate_deploy_params(context)

    # Generate deploy types if needed
    for param_type in ["create", "update_application", "delete_application"]:
        if any(param.startswith(f"{OPERATION_PREFIXES[param_type]}_params:") for param in deploy_param_types):
            yield from generate_factory_deploy_types(context, param_type, deploy_param_types)  # type: ignore  # noqa: PGH003

    # Generate main factory components
    yield Part.Gap1
    yield from generate_factory_class(context, deploy_param_types, argument_forwarding, type_names)
    yield Part.Gap2
    yield from generate_factory_params(context)
    yield Part.Gap2
    yield from _generate_factory_create_transaction(context)
    yield Part.Gap2
    yield from _generate_create_transaction_class(context)
    yield Part.Gap2
    yield from _generate_factory_send(context)
    yield Part.Gap2
    yield from _generate_send_class(context)
