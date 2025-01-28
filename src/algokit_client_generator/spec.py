import copy
import dataclasses
import json
import typing
from collections.abc import Callable, Iterable
from pathlib import Path

from algokit_utils import Arc32Contract, Arc56Contract, CallEnum, CreateEnum, StructField
from algokit_utils import Method as Arc56Method
from algosdk.abi import Method

from algokit_client_generator import utils


@dataclasses.dataclass(kw_only=True)
class ContractArg:
    name: str
    abi_type: str
    python_type: str
    desc: str | None
    has_default: bool = False


@dataclasses.dataclass(kw_only=True)
class ABIStructField:
    name: str
    abi_type: str | list["ABIStructField"]  # Enhanced to handle nested structs
    python_type: str
    is_nested: bool = False
    is_implicit: bool = False


@dataclasses.dataclass(kw_only=True)
class ABIStruct:
    abi_name: str
    struct_class_name: str
    fields: list[ABIStructField]


@dataclasses.dataclass(kw_only=True)
class ABIContractMethod:
    method: Method
    readonly: bool | None
    abi_type: str
    python_type: str
    result_struct: ABIStruct | None
    args: list[ContractArg]
    structs: list[ABIStruct]
    args_class_name: str
    client_method_name: str
    deploy_args_class_name: str
    deploy_create_args_class_name: str


@dataclasses.dataclass(kw_only=True)
class ContractMethod:
    abi: ABIContractMethod | None
    on_complete: list[str]  # Using string literals from Arc56 CallEnum/CreateEnum values
    call_config: typing.Literal["call", "create"]


@dataclasses.dataclass(kw_only=True)
class ContractMethods:
    no_op: list[ContractMethod] = dataclasses.field(default_factory=list)
    create: list[ContractMethod] = dataclasses.field(default_factory=list)
    update_application: list[ContractMethod] = dataclasses.field(default_factory=list)
    delete_application: list[ContractMethod] = dataclasses.field(default_factory=list)
    opt_in: list[ContractMethod] = dataclasses.field(default_factory=list)
    close_out: list[ContractMethod] = dataclasses.field(default_factory=list)

    @property
    def all_methods(self) -> Iterable[ContractMethod]:
        yield from self.no_op
        yield from self.create
        yield from self.update_application
        yield from self.delete_application
        yield from self.opt_in
        yield from self.close_out

    @property
    def all_abi_methods(self) -> Iterable[ContractMethod]:
        return (m for m in self.all_methods if m.abi)

    @property
    def has_abi_methods(self) -> bool:
        return any(self.all_abi_methods)

    def add_method(
        self, abi: ABIContractMethod | None, call_actions: list[CallEnum], create_actions: list[CreateEnum]
    ) -> None:
        # Handle call actions
        for action in call_actions:
            action_name = _map_enum_to_property(action.value if isinstance(action, CallEnum) else action)
            collection = getattr(self, action_name)
            contract_method = ContractMethod(
                abi=abi,
                call_config="call",
                on_complete=[action_name],
            )
            collection.append(contract_method)

        # Handle create actions
        if create_actions:
            contract_method = ContractMethod(
                abi=abi,
                call_config="create",
                on_complete=[
                    _map_enum_to_property(action.value if isinstance(action, CreateEnum) else action)
                    for action in create_actions
                ],
            )
            self.create.append(contract_method)


def group_by_overloads(methods: list[Arc56Method]) -> Iterable[list[Arc56Method]]:
    result: dict[str, list[Arc56Method]] = {}
    for method in methods:
        result.setdefault(method.name, []).append(method)
    return result.values()


def use_method_name(method: Arc56Method) -> str:
    return method.name


def use_method_signature(method: Arc56Method) -> str:
    abi_method = method.to_abi_method()
    return abi_method.get_signature().replace("(", "_").replace(")", "_").replace(",", "_")


def find_naming_strategy(methods: list[Arc56Method]) -> Callable[[Arc56Method], str]:
    if len(methods) == 1:
        return use_method_name
    return use_method_signature


