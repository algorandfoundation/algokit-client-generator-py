import base64
import math
import random

import algokit_utils
import algosdk
import pytest
from algokit_utils import Account
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionWithSigner
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from nacl.signing import SigningKey

from examples.voting.client_generated import CreateArgs, DeployCreate_CreateArgs, VotingRoundAppClient

NUM_QUESTIONS = 10


@pytest.fixture()
def create_args(algod_client: AlgodClient, voter: tuple[Account, bytes]) -> CreateArgs:
    quorum = math.ceil(random.randint(1, 9) * 1000)
    question_counts = [1] * NUM_QUESTIONS

    health = algod_client.status()
    assert isinstance(health, dict)
    response = algod_client.block_info(health["last-round"])
    assert isinstance(response, dict)
    block = response["block"]
    block_ts = block["ts"]

    return CreateArgs(
        vote_id="1",
        metadata_ipfs_cid="cid",
        start_time=int(block_ts),
        end_time=int(block_ts) + 1000,
        quorum=quorum,
        snapshot_public_key=algosdk.encoding.decode_address(voter[0].address),
        nft_image_url="ipfs://cid",
        option_counts=question_counts,
    )


@pytest.fixture()
def deploy_create_args(algod_client: AlgodClient, create_args: CreateArgs) -> DeployCreate_CreateArgs:
    sp = algod_client.suggested_params()
    sp.fee = algosdk.util.algos_to_microalgos(4)
    sp.flat_fee = True
    return DeployCreate_CreateArgs(args=create_args, suggested_params=sp)


@pytest.fixture()
def deploy_voting_client(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    new_account: Account,
    deploy_create_args: DeployCreate_CreateArgs,
) -> VotingRoundAppClient:
    algokit_utils.transfer(
        client=algod_client,
        parameters=algokit_utils.TransferParameters(
            from_account=algokit_utils.get_localnet_default_account(algod_client),
            to_address=new_account.address,
            micro_algos=algosdk.util.algos_to_microalgos(100000),
        ),
    )

    client = VotingRoundAppClient(algod_client=algod_client, indexer_client=indexer_client, creator=new_account)
    client.deploy(allow_delete=True, create_args=deploy_create_args)

    return client


@pytest.fixture()
def voter(algod_client: AlgodClient) -> tuple[Account, bytes]:
    voter = algosdk.account.generate_account()
    voter_account = Account(private_key=voter[0], address=voter[1])
    public_key = algosdk.encoding.decode_address(voter[1])
    private_key = base64.b64decode(voter[0])
    signing_key = SigningKey(private_key[: algosdk.constants.key_len_bytes])
    signed = signing_key.sign(public_key)
    signature = signed.signature
    algokit_utils.transfer(
        client=algod_client,
        parameters=algokit_utils.TransferParameters(
            from_account=algokit_utils.get_localnet_default_account(algod_client),
            to_address=voter_account.address,
            micro_algos=algosdk.util.algos_to_microalgos(10),
        ),
    )
    return voter_account, signature


def test_get_preconditions(
    deploy_voting_client: VotingRoundAppClient, algod_client: AlgodClient, voter: tuple[Account, bytes]
) -> None:
    signature = voter[1]
    sp = algod_client.suggested_params()
    sp.fee = 12000
    sp.flat_fee = True
    response = deploy_voting_client.get_preconditions(
        signature=signature,
        transaction_parameters=algokit_utils.TransactionParameters(
            boxes=[(0, algosdk.encoding.decode_address(voter[0].address))],
            suggested_params=sp,
            sender=voter[0].address,
            signer=AccountTransactionSigner(voter[0].private_key),
        ),
    )
    assert len(response.return_value) == 4


@pytest.fixture()
def bootstrap_response(
    deploy_voting_client: VotingRoundAppClient, algod_client: AlgodClient
) -> algokit_utils.ABITransactionResponse:
    from_account = algokit_utils.get_localnet_default_account(algod_client)
    payment = algosdk.transaction.PaymentTxn(
        sender=from_account.address,
        receiver=deploy_voting_client.app_client.app_address,
        amt=(100000 * 2) + 1000 + 2500 + 400 * (1 + 8 * NUM_QUESTIONS),
        note=b"Bootstrap payment",
        sp=algod_client.suggested_params(),
    )
    default_signer = AccountTransactionSigner(from_account.private_key)

    return deploy_voting_client.bootstrap(
        fund_min_bal_req=TransactionWithSigner(txn=payment, signer=default_signer),
        transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")]),
    )


def test_vote(
    deploy_voting_client: VotingRoundAppClient,
    algod_client: AlgodClient,
    voter: tuple[Account, bytes],
    bootstrap_response: algokit_utils.ABITransactionResponse,
) -> None:
    # bootstrap app
    assert bootstrap_response.confirmed_round

    # vote payment
    question_counts = [0] * NUM_QUESTIONS
    payment = algosdk.transaction.PaymentTxn(
        sender=voter[0].address,
        receiver=deploy_voting_client.app_client.app_address,
        amt=400 * (32 + 2 + len(question_counts) * 1) + 2500,
        sp=deploy_voting_client.app_client.algod_client.suggested_params(),
    )
    voter_signer = AccountTransactionSigner(voter[0].private_key)
    voter_public_key = algosdk.encoding.decode_address(voter[0].address)
    fund_min_bal_req = TransactionWithSigner(payment, voter_signer)
    signature = voter[1]

    # vote fee
    sp = algod_client.suggested_params()
    sp.fee = 12000
    sp.flat_fee = True
    response = deploy_voting_client.vote(
        fund_min_bal_req=fund_min_bal_req,
        signature=signature,
        answer_ids=question_counts,
        transaction_parameters=algokit_utils.TransactionParameters(
            suggested_params=sp,
            boxes=[(0, "V"), (0, voter_public_key)],
            sender=voter[0].address,
            signer=voter_signer,
        ),
    )
    assert response.return_value is None


def test_create(
    algod_client: AlgodClient, indexer_client: IndexerClient, new_account: Account, create_args: CreateArgs
) -> None:
    voting_round_app_client = VotingRoundAppClient(
        algod_client=algod_client,
        indexer_client=indexer_client,
        creator=new_account,
        template_values={"VALUE": 1, "DELETABLE": 1},
    )

    sp = algod_client.suggested_params()
    sp.fee = algosdk.util.algos_to_microalgos(4)
    sp.flat_fee = True

    voting_round_app_client.create(
        args=create_args,
        transaction_parameters=algokit_utils.CreateTransactionParameters(suggested_params=sp),
    )

    # assert response.return_value voting_round_app_client== "Hello, World"


def test_boostrap(
    bootstrap_response: algokit_utils.ABITransactionResponse,
) -> None:
    # bootstrap app
    assert bootstrap_response.confirmed_round


def test_close(
    deploy_voting_client: VotingRoundAppClient,
    bootstrap_response: algokit_utils.ABITransactionResponse,
) -> None:
    # bootstrap app
    assert bootstrap_response.confirmed_round

    sp = deploy_voting_client.app_client.algod_client.suggested_params()
    sp.fee = algosdk.util.algos_to_microalgos(1)
    sp.flat_fee = True
    deploy_voting_client.close(
        transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")], suggested_params=sp)
    )
