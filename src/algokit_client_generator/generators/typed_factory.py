from typing import Literal

from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ContractMethod


def get_bare_create_on_complete_options(method: ContractMethod) -> str:
    on_complete_types = [
        f"OnComplete.{action.replace('_', ' ').title().replace(' ', '')}OC" for action in method.on_complete
    ]
    return f"Literal[{', '.join(on_complete_types)}]"


def generate_factory_deploy_types(
    context: GeneratorContext, param_type: Literal["create", "update_application", "delete_application"]
) -> DocumentParts:
    """Generate the factory deploy types for create, update, or delete operations"""
    yield Part.Gap1

    methods: list[ContractMethod] = getattr(context.methods, param_type)
    if not methods:
        return ""

    is_create = param_type == "create"
    type_suffix = {"create": "Create", "update_application": "Update", "delete_application": "Delete"}[param_type]

    # Split methods into ABI and bare methods
    abi_methods = [m for m in methods if m.abi]
    bare_methods = [m for m in methods if not m.abi]

    # Generate ABI method params class if there are ABI methods
    if abi_methods:
        # Build method signature and args unions
        method_data = [
            (
                f"Tuple[{', '.join(arg.python_type for arg in m.abi.args)}] | {utils.to_camel_case(m.abi.client_method_name)}Args",
                f'Literal["{m.abi.method.get_signature()}"]',
            )
            for m in abi_methods
            if m.abi and m.abi.args
        ]
        args_unions, method_signatures = zip(*method_data, strict=False) if method_data else ([], [])

        # Collect unique on_complete values
        on_completes = {
            f"algosdk.transaction.OnComplete.{on_complete.replace('_', ' ').title().replace(' ', '')}OC"
            for m in abi_methods
            for on_complete in m.on_complete
        }

        class_name = f"{context.contract_name}MethodCall{type_suffix}Params"

        yield utils.indented(f"""
@dataclass(frozen=True)
class {class_name}(
    {'AppClientCreateSchema, ' if is_create else ''}BaseAppClientMethodCallParams[
        {', '.join(args_unions) if len(args_unions) == 1 else f'Union[{", ".join(args_unions)}]' if args_unions else 'Any'},
        {', '.join(method_signatures) if len(method_signatures) == 1 else f'Union[{", ".join(method_signatures)}]' if method_signatures else 'Any'},
        Literal[{', '.join(on_completes)}]
    ]
):
    \"\"\"Parameters for {'creating' if is_create else 'calling'} {context.contract_name} contract\"\"\"
    def to_algokit_utils_params(self) -> AppClientMethodCall{'Create' if is_create else ''}Params:
        method_args = list(self.args.values()) if isinstance(self.args, dict) else self.args
        return AppClientMethodCall{'Create' if is_create else ''}Params(
            **{{
                **self.__dict__,
                "args": method_args,
                "method": APP_SPEC.get_arc56_method(self.method).to_abi_method(),
                }}
            )
""")
    # Generate bare method params class if there are bare methods
    if bare_methods:
        yield Part.Gap1
        on_complete_options = get_bare_create_on_complete_options(bare_methods[0])
        base_classes = (
            "AppClientBareCallParams"
            if not is_create
            else f"AppClientCreateSchema, AppClientBareCallParams, BaseOnCompleteParams[{on_complete_options}]"
        )

        class_name = f"{context.contract_name}BareCall{type_suffix}Params"

        yield utils.indented(f"""
@dataclass(frozen=True)
class {class_name}({base_classes}):
    \"\"\"Parameters for {'creating' if is_create else 'calling'} {context.contract_name} contract using bare calls\"\"\"
    def to_algokit_utils_params(self) -> AppClientBareCall{'Create' if is_create else ''}Params:
        return AppClientBareCall{'Create' if is_create else ''}Params(**self.__dict__)
""")