def process_struct_field(  # noqa: PLR0913
    field_def: StructField,
    used_module_symbols: set[str],
    parent_name: str = "",
    io_type: utils.IOType = utils.IOType.OUTPUT,
    structs: dict[str, "ABIStruct"] | None = None,
    sanitizer: utils.Sanitizer | None = None,
) -> ABIStructField:
    """Process a struct field, handling nested structures"""
    field_name = field_def.name
    field_type = field_def.type

    # Implicit nested structs
    if isinstance(field_type, list):  # Nested struct
        sanitizer = sanitizer or utils.get_sanitizer(preserve_names=False)
        parent_python_type = sanitizer.make_safe_type_identifier(f"{parent_name}_{field_name}")
        nested_fields = [
            process_struct_field(f, used_module_symbols, parent_python_type, io_type, structs) for f in field_type
        ]
        return ABIStructField(
            name=field_name,
            abi_type=nested_fields,
            python_type=parent_python_type,
            is_nested=True,
            is_implicit=True,
        )
    # Structs referenced by name
    elif isinstance(field_type, str) and structs and field_type in structs:
        return ABIStructField(
            name=field_name,
            abi_type=field_type,
            python_type=structs[field_type].struct_class_name,
            is_nested=True,
            is_implicit=False,
        )
    else:  # Regular field
        return ABIStructField(
            name=field_name,
            abi_type=field_type,
            python_type=utils.map_abi_type_to_python(field_type, io_type),
            is_nested=False,
            is_implicit=False,
        )


def process_struct(  # noqa: PLR0913
    struct_name: str,
    struct_def: list[StructField],
    used_module_symbols: set[str],
    io_type: utils.IOType = utils.IOType.OUTPUT,
    structs: dict[str, "ABIStruct"] | None = None,
    sanitizer: utils.Sanitizer | None = None,
) -> ABIStruct:
    """Process a struct definition, including nested structs"""
    sanitized_name = utils.get_struct_name(struct_name)

    struct_class_name = utils.get_unique_symbol_by_incrementing(
        used_module_symbols, utils.get_class_name(sanitized_name), sanitizer=sanitizer
    )

    fields = [
        process_struct_field(field, used_module_symbols, struct_class_name, io_type, structs) for field in struct_def
    ]

    return ABIStruct(
        abi_name=struct_name,  # Keep original name for reference
        struct_class_name=struct_class_name,
        fields=fields,
    )


def get_all_structs(  # noqa: C901
    app_spec: Arc56Contract,
    used_module_symbols: set[str],
    sanitizer: utils.Sanitizer | None = None,
) -> dict[str, ABIStruct]:
    """Extract all structs from app spec, whether used in methods or not"""
    flat_structs: dict[str, ABIStruct] = _flatten_structs_from_spec(app_spec, used_module_symbols)
    structs: dict[str, ABIStruct] = copy.deepcopy(flat_structs)

    def get_or_create_struct(struct_name: str, io_type: utils.IOType = utils.IOType.OUTPUT) -> ABIStruct:
        if struct_name not in structs:
            if struct_name not in app_spec.structs:
                raise ValueError(f"Referenced struct {struct_name} not found in app spec")
            struct_def = app_spec.structs[struct_name]
            abi_struct = process_struct(struct_name, struct_def, used_module_symbols, io_type, structs, sanitizer)
            structs[struct_name] = abi_struct
        return structs[struct_name]

    # Process nested structs in struct fields resolved from app_spec
    sanitizer = sanitizer or utils.get_sanitizer(preserve_names=False)
    for struct in flat_structs.values():
        for field in struct.fields:
            if field.is_nested and field.is_implicit and isinstance(field.abi_type, list):
                name_identifier = sanitizer.make_safe_type_identifier(f"{struct.abi_name}_{field.name}")
                nested_struct = ABIStruct(
                    abi_name=name_identifier,
                    struct_class_name=name_identifier,
                    fields=field.abi_type,
                )
                structs[nested_struct.abi_name] = nested_struct

    # Process structs from global/local/box maps
    for maps in (app_spec.state.maps.global_state, app_spec.state.maps.local_state, app_spec.state.maps.box):
        for map_info in maps.values():
            if map_info.value_type in app_spec.structs:
                get_or_create_struct(map_info.value_type)
            if map_info.key_type in app_spec.structs:
                get_or_create_struct(map_info.key_type, utils.IOType.INPUT)

    # Process structs from state keys
    for keys in (app_spec.state.keys.global_state, app_spec.state.keys.local_state, app_spec.state.keys.box):
        for key_info in keys.values():
            if key_info.value_type in app_spec.structs:
                get_or_create_struct(key_info.value_type)
            if key_info.key_type in app_spec.structs:
                get_or_create_struct(key_info.key_type, utils.IOType.INPUT)

    return dict(sorted(structs.items(), key=lambda x: x[0]))


