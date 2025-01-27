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


@dataclasses.dataclass(kw_only=True)
class ABIStruct:
    abi_name: str
    struct_class_name: str
    fields: list[ABIStructField]

    def get_python_type_hints(self) -> str:
        """Generate Python type hints for the struct"""
        field_types = []
        for field in self.fields:
            if field.is_nested:
                # For nested structs, reference the generated class name
                assert isinstance(field.abi_type, list)
                nested_struct = ABIStruct(
                    abi_name=f"{self.abi_name}_{field.name}",
                    struct_class_name=f"{self.struct_class_name}{field.name.title()}",
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
                field_types.append(f"{field.name}: {nested_struct.struct_class_name}")
            else:
                field_types.append(f"{field.name}: {field.python_type}")
        return ", ".join(field_types)


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


def process_struct_field(
    field_def: StructField,
    used_module_symbols: set[str],
    parent_name: str = "",
    io_type: utils.IOType = utils.IOType.OUTPUT,
) -> ABIStructField:
    """Process a struct field, handling nested structures"""
    field_name = field_def.name
    field_type = field_def.type

    if isinstance(field_type, list):  # Nested struct
        nested_fields = [
            process_struct_field(f, used_module_symbols, f"{parent_name}_{field_name}", io_type) for f in field_type
        ]
        return ABIStructField(
            name=field_name, abi_type=nested_fields, python_type=f"{parent_name}{field_name.title()}", is_nested=True
        )
    else:  # Regular field
        return ABIStructField(
            name=field_name,
            abi_type=field_type,
            python_type=utils.map_abi_type_to_python(field_type, io_type),
            is_nested=False,
        )


def process_struct(
    struct_name: str,
    struct_def: list[StructField],
    used_module_symbols: set[str],
    io_type: utils.IOType = utils.IOType.OUTPUT,
) -> ABIStruct:
    """Process a struct definition, including nested structs"""
    sanitized_name = utils.get_struct_name(struct_name)

    struct_class_name = utils.get_unique_symbol_by_incrementing(
        used_module_symbols, utils.get_class_name(sanitized_name)
    )

    fields = [process_struct_field(field, used_module_symbols, struct_class_name, io_type) for field in struct_def]

    return ABIStruct(
        abi_name=struct_name,  # Keep original name for reference
        struct_class_name=struct_class_name,
        fields=fields,
    )


def get_all_structs(  # noqa: C901
    app_spec: Arc56Contract,
    used_module_symbols: set[str],
) -> dict[str, ABIStruct]:
    """Extract all structs from app spec, whether used in methods or not"""
    structs: dict[str, ABIStruct] = {}

    def get_or_create_struct(struct_name: str, io_type: utils.IOType = utils.IOType.OUTPUT) -> ABIStruct:
        if struct_name not in structs:
            if struct_name not in app_spec.structs:
                raise ValueError(f"Referenced struct {struct_name} not found in app spec")
            struct_def = app_spec.structs[struct_name]
            abi_struct = process_struct(struct_name, struct_def, used_module_symbols, io_type)
            structs[struct_name] = abi_struct
        return structs[struct_name]

    # Process all structs defined in app_spec
    for struct_name in app_spec.structs:
        get_or_create_struct(struct_name)

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

    return structs


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