def generate_typed_factory(context: GeneratorContext) -> DocumentParts:
    # First generate the deploy parameter types based on available methods
    deploy_param_types = []
    argument_forwarding_params = []

    # Only include create params if there are create methods
    if context.methods.create:
        yield generate_factory_deploy_types(context, "create")
        create_types = []
        if any(m.abi for m in context.methods.create):
            create_types.append(f"{context.contract_name}MethodCallCreateParams")
        if any(not m.abi for m in context.methods.create):
            create_types.append(f"{context.contract_name}BareCallCreateParams")
        deploy_param_types.append(f"create_params: {' | '.join(create_types)} | None = None")
        argument_forwarding_params.append(
            "create_params=create_params.to_algokit_utils_params() if create_params else None"
        )
    # Only include update params if there are update methods
    if context.methods.update_application:
        yield generate_factory_deploy_types(context, "update_application")
        update_types = []
        if any(m.abi for m in context.methods.update_application):
            update_types.append(f"{context.contract_name}MethodCallUpdateParams")
        if any(not m.abi for m in context.methods.update_application):
            update_types.append(f"{context.contract_name}BareCallUpdateParams")
        deploy_param_types.append(f"update_params: {' | '.join(update_types)} | None = None")
        argument_forwarding_params.append(
            "update_params=update_params.to_algokit_utils_params() if update_params else None"
        )
    # Only include delete params if there are delete methods
    if context.methods.delete_application:
        yield generate_factory_deploy_types(context, "delete_application")
        delete_types = []
        if any(m.abi for m in context.methods.delete_application):
            delete_types.append(f"{context.contract_name}MethodCallDeleteParams")
        if any(not m.abi for m in context.methods.delete_application):
            delete_types.append(f"{context.contract_name}BareCallDeleteParams")
        deploy_param_types.append(f"delete_params: {' | '.join(delete_types)} | None = None")
        argument_forwarding_params.append(
            "delete_params=delete_params.to_algokit_utils_params() if delete_params else None"
        )
    # Generate the factory class with conditional deploy parameters
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

    def deploy(
        self,
        *,
        deploy_time_params: TealTemplateParams | None = None,
        on_update: OnUpdate = OnUpdate.Fail,
        on_schema_break: OnSchemaBreak = OnSchemaBreak.Fail,
        {',\n           '.join(deploy_param_types)},
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
            {',\n               '.join(argument_forwarding_params)},
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
""")

    # Generate the supporting classes based on available methods
    yield Part.Gap2
    yield generate_factory_params(context)
    yield Part.Gap2
    yield generate_factory_create_transaction(context)
    yield Part.Gap2
    yield generate_factory_send(context)


def generate_factory_params(context: GeneratorContext) -> DocumentParts:
    """Generate the factory params class with create, update and delete methods"""
    yield utils.indented(f"""
class {context.contract_name}FactoryParams:
    \"\"\"Parameters for creating transactions for {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactoryCreateParams(app_factory)
        self.deploy_update = {context.contract_name}FactoryDeployUpdateParams(app_factory)
        self.deploy_delete = {context.contract_name}FactoryDeployDeleteParams(app_factory)

class {context.contract_name}FactoryCreateParams:
    \"\"\"Parameters for creating new instances of {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: (
            Literal[
                OnComplete.NoOpOC,
                OnComplete.UpdateApplicationOC,
                OnComplete.DeleteApplicationOC,
                OnComplete.OptInOC,
                OnComplete.CloseOutOC,
        ]
        | None) = None,
        **kwargs
    ) -> AppCreateParams:
        \"\"\"Creates a new instance of the {context.contract_name} contract using a bare call

        Args:
            on_complete: On-completion action for the call
            **kwargs: Additional parameters for the call

        Returns:
            The parameters for a create call
        \"\"\"
        return self.app_factory.params.bare.create(AppFactoryCreateParams(on_complete=on_complete, **kwargs))
""")

    yield Part.Gap2
    yield Part.IncIndent

    # Generate ABI method params for create
    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue

        args_type = "Any"
        if method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

        yield utils.indented(f"""
    def {method.abi.client_method_name}(
        self,
        args: {args_type},
        *,
        on_complete: (
            Literal[
                OnComplete.NoOpOC,
                OnComplete.UpdateApplicationOC,
                OnComplete.DeleteApplicationOC,
                OnComplete.OptInOC,
                OnComplete.CloseOutOC,
            ]
            | None
        ) = None,
        **kwargs
    ) -> AppCreateParams:
        \"\"\"Creates a new instance using the {method.abi.method.get_signature()} ABI method

        Args:
            args: The arguments for the method call
            on_complete: On-completion action for the call
            **kwargs: Additional parameters for the call

        Returns:
            The parameters for a create call using this ABI method
        \"\"\"
        if isinstance(args, tuple):
            method_args = list(args)
        else:
            method_args = list(args.values())

        return self.app_factory.params.create(
            AppFactoryCreateMethodCallParams(
                method="{method.abi.method.get_signature()}",
                args=method_args, # type: ignore
                on_complete=on_complete,
                **kwargs
            )
        )
""")

    yield Part.DecIndent

    yield utils.indented(f"""
class {context.contract_name}FactoryDeployUpdateParams:
    \"\"\"Parameters for deploying updates to {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(self, **kwargs) -> AppUpdateParams:
        \"\"\"Updates an existing instance using a bare call

        Args:
            **kwargs: Parameters for the call

        Returns:
            The parameters for an update call
        \"\"\"
        return self.app_factory.params.bare.deploy_update(AppClientBareCallParams(**kwargs))

class {context.contract_name}FactoryDeployDeleteParams:
    \"\"\"Parameters for deleting instances of {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(self, **kwargs) -> AppDeleteParams:
        \"\"\"Deletes an existing instance using a bare call

        Args:
            **kwargs: Parameters for the call

        Returns:
            The parameters for a delete call
        \"\"\"
        return self.app_factory.params.bare.deploy_delete(AppClientBareCallParams(**kwargs))
""")


def generate_factory_create_transaction(context: GeneratorContext) -> DocumentParts:
    """Generate the factory create transaction class"""
    yield utils.indented(f"""
class {context.contract_name}FactoryCreateTransaction:
    \"\"\"Create transactions for {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactoryCreateTransactionCreate(app_factory)

