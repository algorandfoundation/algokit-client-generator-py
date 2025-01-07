import algokit_utils
import algokit_utils.applications

from algokit_client_generator import utils
from algokit_client_generator.spec import get_contract_methods


class GeneratorContext:
    def __init__(self, app_spec: algokit_utils.applications.Arc56Contract):
        self.app_spec = app_spec
        # TODO: track these as they are emitted?
        self.used_module_symbols = {
            "_APP_SPEC_JSON",
            "APP_SPEC",
            "_TArgs",
            "_TArgsHolder",
            "_TResult",
            "_ArgsBase",
            "_as_dict",
            "_filter_none",
            "_convert_on_complete",
            "_convert_deploy_args",
            "DeployCreate",
            "Deploy",
            "GlobalState",
            "LocalState",
            "Composer",
        }
        self.used_client_symbols = {
            "__init__",
            "app_spec",
            "app_client",
            "algod_client",
            "app_id",
            "app_address",
            "sender",
            "signer",
            "suggested_params",
            "no_op",
            "clear_state",
            "deploy",
            "get_global_state",
            "get_local_state",
            "compose",
        }
        self.client_name = utils.get_unique_symbol_by_incrementing(
            self.used_module_symbols, utils.get_class_name(self.app_spec.name, "client")
        )
        self.methods = get_contract_methods(app_spec, self.used_module_symbols, self.used_client_symbols)
        self.disable_linting = True
