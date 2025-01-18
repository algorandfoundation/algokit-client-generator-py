from typing import Literal

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ContractMethod


def _generate_on_complete_type() -> str:
    """Generate the OnComplete type literal"""
    return """Literal[
                OnComplete.NoOpOC,
                OnComplete.UpdateApplicationOC,
                OnComplete.DeleteApplicationOC,
                OnComplete.OptInOC,
                OnComplete.CloseOutOC,
            ]"""


def _generate_method_args_type(method: ContractMethod) -> str:
    """Generate the args type for a method"""
    if not method.abi or not method.abi.args:
        return "Any"
    tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
    return f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"


def _generate_method_args_parser() -> str:
    """Generate code to parse method arguments"""
    return """
        method_args = None
        if isinstance(args, tuple):
            method_args = list(args)
        elif isinstance(args, dict):
            method_args = list(args.values())
    """


def _generate_common_method_params(method_name: str, args_type: str) -> str:
    """Generate common method parameters"""
    return f"""
    def {method_name}(
        self,
        args: {args_type},
        *,
        on_complete: ({_generate_on_complete_type()} | None) = None,
        **kwargs
    )"""


def _generate_abi_method(method: ContractMethod, operation: str) -> DocumentParts:
    """Generate an ABI method"""
    if not method.abi:
        return ""

    args_type = _generate_method_args_type(method)
    method_params = _generate_common_method_params(method.abi.client_method_name, args_type)

    yield Part.Gap1
    yield Part.IncIndent
    yield utils.indented(f"""
    {method_params} -> App{operation.title()}{'MethodCall' if method.abi else ''}Params:
        \"\"\"Creates a new instance using the {method.abi.method.get_signature()} ABI method\"\"\"
        {_generate_method_args_parser()}
        return self.app_factory.params.{operation}(
            AppFactoryCreateMethodCallParams(
                method="{method.abi.method.get_signature()}",
                args=method_args, # type: ignore
                on_complete=on_complete,
                **kwargs
            )
        )
""")
    yield Part.DecIndent


def _generate_abi_transaction_method(method: ContractMethod) -> DocumentParts:
    """Generate an ABI transaction method"""
    if not method.abi:
        return ""

    args_type = _generate_method_args_type(method)
    method_params = _generate_common_method_params(method.abi.client_method_name, args_type)

    yield Part.IncIndent
    yield utils.indented(f"""
    {method_params} -> BuiltTransactions:
        \"\"\"Creates a transaction using the {method.abi.method.get_signature()} ABI method\"\"\"
        {_generate_method_args_parser()}
        return self.app_factory.create_transaction.create(
            AppFactoryCreateMethodCallParams(
                method="{method.abi.method.get_signature()}",
                args=method_args, # type: ignore
                on_complete=on_complete,
                **kwargs
            )
        )
""")
    yield Part.DecIndent


def _generate_abi_send_method(method: ContractMethod, context: GeneratorContext) -> DocumentParts:
    """Generate an ABI send method"""
    if not method.abi:
        return ""

    args_type = _generate_method_args_type(method)
    return_type = method.abi.python_type
    method_name = method.abi.client_method_name

    # Handle multiple create methods case
    create_methods = [m for m in context.methods.all_abi_methods if m.call_config == "create"]
    if len(create_methods) > 1:
        signature = method.abi.method.get_signature()
        cleaned_sig = signature.replace("[]", "").replace(",", "_")
        method_name = utils.to_snake_case(cleaned_sig.replace("(", "_").replace(")", "_"))

    method_params = _generate_common_method_params(method_name, args_type)

    yield utils.indented(f"""
    {method_params} -> tuple[{context.contract_name}Client, AppFactoryCreateMethodCallResult[{return_type}]]:
        \"\"\"Creates and sends a transaction using the {method.abi.method.get_signature()} ABI method\"\"\"
        {_generate_method_args_parser()}
        result = self.app_factory.send.create(
            AppFactoryCreateMethodCallParams(
                method="{method.abi.method.get_signature()}",
                args=method_args, # type: ignore
                on_complete=on_complete,
                **kwargs
            )
        )
        return_value = None if result[1].abi_return is None else cast({return_type}, result[1].abi_return)

        return {context.contract_name}Client(result[0]), AppFactoryCreateMethodCallResult[{return_type}](
            app_id=result[1].app_id,
            abi_return=return_value,
            transaction=result[1].transaction,
            confirmation=result[1].confirmation,
            group_id=result[1].group_id,
            tx_ids=result[1].tx_ids,
            transactions=result[1].transactions,
            confirmations=result[1].confirmations,
            app_address=result[1].app_address,
        )
""")


