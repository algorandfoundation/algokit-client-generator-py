import base64
import algokit_utils
import pytest
from algokit_utils.models import AlgoAmount
from algokit_utils.protocols import AlgorandClientProtocol
from algokit_utils.transactions import PaymentParams

from examples.nested.client import AddArgs, GetPayTxnAmountArgs, NestedContractFactory, NestedMethodCallArgs


@pytest.fixture
def default_deployer(algorand: AlgorandClientProtocol) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def nested_factory(algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> NestedContractFactory:
    return algorand.client.get_typed_app_factory(NestedContractFactory, default_sender=default_deployer.address)


def test_nested_method_call_with_obj_args_without_pay_txn(nested_factory: NestedContractFactory, algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> None:
    client, _ = nested_factory.deploy()
    pay_txn = algorand.create_transaction.payment(PaymentParams(sender=default_deployer.address, receiver=default_deployer.address, amount=AlgoAmount.from_algo(0)))
    nested_app_call = client.params.get_pay_txn_amount(args=GetPayTxnAmountArgs(pay_txn=pay_txn))
    response = client.send.nested_method_call(args=NestedMethodCallArgs(_='test', method_call=nested_app_call))
    assert response.abi_return 
    assert base64.b32encode(bytearray(response.abi_return)).decode()[:52] == response.tx_ids[1]


def test_nested_method_call_with_tuple_args_without_pay_txn(nested_factory: NestedContractFactory, algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> None:
    client, _ = nested_factory.deploy()
    pay_txn = algorand.create_transaction.payment(PaymentParams(sender=default_deployer.address, receiver=default_deployer.address, amount=AlgoAmount.from_algo(0)))
    nested_app_call = client.params.get_pay_txn_amount(args=GetPayTxnAmountArgs(pay_txn=pay_txn))
    response = client.send.nested_method_call(args=('test', None, nested_app_call))
    assert response.abi_return 
    assert base64.b32encode(bytearray(response.abi_return)).decode()[:52] == response.tx_ids[1]

def test_nested_method_call_with_obj_args_with_pay_txn(nested_factory: NestedContractFactory, algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> None:
    client, _ = nested_factory.deploy()
    pay_txn = algorand.create_transaction.payment(PaymentParams(sender=default_deployer.address, receiver=default_deployer.address, amount=AlgoAmount.from_algo(0)))
    nested_app_call = client.params.add(args=AddArgs(a=1, b=2))
    response = client.send.nested_method_call(args=NestedMethodCallArgs(_='test', _pay_txn=pay_txn, method_call=nested_app_call))
    assert response.abi_return 
    assert base64.b32encode(bytearray(response.abi_return)).decode()[:52] == response.tx_ids[1]


def test_nested_method_call_with_tuple_args_with_pay_txn(nested_factory: NestedContractFactory, algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> None:
    client, _ = nested_factory.deploy()
    pay_txn = algorand.create_transaction.payment(PaymentParams(sender=default_deployer.address, receiver=default_deployer.address, amount=AlgoAmount.from_algo(0)))
    nested_app_call = client.params.add(args=AddArgs(a=1, b=2))
    response = client.send.nested_method_call(args=('test', pay_txn, nested_app_call))
    assert response.abi_return 
    assert base64.b32encode(bytearray(response.abi_return)).decode()[:52] == response.tx_ids[1]
