# mypy: disable-error-code="no-untyped-call"
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

from examples.conftest import get_unique_name
from examples.voting.client import CreateArgs, DeployCreate, VotingPreconditions, VotingRoundAppClient

NUM_QUESTIONS = 10


@pytest.fixture(scope="session")
def create_args(algod_client: AlgodClient, voter: Account) -> CreateArgs:
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
        snapshot_public_key=voter.public_key,
        nft_image_url="ipfs://cid",
        option_counts=question_counts,
    )


@pytest.fixture()
def deploy_create_args(algod_client: AlgodClient, create_args: CreateArgs) -> DeployCreate[CreateArgs]:
    sp = algod_client.suggested_params()
    sp.fee = algosdk.util.algos_to_microalgos(4)
    sp.flat_fee = True
    return DeployCreate(args=create_args, suggested_params=sp)


@pytest.fixture()
def deploy_voting_client(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    funded_account: Account,
    deploy_create_args: DeployCreate[CreateArgs],
) -> VotingRoundAppClient:
    algokit_utils.transfer(
        client=algod_client,
        parameters=algokit_utils.TransferParameters(
            from_account=algokit_utils.get_localnet_default_account(algod_client),
            to_address=funded_account.address,
            micro_algos=algosdk.util.algos_to_microalgos(1),
        ),
    )

    client = VotingRoundAppClient(
        algod_client=algod_client, indexer_client=indexer_client, creator=funded_account, app_name=get_unique_name()
    )
    client.deploy(allow_delete=True, create_args=deploy_create_args)

    return client


@pytest.fixture(scope="session")
def voter(algod_client: AlgodClient) -> Account:
    voter = algosdk.account.generate_account()
    voter_account = Account(private_key=voter[0], address=voter[1])
    algokit_utils.transfer(
        client=algod_client,
        parameters=algokit_utils.TransferParameters(
            from_account=algokit_utils.get_localnet_default_account(algod_client),
            to_address=voter_account.address,
            micro_algos=algosdk.util.algos_to_microalgos(10),
        ),
    )
    return voter_account


@pytest.fixture(scope="session")
def voter_signature(voter: Account) -> bytes:
    private_key = base64.b64decode(voter.private_key)
    signing_key = SigningKey(private_key[: algosdk.constants.key_len_bytes])
    signed = signing_key.sign(voter.public_key)
    return signed.signature


@pytest.fixture()
def fund_min_bal_req(algod_client: AlgodClient, deploy_voting_client: VotingRoundAppClient) -> TransactionWithSigner:
    from_account = algokit_utils.get_localnet_default_account(algod_client)
    payment = algosdk.transaction.PaymentTxn(
        sender=from_account.address,
        receiver=deploy_voting_client.app_address,
        amt=(100000 * 2) + 1000 + 2500 + 400 * (1 + 8 * NUM_QUESTIONS),
        note=b"Bootstrap payment",
        sp=algod_client.suggested_params(),
    )
    return TransactionWithSigner(txn=payment, signer=from_account.signer)


@pytest.fixture()
def bootstrap_response(
    deploy_voting_client: VotingRoundAppClient,
    fund_min_bal_req: TransactionWithSigner,
) -> algokit_utils.ABITransactionResponse[None]:
    return deploy_voting_client.bootstrap(
        fund_min_bal_req=fund_min_bal_req,
        transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")]),
    )


def test_get_preconditions(
    deploy_voting_client: VotingRoundAppClient, algod_client: AlgodClient, voter: Account, voter_signature: bytes
) -> None:
    sp = algod_client.suggested_params()
    sp.fee = 12000
    sp.flat_fee = True
    response = deploy_voting_client.get_preconditions(
        signature=voter_signature,
        transaction_parameters=algokit_utils.TransactionParameters(
            boxes=[(0, voter.public_key)],
            suggested_params=sp,
            sender=voter.address,
            signer=AccountTransactionSigner(voter.private_key),
        ),
    )

    assert isinstance(response.return_value, VotingPreconditions)
    assert response.return_value.is_voting_open == 0
    assert response.return_value.has_already_voted == 0
    assert response.return_value.is_allowed_to_vote == 1