def _generate_operation_params_class(context: GeneratorContext, operation: str) -> DocumentParts:
    """Generate params class for a specific operation"""
    class_name = f"{context.contract_name}Factory{operation.title()}Params"
    method_name = f"deploy_{operation}" if operation != "create" else operation

    yield utils.indented(f"""
class {class_name}:
    \"\"\"Parameters for '{operation}' operations of {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: ({_generate_on_complete_type()} | None) = None,
        **kwargs
    ) -> App{operation.title()}Params:
        \"\"\"{operation.title()}s an instance using a bare call\"\"\"
        return self.app_factory.params.bare.{method_name}(
            AppFactoryCreateParams(on_complete=on_complete, **kwargs)
        )
""")

    # Generate ABI methods if applicable
    if operation == "create":
        for method in context.methods.all_abi_methods:
            if not method.abi:
                continue
            yield Part.Gap1
            yield _generate_abi_method(method, operation)


def _generate_deploy_params(context: GeneratorContext) -> tuple[list[str], list[str]]:
    """Generate deploy parameters and their forwarding code based on available methods"""
    deploy_param_types = []
    argument_forwarding = []

    # Only include create params if there are create methods
    if context.methods.create:
        create_types = []
        if any(m.abi for m in context.methods.create):
            create_types.append(f"{context.contract_name}MethodCallCreateParams")
        if any(not m.abi for m in context.methods.create):
            create_types.append(f"{context.contract_name}BareCallCreateParams")
        if create_types:
            deploy_param_types.append(f"create_params: {' | '.join(create_types)} | None = None")
            argument_forwarding.append(
                "create_params=create_params.to_algokit_utils_params() if create_params else None"
            )

    # Only include update params if there are update methods
    if context.methods.update_application:
        update_types = []
        if any(m.abi for m in context.methods.update_application):
            update_types.append(f"{context.contract_name}MethodCallUpdateParams")
        if any(not m.abi for m in context.methods.update_application):
            update_types.append(f"{context.contract_name}BareCallUpdateParams")
        if update_types:
            deploy_param_types.append(f"update_params: {' | '.join(update_types)} | None = None")
            argument_forwarding.append(
                "update_params=update_params.to_algokit_utils_params() if update_params else None"
            )

    # Only include delete params if there are delete methods
    if context.methods.delete_application:
        delete_types = []
        if any(m.abi for m in context.methods.delete_application):
            delete_types.append(f"{context.contract_name}MethodCallDeleteParams")
        if any(not m.abi for m in context.methods.delete_application):
            delete_types.append(f"{context.contract_name}BareCallDeleteParams")
        if delete_types:
            deploy_param_types.append(f"delete_params: {' | '.join(delete_types)} | None = None")
            argument_forwarding.append(
                "delete_params=delete_params.to_algokit_utils_params() if delete_params else None"
            )

    return deploy_param_types, argument_forwarding


