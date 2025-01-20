import dataclasses
import json
import typing
from collections.abc import Callable, Iterable
from pathlib import Path

from algokit_utils.applications import Arc32Contract, Arc56Contract
from algokit_utils.applications import Method as Arc56Method
from algokit_utils.applications.app_spec.arc56 import CallEnum, CreateEnum
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
    abi_type: str
    python_type: str


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


def get_contract_methods(
    app_spec: Arc56Contract,
    used_module_symbols: set[str],
    used_client_symbols: set[str],
) -> ContractMethods:
    result = ContractMethods()

    # Handle bare actions
    if app_spec.bare_actions:
        result.add_method(None, app_spec.bare_actions.call, app_spec.bare_actions.create)

    # Group methods by name to handle overloads
    methods_by_name: dict[str, list[Arc56Method]] = {}
    for method in app_spec.methods:
        methods_by_name.setdefault(method.name, []).append(method)

    structs: dict[str, ABIStruct] = {}
    for methods in methods_by_name.values():
        naming_strategy = find_naming_strategy(methods)
        for method in methods:
            method_name = naming_strategy(method)
            args_class_name = utils.get_unique_symbol_by_incrementing(
                used_module_symbols,
                utils.get_class_name(method_name, "args"),
            )

            # Process structs
            parameter_type_map: dict[str, str] = {}
            method_structs: list[ABIStruct] = []
            result_struct: ABIStruct | None = None

            # Handle return struct if it exists
            if method.returns.struct:
                struct_name = method.returns.struct
                struct_def = app_spec.structs[struct_name]
                if struct_name not in structs:
                    struct_class_name = utils.get_unique_symbol_by_incrementing(
                        used_module_symbols, utils.get_class_name(struct_name)
                    )
                    result_struct = ABIStruct(
                        abi_name=struct_name,
                        struct_class_name=struct_class_name,
                        fields=[
                            ABIStructField(
                                name=field.name,
                                abi_type=field.type if isinstance(field.type, str) else "tuple",
                                python_type=utils.map_abi_type_to_python(
                                    field.type if isinstance(field.type, str) else "tuple"
                                ),
                            )
                            for field in struct_def
                        ],
                    )
                    structs[struct_name] = result_struct
                else:
                    result_struct = structs[struct_name]

            # Handle argument structs
            for arg in method.args:
                if arg.struct:
                    struct_name = arg.struct
                    struct_def = app_spec.structs[struct_name]
                    if struct_name not in structs:
                        struct_class_name = utils.get_unique_symbol_by_incrementing(
                            used_module_symbols, utils.get_class_name(struct_name)
                        )
                        abi_struct = ABIStruct(
                            abi_name=struct_name,
                            struct_class_name=struct_class_name,
                            fields=[
                                ABIStructField(
                                    name=field.name,
                                    abi_type=field.type if isinstance(field.type, str) else "tuple",
                                    python_type=utils.map_abi_type_to_python(
                                        field.type if isinstance(field.type, str) else "tuple"
                                    ),
                                )
                                for field in struct_def
                            ],
                        )
                        structs[struct_name] = abi_struct
                        method_structs.append(abi_struct)
                        parameter_type_map[arg.name or f"arg{len(parameter_type_map)}"] = struct_class_name
                    else:
                        method_structs.append(structs[struct_name])
                        parameter_type_map[arg.name or f"arg{len(parameter_type_map)}"] = structs[
                            struct_name
                        ].struct_class_name

            # Create ABIContractMethod
            abi = ABIContractMethod(
                method=method.to_abi_method(),
                readonly=method.readonly,
                abi_type=method.returns.type,
                python_type=result_struct.struct_class_name
                if result_struct
                else utils.map_abi_type_to_python(method.returns.type),
                result_struct=result_struct,
                structs=method_structs,
                args=[
                    ContractArg(
                        name=arg.name or f"arg{idx}",
                        abi_type=arg.type,
                        python_type=parameter_type_map.get(arg.name or f"arg{idx}")
                        or utils.map_abi_type_to_python(arg.type),
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