class {context.contract_name}FactoryCreateTransactionCreate:
    \"\"\"Create new instances of {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: (
            Literal[
                OnComplete.NoOpOC,
                OnComplete.UpdateApplicationOC,
                OnComplete.DeleteApplicationOC,
                OnComplete.OptInOC,
                OnComplete.CloseOutOC,
            ]
            | None
        ) = None,
        **kwargs
    ) -> Transaction:
        \"\"\"Creates a new instance using a bare call

        Args:
            on_complete: On-completion action for the call
            **kwargs: Additional parameters for the call

        Returns:
            The transaction for a create call
        \"\"\"
        return self.app_factory.create_transaction.bare.create(
            AppFactoryCreateParams(on_complete=on_complete, **kwargs)
        )
""")

    yield Part.Gap2
    yield Part.IncIndent

    # Generate ABI method transactions
    for method in context.methods.all_abi_methods:
        if not method.abi:
            continue

        args_type = "Any"
        if method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

        yield utils.indented(f"""
    def {method.abi.client_method_name}(
        self,
        args: {args_type},
        *,
        on_complete: (
            Literal[
                OnComplete.NoOpOC,
                OnComplete.UpdateApplicationOC,
                OnComplete.DeleteApplicationOC,
                OnComplete.OptInOC,
                OnComplete.CloseOutOC,
            ]
            | None
        ) = None,
        **kwargs
    ) -> BuiltTransactions:
        \"\"\"Creates a new instance using the {method.abi.method.get_signature()} ABI method

        Args:
            args: The arguments for the method call
            on_complete: On-completion action for the call
            **kwargs: Additional parameters for the call

        Returns:
            The transaction for a create call using this ABI method
        \"\"\"
        if isinstance(args, tuple):
            method_args = list(args)
        else:
            method_args = list(args.values())

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


def generate_factory_send(context: GeneratorContext) -> DocumentParts:
    """Generate the factory send class"""
    yield utils.indented(f"""
class {context.contract_name}FactorySend:
    \"\"\"Send calls to {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory
        self.create = {context.contract_name}FactorySendCreate(app_factory)

class {context.contract_name}FactorySendCreate:
    \"\"\"Send create calls to {context.contract_name} contract\"\"\"

    def __init__(self, app_factory: AppFactory):
        self.app_factory = app_factory

    def bare(
        self,
        *,
        on_complete: (
            Literal[
                OnComplete.NoOpOC,
                OnComplete.UpdateApplicationOC,
                OnComplete.DeleteApplicationOC,
                OnComplete.OptInOC,
                OnComplete.CloseOutOC,
            ]
            | None
        ) = None,
        **kwargs
    ) -> tuple[{context.contract_name}Client, SendAppCreateTransactionResult]:
        \"\"\"Creates a new instance using a bare call

        Args:
            on_complete: On-completion action for the call
            **kwargs: Additional parameters for the call

        Returns:
            A tuple of (client, deploy response)
        \"\"\"
        result = self.app_factory.send.bare.create(
            AppFactoryCreateWithSendParams(on_complete=on_complete, **kwargs)
        )
        return {context.contract_name}Client(result[0]), result[1]
""")

    yield Part.Gap2
    yield Part.IncIndent

    # Generate ABI method sends
    methods = [m for m in context.methods.all_abi_methods if m.call_config == "create"]
    for method in methods:
        if not method.abi:
            continue

        # Convert ABI signature to snake_case method name
        method_name = "create"
        if len(methods) > 1:
            # Convert ABI signature to snake_case method name, properly handling arrays
            signature = method.abi.method.get_signature()
            # First replace array notation and multiple underscores
            cleaned_sig = signature.replace("[]", "").replace(",", "_")
            # Then convert to snake case
            method_name = utils.to_snake_case(cleaned_sig.replace("(", "_").replace(")", "_"))
        args_type = "Any"
        if method.abi.args:
            tuple_type = f"Tuple[{', '.join(arg.python_type for arg in method.abi.args)}]"
            args_type = f"{tuple_type} | {utils.to_camel_case(method.abi.client_method_name)}Args"

        return_type = method.abi.python_type
        yield Part.Gap1
        yield utils.indented(f"""
    def {method_name}(
        self,
        args: {args_type},
        *,
        on_complete: (
            Literal[
                OnComplete.NoOpOC,
                OnComplete.UpdateApplicationOC,
                OnComplete.DeleteApplicationOC,
                OnComplete.OptInOC,
                OnComplete.CloseOutOC,
            ]
            | None
        ) = None,
        **kwargs
    ) -> tuple[{context.contract_name}Client, AppFactoryCreateMethodCallResult]:
        \"\"\"Creates a new instance using the {method.abi.method.get_signature()} ABI method

        Args:
            args: The arguments for the method call
            on_complete: On-completion action for the call
            **kwargs: Additional parameters for the call

        Returns:
            A tuple of (client, deploy response) with the return value from the ABI call
        \"\"\"
        if isinstance(args, tuple):
            method_args = list(args)
        else:
            method_args = list(args.values())

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

    yield Part.DecIndent