def generate_factory_deploy_types(
    context: GeneratorContext, param_type: Literal["create", "update_application", "delete_application"]
) -> DocumentParts:
    """Generate the factory deploy types for create, update, or delete operations"""
    methods: list[ContractMethod] = getattr(context.methods, param_type)
    if not methods:
        return ""

    # Check if this type is actually used in deploy params
    deploy_params, _ = _generate_deploy_params(context)
    param_prefix = {"create": "create", "update_application": "update", "delete_application": "delete"}[param_type]
    if not any(param.startswith(f"{param_prefix}_params:") for param in deploy_params):
        return ""

    is_create = param_type == "create"
    type_suffix = {"create": "Create", "update_application": "Update", "delete_application": "Delete"}[param_type]

    # Split methods into ABI and bare methods
    abi_methods = [m for m in methods if m.abi]
    bare_methods = [m for m in methods if not m.abi]

    # Generate ABI method params class if there are ABI methods
    if abi_methods:
        yield Part.Gap1

        # Build method signature and args unions
        method_data = []
        for m in abi_methods:
            if m.abi and m.abi.args:
                args_type = f"Tuple[{', '.join(arg.python_type for arg in m.abi.args)}]"
                args_union = f"{args_type} | {utils.to_camel_case(m.abi.client_method_name)}Args"
                method_sig = f'Literal["{m.abi.method.get_signature()}"]'
                method_data.append((args_union, method_sig))

        args_unions, method_signatures = zip(*method_data, strict=False) if method_data else ([], [])

        # Collect unique on_complete values
        on_completes = set()
        for m in abi_methods:
            for on_complete in m.on_complete:
                formatted = f"OnComplete.{on_complete.replace('_', ' ').title().replace(' ', '')}OC"
                on_completes.add(formatted)

        class_name = f"{context.contract_name}MethodCall{type_suffix}Params"

        yield utils.indented(f"""
@dataclass(frozen=True)
class {class_name}(
    {'AppClientCreateSchema, ' if is_create else ''}BaseAppClientMethodCallParams[
        {', '.join(args_unions) if len(args_unions) == 1 else f'Union[{", ".join(args_unions)}]' if args_unions else 'Any'},
        {', '.join(method_signatures) if len(method_signatures) == 1 else f'Union[{", ".join(method_signatures)}]' if method_signatures else 'Any'},
        Literal[{', '.join(sorted(on_completes))}]
    ]
):
    \"\"\"Parameters for {'creating' if is_create else 'calling'} {context.contract_name} contract using ABI\"\"\"

    def to_algokit_utils_params(self) -> AppClientMethodCall{'Create' if is_create else ''}Params:
        method_args = list(self.args.values()) if isinstance(self.args, dict) else self.args
        return AppClientMethodCall{'Create' if is_create else ''}Params(
            **{{
                **self.__dict__,
                "args": method_args,
            }}
        )
""")

    # Generate bare method params class if there are bare methods
    if bare_methods:
        yield Part.Gap1

        # Get on_complete options for bare methods
        on_complete_options = set()
        for m in bare_methods:
            for on_complete in m.on_complete:
                formatted = f"OnComplete.{on_complete.replace('_', ' ').title().replace(' ', '')}OC"
                on_complete_options.add(formatted)

        base_classes = []
        if is_create:
            base_classes.append("AppClientCreateSchema")
        base_classes.append("AppClientBareCallParams")
        if is_create and on_complete_options:
            base_classes.append(f"BaseOnCompleteParams[Literal[{', '.join(sorted(on_complete_options))}]]")

        class_name = f"{context.contract_name}BareCall{type_suffix}Params"

        yield utils.indented(f"""
@dataclass(frozen=True)
class {class_name}({', '.join(base_classes)}):
    \"\"\"Parameters for {'creating' if is_create else 'calling'} {context.contract_name} contract using bare calls\"\"\"

    def to_algokit_utils_params(self) -> AppClientBareCall{'Create' if is_create else ''}Params:
        return AppClientBareCall{'Create' if is_create else ''}Params(**self.__dict__)
""")


def generate_factory_class(
    context: GeneratorContext, deploy_params: list[str], argument_forwarding: list[str]
) -> DocumentParts:
    """Generate the main factory class"""

    yield utils.indented(f"""
class {context.contract_name}Factory(TypedAppFactoryProtocol):
    \"\"\"Factory for deploying and managing {context.contract_name}Client smart contracts\"\"\"

    def __init__(
        self,
        algorand: AlgorandClientProtocol,
        *,
        app_name: str | None = None,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        version: str | None = None,
        updatable: bool | None = None,
        deletable: bool | None = None,
        deploy_time_params: TealTemplateParams | None = None,
    ):
        self.app_factory = AppFactory(
            params=AppFactoryParams(
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

    @property
    def app_name(self) -> str:
        return self.app_factory.app_name

    @property
    def app_spec(self) -> Arc56Contract:
        return self.app_factory.app_spec

    @property
    def algorand(self) -> AlgorandClientProtocol:
        return self.app_factory.algorand

    def deploy(
        self,
        *,
        deploy_time_params: TealTemplateParams | None = None,
        on_update: OnUpdate = OnUpdate.Fail,
        on_schema_break: OnSchemaBreak = OnSchemaBreak.Fail,
        {',\n        '.join(deploy_params)},
        existing_deployments: AppLookup | None = None,
        ignore_cache: bool = False,
        updatable: bool | None = None,
        deletable: bool | None = None,
        app_name: str | None = None,
        max_rounds_to_wait: int | None = None,
        suppress_log: bool = False,
        populate_app_call_resources: bool = False,
    ) -> tuple[{context.contract_name}Client, AppFactoryDeployResponse]:
        deploy_response = self.app_factory.deploy(
            deploy_time_params=deploy_time_params,
            on_update=on_update,
            on_schema_break=on_schema_break,
            {',\n            '.join(argument_forwarding)},
            existing_deployments=existing_deployments,
            ignore_cache=ignore_cache,
            updatable=updatable,
            deletable=deletable,
            app_name=app_name,
            max_rounds_to_wait=max_rounds_to_wait,
            suppress_log=suppress_log,
            populate_app_call_resources=populate_app_call_resources,
        )

        return {context.contract_name}Client(deploy_response[0]), deploy_response[1]

    def get_app_client_by_creator_and_name(
        self,
        creator_address: str,
        app_name: str,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        ignore_cache: bool | None = None,
        app_lookup_cache: AppLookup | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> {context.contract_name}Client:
        \"\"\"Get an app client by creator address and name\"\"\"
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

    def get_app_client_by_id(
        self,
        app_id: int,
        app_name: str | None = None,
        default_sender: str | bytes | None = None,
        default_signer: TransactionSigner | None = None,
        approval_source_map: SourceMap | None = None,
        clear_source_map: SourceMap | None = None,
    ) -> {context.contract_name}Client:
        \"\"\"Get an app client by app ID\"\"\"
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
""")


