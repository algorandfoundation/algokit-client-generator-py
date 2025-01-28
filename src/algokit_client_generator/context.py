import algokit_utils

from algokit_client_generator import utils
from algokit_client_generator.spec import ABIStruct, get_all_structs, get_contract_methods


class GeneratorContext:
    def __init__(self, app_spec: algokit_utils.Arc56Contract, *, preserve_names: bool = False):
        self.app_spec = app_spec
        self.structs: dict[str, ABIStruct] = {}
        self.sanitizer = utils.get_sanitizer(preserve_names=preserve_names)

        # Reserved module-level symbols to avoid naming conflicts
        self.used_module_symbols = {
            "_APP_SPEC_JSON",  # Used in app_spec.py to store raw JSON
            "APP_SPEC",  # Used throughout as algokit_utils.Arc56Contract instance
            "DeployCreate",  # Used in typed_factory.py for deployment types
            "Deploy",  # Used in typed_factory.py for deployment types
            "Composer",  # Used in composer.py for transaction composition
        }

        # Reserved client method/property names to avoid naming conflicts
        self.used_client_symbols = {
            "__init__",  # Constructor in typed_client.py
            "app_spec",  # Property in typed_client.py returning algokit_utils.Arc56Contract
            "app_client",  # Internal algokit_utils.AppClient instance in typed_client.py
            "app_id",  # Property in typed_client.py returning application ID
            "app_address",  # Property in typed_client.py returning application address
            "no_op",  # Used for no-op transaction methods
            "clear_state",  # Used for clear state transaction methods in typed_client.py
            "deploy",  # Used in typed_factory.py for deployment
            "compose",  # Used for transaction composition in composer.py
            "from_creator_and_name",  # Static factory method in typed_client.py
            "from_network",  # Static factory method in typed_client.py
            "clone",  # Method in typed_client.py for cloning client instance
            "decode_return_value",  # Method in typed_client.py for ABI return value decoding
            "new_group",  # Method in typed_client.py for creating transaction groups
        }

        self.contract_name = utils.get_unique_symbol_by_incrementing(
            self.used_module_symbols, utils.get_class_name(self.app_spec.name)
        )

        self.structs = get_all_structs(self.app_spec, self.used_module_symbols, self.sanitizer)
        self.methods = get_contract_methods(
            self.app_spec, self.structs, self.used_module_symbols, self.used_client_symbols
        )
        self.disable_linting = True