def get_contract_methods(
    app_spec: Arc56Contract,
    structs: dict[str, ABIStruct],
    used_module_symbols: set[str],
    used_client_symbols: set[str],
) -> ContractMethods:
    result = ContractMethods()

    def get_type_for_value(value_type: str, io_type: utils.IOType = utils.IOType.OUTPUT) -> str:
        """Helper to get Python type for a value, handling struct references"""
        if value_type in structs:
            return structs[value_type].struct_class_name
        return utils.map_abi_type_to_python(value_type, io_type)

    # Handle bare actions
    if app_spec.bare_actions:
        result.add_method(None, app_spec.bare_actions.call, app_spec.bare_actions.create)

    # Group methods by name to handle overloads
    methods_by_name: dict[str, list[Arc56Method]] = {}
    for method in app_spec.methods:
        methods_by_name.setdefault(method.name, []).append(method)

    for methods in methods_by_name.values():
        naming_strategy = find_naming_strategy(methods)
        for method in methods:
            method_name = naming_strategy(method)
            args_class_name = utils.get_unique_symbol_by_incrementing(
                used_module_symbols,
                utils.get_class_name(method_name, "args"),
            )

            # Process method parameters
            parameter_type_map: dict[str, str] = {}
            method_structs: list[ABIStruct] = []
            result_struct: ABIStruct | None = None

            # Handle return struct if it exists
            if method.returns.struct and method.returns.struct in structs:
                result_struct = structs[method.returns.struct]

            # Handle argument structs
            for arg in method.args:
                if arg.struct and arg.struct in structs:
                    abi_struct = structs[arg.struct]
                    method_structs.append(abi_struct)
                    parameter_type_map[arg.name or f"arg{len(parameter_type_map)}"] = abi_struct.struct_class_name

            # Create ABIContractMethod
            abi = ABIContractMethod(
                method=method.to_abi_method(),
                readonly=method.readonly,
                abi_type=method.returns.type,
                python_type=result_struct.struct_class_name
                if result_struct
                else get_type_for_value(method.returns.type),
                result_struct=result_struct,
                structs=method_structs,
                args=[
                    ContractArg(
                        name=arg.name or f"arg{idx}",
                        abi_type=arg.type,
                        python_type=parameter_type_map.get(arg.name or f"arg{idx}")
                        or get_type_for_value(arg.type, utils.IOType.INPUT),
                        desc=arg.desc,
                        has_default=arg.default_value is not None,
                    )
                    for idx, arg in enumerate(method.args)
                ],
                args_class_name=args_class_name,
                deploy_args_class_name=f"Deploy[{args_class_name}]",
                deploy_create_args_class_name=f"DeployCreate[{args_class_name}]",
                client_method_name=utils.get_unique_symbol_by_incrementing(
                    used_client_symbols, utils.get_method_name(method_name)
                ),
            )

            # Get method actions
            result.add_method(abi, method.actions.call or [], method.actions.create or [])

    return result


def load_from_json(path: Path) -> Arc56Contract:
    try:
        raw_json = path.read_text()

        if "contract" in json.loads(raw_json):
            arc32 = Arc32Contract.from_json(raw_json)
            return Arc56Contract.from_arc32(arc32)
        else:
            return Arc56Contract.from_json(raw_json)
    except Exception as ex:
        raise ValueError("Invalid application.json") from ex


def _map_enum_to_property(enum_value: str) -> str:
    """Maps Arc56 enum values to property names.

    For example:
    - DeleteApplication -> delete_application
    - NoOp -> no_op
    - OptIn -> opt_in
    """
    result = ""
    for i, char in enumerate(enum_value):
        if i > 0 and char.isupper():
            result += "_"
        result += char.lower()
    return result


def _flatten_structs_from_spec(app_spec: Arc56Contract, used_module_symbols: set[str]) -> dict[str, ABIStruct]:
    structs: dict[str, ABIStruct] = {}
    unprocessed_structs = set(app_spec.structs.keys())

    def _get_struct_dependencies(
        struct_def: list[StructField], all_struct_defs: dict[str, list[StructField]]
    ) -> set[str]:
        """Get names of structs referenced by this struct definition"""
        deps = set()
        for field in struct_def:
            if isinstance(field.type, list):
                continue
            if field.type in all_struct_defs:
                deps.add(field.type)
        return deps

    while unprocessed_structs:
        # Find structs with all dependencies resolved
        ready = {
            name
            for name in unprocessed_structs
            if all(dep in structs for dep in _get_struct_dependencies(app_spec.structs[name], app_spec.structs))
        }
        if not ready:
            # Circular dependency or missing struct, process alphabetically as fallback
            ready = {next(iter(unprocessed_structs))}

        for struct_name in ready:
            struct_def = app_spec.structs[struct_name]
            abi_struct = process_struct(
                struct_name=struct_name,
                struct_def=struct_def,
                used_module_symbols=used_module_symbols,
                structs=structs,  # Pass existing structs (dependencies)
                io_type=utils.IOType.OUTPUT,
            )
            if struct_name not in structs:
                structs[struct_name] = abi_struct
                unprocessed_structs.remove(struct_name)
            else:
                raise ValueError(f"Duplicate struct definition {struct_name}")

    return structs