def generate_factory_params(context: GeneratorContext) -> DocumentParts:
    """Generate factory params classes"""
    yield utils.indented(f"""
class {context.contract_name}FactoryParams:
    \"\"\"Parameters for creating transactions for {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactoryCreateParams(app_factory)
        self.deploy_update = {context.contract_name}FactoryUpdateParams(app_factory)
        self.deploy_delete = {context.contract_name}FactoryDeleteParams(app_factory)
""")

    # Generate params classes for create/update/delete
    for operation in ["create", "update", "delete"]:
        yield Part.Gap1
        yield _generate_operation_params_class(context, operation)


def _generate_factory_create_transaction(context: GeneratorContext) -> DocumentParts:
    """Generate factory create transaction classes"""
    yield utils.indented(f"""
class {context.contract_name}FactoryCreateTransaction:
    \"\"\"Create transactions for {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactoryCreateTransactionCreate(app_factory)
""")

    yield Part.Gap1
    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue
        yield Part.Gap1
        yield _generate_abi_transaction_method(method)


def _generate_factory_send(context: GeneratorContext) -> DocumentParts:
    """Generate factory send classes"""
    yield utils.indented(f"""
class {context.contract_name}FactorySend:
    \"\"\"Send calls to {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactorySendCreate(app_factory)
""")


def _generate_create_transaction_class(context: GeneratorContext) -> DocumentParts:
    """Generate the create transaction class"""
    yield utils.indented(f"""
class {context.contract_name}FactoryCreateTransactionCreate:
    \"\"\"Create new instances of {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: ({_generate_on_complete_type()} | None) = None,
        **kwargs
    ) -> Transaction:
        \"\"\"Creates a new instance using a bare call\"\"\"
        return self.app_factory.create_transaction.bare.create(
            AppFactoryCreateParams(on_complete=on_complete, **kwargs)
        )
""")


def _generate_send_class(context: GeneratorContext) -> DocumentParts:
    """Generate the send class"""
    yield utils.indented(f"""
class {context.contract_name}FactorySendCreate:
    \"\"\"Send create calls to {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: ({_generate_on_complete_type()} | None) = None,
        **kwargs
    ) -> tuple[{context.contract_name}Client, SendAppCreateTransactionResult]:
        \"\"\"Creates a new instance using a bare call\"\"\"
        result = self.app_factory.send.bare.create(
            AppFactoryCreateWithSendParams(on_complete=on_complete, **kwargs)
        )
        return {context.contract_name}Client(result[0]), result[1]
""")

    for method in [m for m in context.methods.all_abi_methods if m.call_config == "create"]:
        if not method.abi:
            continue
        yield Part.Gap1
        yield Part.IncIndent
        yield _generate_abi_send_method(method, context)
        yield Part.DecIndent


def generate_typed_factory(context: GeneratorContext) -> DocumentParts:
    """Generate the complete typed factory"""

    # Get deploy parameters
    deploy_param_types, argument_forwarding = _generate_deploy_params(context)

    # Only generate types that are actually used in deploy params
    if any(param.startswith("create_params:") for param in deploy_param_types):
        yield generate_factory_deploy_types(context, "create")
    if any(param.startswith("update_params:") for param in deploy_param_types):
        yield generate_factory_deploy_types(context, "update_application")
    if any(param.startswith("delete_params:") for param in deploy_param_types):
        yield generate_factory_deploy_types(context, "delete_application")

    # Generate factory class
    yield Part.Gap1
    yield generate_factory_class(context, deploy_param_types, argument_forwarding)
    yield Part.Gap2

    # Generate params classes
    yield generate_factory_params(context)
    yield Part.Gap2

    # Generate transaction classes
    yield _generate_factory_create_transaction(context)
    yield Part.Gap2
    yield _generate_create_transaction_class(context)
    yield Part.Gap2

    yield _generate_factory_send(context)
    yield Part.Gap2
    yield _generate_send_class(context)
