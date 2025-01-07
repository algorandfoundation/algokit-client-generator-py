from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts


def generate_typed_factory(context: GeneratorContext) -> DocumentParts:
    """Generate the factory class for deploying and managing smart contracts"""
    yield utils.indented(f"""
class {context.client_name}Factory(TypedAppFactoryProtocol):
    \"\"\"Factory for deploying and managing {context.client_name} smart contracts\"\"\"

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
    ) -> {context.client_name}:
        return {context.client_name}(
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
    ) -> {context.client_name}:
        return {context.client_name}(
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
        existing_deployments: AppLookup | None = None,
        ignore_cache: bool = False,
        updatable: bool | None = None,
        deletable: bool | None = None,
        app_name: str | None = None,
        max_rounds_to_wait: int | None = None,
        suppress_log: bool = False,
        populate_app_call_resources: bool = False,
    ) -> tuple[{context.client_name}, AppFactoryDeployResponse]:
        deploy_response = self.app_factory.deploy(
            deploy_time_params=deploy_time_params,
            on_update=on_update,
            on_schema_break=on_schema_break,
            existing_deployments=existing_deployments,
            ignore_cache=ignore_cache,
            updatable=updatable,
            deletable=deletable,
            app_name=app_name,
            max_rounds_to_wait=max_rounds_to_wait,
            suppress_log=suppress_log,
            populate_app_call_resources=populate_app_call_resources,
        )

        return {context.client_name}(deploy_response[0]), deploy_response[1]
""")
