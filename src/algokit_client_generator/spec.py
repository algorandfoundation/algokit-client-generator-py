import dataclasses
import typing
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

import algokit_utils
from algokit_abi import abi, arc56

from algokit_client_generator import utils


@dataclasses.dataclass(kw_only=True)
class ContractArg:
    name: str
    abi_type: abi.ABIType | arc56.ReferenceType | arc56.TransactionType
    python_type: str
    desc: str | None
    has_default: bool = False


@dataclasses.dataclass(kw_only=True)
class ABIContractMethod:
    method: arc56.Method
    readonly: bool | None
    abi_type: abi.ABIType | arc56.VoidType
    python_type: str
    args: list[ContractArg]
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
        self,
        abi: ABIContractMethod | None,
        call_actions: Sequence[arc56.CallEnum],
        create_actions: Sequence[arc56.CreateEnum],
    ) -> None:
        # Handle call actions
        for action in call_actions:
            action_name = _map_enum_to_property(action.value if isinstance(action, arc56.CallEnum) else action)
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
                    _map_enum_to_property(action.value if isinstance(action, arc56.CreateEnum) else action)
                    for action in create_actions
                ],
            )
            self.create.append(contract_method)


def group_by_overloads(methods: list[arc56.Method]) -> Iterable[list[arc56.Method]]:
    result: dict[str, list[arc56.Method]] = {}
    for method in methods:
        result.setdefault(method.name, []).append(method)
    return result.values()


def use_method_name(method: arc56.Method) -> str:
    return method.name


def use_method_signature(method: arc56.Method) -> str:
    return method.signature.replace("(", "_").replace(")", "_").replace(",", "_")


def find_naming_strategy(methods: list[arc56.Method]) -> Callable[[arc56.Method], str]:
    if len(methods) == 1:
        return use_method_name
    return use_method_signature


def get_contract_methods(
    app_spec: arc56.Arc56Contract,
    used_module_symbols: set[str],
    used_client_symbols: set[str],
) -> ContractMethods:
    result = ContractMethods()

    # Handle bare actions
    if app_spec.bare_actions:
        result.add_method(None, app_spec.bare_actions.call, app_spec.bare_actions.create)

    # Group methods by name to handle overloads
    methods_by_name: dict[str, list[arc56.Method]] = {}
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

            # Create ABIContractMethod
            abi_method = ABIContractMethod(
                method=method,
                readonly=method.readonly,
                abi_type=method.returns.type,
                python_type=utils.map_arc56_type_to_python(method.returns.type, utils.IOType.OUTPUT),
                args=[
                    ContractArg(
                        name=arg.name or f"arg{idx}",
                        abi_type=arg.type,
                        python_type=utils.map_arc56_type_to_python(arg.type, utils.IOType.INPUT),
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
            result.add_method(abi_method, method.actions.call or [], method.actions.create or [])

    return result


def load_from_json(path: Path) -> arc56.Arc56Contract:
    try:
        raw_json = path.read_text()
        return algokit_utils.AppClient.normalise_app_spec(raw_json)
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