def test_vote(
    deploy_voting_client: VotingRoundAppClient,
    algod_client: AlgodClient,
    voter: Account,
    voter_signature: bytes,
    bootstrap_response: algokit_utils.ABITransactionResponse[None],
) -> None:
    # bootstrap app
    assert bootstrap_response.confirmed_round

    # vote payment
    question_counts = [0] * NUM_QUESTIONS
    payment = algosdk.transaction.PaymentTxn(
        sender=voter.address,
        receiver=deploy_voting_client.app_address,
        amt=400 * (32 + 2 + len(question_counts) * 1) + 2500,
        sp=deploy_voting_client.algod_client.suggested_params(),
    )
    fund_min_bal_req = TransactionWithSigner(payment, voter.signer)

    # vote fee
    sp = algod_client.suggested_params()
    sp.fee = 12000
    sp.flat_fee = True
    response = deploy_voting_client.vote(
        fund_min_bal_req=fund_min_bal_req,
        signature=voter_signature,
        answer_ids=question_counts,
        transaction_parameters=algokit_utils.TransactionParameters(
            suggested_params=sp,
            boxes=[(0, "V"), (0, voter.public_key)],
            sender=voter.address,
            signer=voter.signer,
        ),
    )
    assert response.return_value is None


def test_create(algod_client: AlgodClient, funded_account: Account, create_args: CreateArgs) -> None:
    voting_round_app_client = VotingRoundAppClient(
        algod_client=algod_client,
        signer=funded_account,
        template_values={"VALUE": 1, "DELETABLE": 1},
    )

    sp = algod_client.suggested_params()
    sp.fee = algosdk.util.algos_to_microalgos(4)
    sp.flat_fee = True

    response = voting_round_app_client.create_create(
        vote_id=create_args.vote_id,
        snapshot_public_key=create_args.snapshot_public_key,
        metadata_ipfs_cid=create_args.metadata_ipfs_cid,
        start_time=create_args.start_time,
        end_time=create_args.end_time,
        option_counts=create_args.option_counts,
        quorum=create_args.quorum,
        nft_image_url=create_args.nft_image_url,
        transaction_parameters=algokit_utils.CreateTransactionParameters(suggested_params=sp),
    )

    assert response.confirmed_round


def test_boostrap(
    bootstrap_response: algokit_utils.ABITransactionResponse[None],
) -> None:
    # bootstrap app
    assert bootstrap_response.confirmed_round


def test_close(
    deploy_voting_client: VotingRoundAppClient,
    bootstrap_response: algokit_utils.ABITransactionResponse[None],
) -> None:
    # bootstrap app
    assert bootstrap_response.confirmed_round

    sp = deploy_voting_client.app_client.algod_client.suggested_params()
    sp.fee = algosdk.util.algos_to_microalgos(1)
    sp.flat_fee = True
    deploy_voting_client.close(
        transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")], suggested_params=sp)
    )


def test_compose(
    algod_client: AlgodClient,
    deploy_voting_client: VotingRoundAppClient,
    fund_min_bal_req: TransactionWithSigner,
    voter: Account,
    voter_signature: bytes,
) -> None:
    sp = algod_client.suggested_params()
    sp.fee = 12000
    sp.flat_fee = True

    response = (
        deploy_voting_client.compose()
        .bootstrap(
            fund_min_bal_req=fund_min_bal_req,
            transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")]),
        )
        .get_preconditions(
            signature=voter_signature,
            transaction_parameters=algokit_utils.TransactionParameters(
                boxes=[(0, voter.public_key)],
                suggested_params=sp,
                sender=voter.address,
                signer=AccountTransactionSigner(voter.private_key),
            ),
        )
    ).execute()

    bootstrap_response, get_preconditions = response.abi_results
    assert bootstrap_response.tx_id

    assert get_preconditions.return_value[:3] == [1, 1, 0]
