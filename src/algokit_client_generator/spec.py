import dataclasses
import typing
from collections.abc import Callable, Iterable

from algokit_utils import ApplicationSpecification, CallConfig, MethodConfigDict, MethodHints, OnCompleteActionName
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
    hints: MethodHints
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
    on_complete: list[OnCompleteActionName]
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

    def add_method(self, abi: ABIContractMethod | None, method_config: MethodConfigDict) -> None:
        create_on_completes = []
        for on_complete, call_config in method_config.items():
            if call_config & CallConfig.CALL != CallConfig.NEVER:
                collection = getattr(self, on_complete)
                contract_method = ContractMethod(
                    abi=abi,
                    call_config="call",
                    on_complete=[on_complete],
                )
                collection.append(contract_method)
            if call_config & CallConfig.CREATE != CallConfig.NEVER:
                create_on_completes.append(on_complete)

        if create_on_completes:
            contract_method = ContractMethod(
                abi=abi,
                call_config="create",
                on_complete=create_on_completes,
            )
            self.create.append(contract_method)


def group_by_overloads(methods: list[Method]) -> Iterable[list[Method]]:
    result: dict[str, list[Method]] = {}
    for method in methods:
        result.setdefault(method.name, []).append(method)
    return result.values()


def use_method_name(method: Method) -> str:
    return method.name


def use_method_signature(method: Method) -> str:
    return method.get_signature().replace("(", "_").replace(")", "_").replace(",", "_")


def find_naming_strategy(methods: list[Method]) -> Callable[[Method], str]:
    if len(methods) == 1:
        return use_method_name
    return use_method_signature


def get_contract_methods(
    app_spec: ApplicationSpecification, used_module_symbols: set[str], used_client_symbols: set[str]
) -> ContractMethods:
    result = ContractMethods()
    result.add_method(None, app_spec.bare_call_config)

    structs: dict[str, ABIStruct] = {}
    for methods in group_by_overloads(app_spec.contract.methods):
        naming_strategy = find_naming_strategy(methods)
        for method in methods:
            method_name = naming_strategy(method)
            hints = app_spec.hints[method.get_signature()]
            args_class_name = utils.get_unique_symbol_by_incrementing(
                used_module_symbols,
                utils.get_class_name(method_name, "args"),
            )

            parameter_type_map: dict[str, str] = {}
            method_structs: list[ABIStruct] = []
            result_struct: ABIStruct | None = None
            for parameter, struct in hints.structs.items():
                abi_name = struct["name"]
                abi_struct = structs.get(abi_name)
                if not abi_struct:
                    # TODO: check for collisions where the same name refers to different structures
                    struct_class_name = utils.get_unique_symbol_by_incrementing(
                        used_module_symbols, utils.get_class_name(abi_name)
                    )
                    abi_struct = ABIStruct(
                        abi_name=abi_name,
                        struct_class_name=struct_class_name,
                        fields=[
                            ABIStructField(
                                name=name,
                                abi_type=abi_type,
                                python_type=utils.map_abi_type_to_python(abi_type),
                            )
                            # TODO: nested structs?!
                            for name, abi_type in struct["elements"]
                        ],
                    )
                structs[abi_name] = abi_struct
                if parameter == "output":  # TODO: check return signature
                    result_struct = abi_struct
                parameter_type_map[parameter] = abi_struct.struct_class_name
                method_structs.append(abi_struct)

            abi = ABIContractMethod(
                method=method,
                hints=hints,
                abi_type=str(method.returns),
                python_type=result_struct.struct_class_name
                if result_struct
                else utils.map_abi_type_to_python(str(method.returns)),
                result_struct=result_struct,
                structs=method_structs,
                args=[
                    ContractArg(
                        name=arg.name or f"arg{idx}",
                        abi_type=str(arg.type),
                        python_type=parameter_type_map[arg.name]
                        if arg.name in parameter_type_map
                        else utils.map_abi_type_to_python(str(arg.type)),
                        desc=arg.desc,
                        has_default=arg.name in hints.default_arguments,
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
            result.add_method(abi, hints.call_config)

    return result
