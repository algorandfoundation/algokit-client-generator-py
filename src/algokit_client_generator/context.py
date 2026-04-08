import copy
import typing

from algokit_abi import abi, arc56

from algokit_client_generator import utils
from algokit_client_generator.spec import get_contract_methods
from algokit_client_generator.utils import Sanitizer

AppSpecMode = typing.Literal["full", "minimal"]


def _shrink_app_spec(app_spec: arc56.Arc56Contract, mode: AppSpecMode) -> arc56.Arc56Contract:
    """Shrink the app spec by removing unnecessary data for minimal mode"""
    stripped_app_spec = copy.deepcopy(app_spec)

    # Keep only source info entries that can be used for approval and clear program error mapping
    if (
        stripped_app_spec.source_info
        and stripped_app_spec.source_info.approval
        and len(stripped_app_spec.source_info.approval.source_info) > 0
    ):
        stripped_app_spec.source_info.approval.source_info = _shrink_source_info(
            stripped_app_spec.source_info.approval.source_info
        )

    if (
        stripped_app_spec.source_info
        and stripped_app_spec.source_info.clear
        and len(stripped_app_spec.source_info.clear.source_info) > 0
    ):
        stripped_app_spec.source_info.clear.source_info = _shrink_source_info(
            stripped_app_spec.source_info.clear.source_info
        )

    stripped_app_spec.compiler_info = None

    # These are used for deploying but not for calling deployed apps
    if mode == "minimal":
        stripped_app_spec.source = None
        stripped_app_spec.byte_code = None
        stripped_app_spec.template_variables = None
        stripped_app_spec.scratch_variables = None

    return stripped_app_spec


def _shrink_source_info(source_info: list[arc56.SourceInfo]) -> list[arc56.SourceInfo]:
    """Filter source info to keep only entries with error messages for runtime error mapping"""
    filtered_entries = []

    for entry in source_info:
        # Only keep entries that have error messages
        if entry.error_message:
            minimal_entry = arc56.SourceInfo(pc=entry.pc, error_message=entry.error_message)
            # Keep minimal context for error mapping if available
            if entry.teal:
                minimal_entry.teal = entry.teal
            filtered_entries.append(minimal_entry)

    return filtered_entries


class GeneratorContext:
    def __init__(self, app_spec: arc56.Arc56Contract, *, preserve_names: bool = False, mode: AppSpecMode = "full"):
        self.mode = mode
        self.generated_structs = dict[str, str]()
        self.sanitizer = utils.get_sanitizer(preserve_names=preserve_names)
        self.app_spec = _apply_app_spec_changes(app_spec, self.generated_structs, self.sanitizer, mode)

        # Reserved module-level symbols to avoid naming conflicts
        self.used_module_symbols = {
            "_APP_SPEC_JSON",  # Used in app_spec.py to store raw JSON
            "APP_SPEC",  # Used throughout as algokit_utils.Arc56Contract instance
            "_STRUCT_NAME_TO_TYPE",  # used to configure abi.StructType decode types
            "_get_struct_customization",
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

        self.methods = get_contract_methods(self.app_spec, self.used_module_symbols, self.used_client_symbols)
        self.disable_linting = True


def _apply_app_spec_changes(
    app_spec: arc56.Arc56Contract, generated_structs: dict[str, str], sanitizer: Sanitizer, mode: AppSpecMode
) -> arc56.Arc56Contract:
    app_spec = _shrink_app_spec(app_spec, mode)

    # resolve structs to a type with the desired generated name
    # during generation this is just a new dict type with the appropriate name
    # in the generated code there will be another mapping to a generated type
    def resolve_struct_type(s: abi.StructType) -> type:
        struct_name = s.struct_name
        generated_struct_name = sanitizer.make_safe_type_identifier(struct_name)
        generated_structs[struct_name] = generated_struct_name
        return typing.NewType(generated_struct_name, dict)  # type: ignore[return-value]

    return app_spec.apply_decode_types(resolve_struct_type)
