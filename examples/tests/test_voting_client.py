# mypy: disable-error-code="call-overload"

import base64
import random
import uuid
from dataclasses import dataclass

import algokit_utils
import algokit_utils.applications
import algokit_utils.transactions
import algosdk
import pytest
from algokit_utils import AlgorandClient, CommonAppCallCreateParams, CommonAppCallParams
from algokit_utils.applications import FundAppAccountParams, OnUpdate
from algokit_utils.models import AlgoAmount
from algosdk.v2client.algod import AlgodClient
from nacl.signing import SigningKey

from examples.smart_contracts.artifacts.voting_round.voting_round_client import (
    BootstrapArgs,
    CreateArgs,
    GetPreconditionsArgs,
    VoteArgs,
    VotingRoundClient,
    VotingRoundFactory,
)


@pytest.fixture
def default_deployer(algorand: AlgorandClient) -> algokit_utils.SigningAccount:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def voting_factory(algorand: AlgorandClient, default_deployer: algokit_utils.SigningAccount) -> VotingRoundFactory:
    return algorand.client.get_typed_app_factory(VotingRoundFactory, default_sender=default_deployer.address)


@pytest.fixture
def voting_app_client(voting_factory: VotingRoundFactory) -> VotingRoundClient:
    client, _ = voting_factory.deploy(
        compilation_params={
            "deploy_time_params": {"VALUE": 1},
            "deletable": True,
            "updatable": True,
        },
        on_update=OnUpdate.UpdateApp,
    )
    return client


@dataclass
class RandomVotingAppDeployment:
    algorand: AlgorandClient
    algod: AlgodClient
    client: VotingRoundClient
    total_question_options: int
    test_account: algokit_utils.SigningAccount
    private_key: bytes
    quorum: int
    question_count: int
    question_counts: list[int]
    public_key: bytes
    current_time: int
    signature: bytes
    random_answer_ids: list[int]


@pytest.fixture
def random_voting_round_app(
    voting_factory: VotingRoundFactory, default_deployer: algokit_utils.SigningAccount
) -> RandomVotingAppDeployment:
    algod = voting_factory.algorand.client.algod
    status = algod.status()
    last_round = status["last-round"]
    last_round = algod.block_info(last_round)
    current_time = last_round["block"]["ts"]

    voter = default_deployer
    quorum = random.randint(1, 1000)
    question_count = random.randint(1, 10)
    question_counts = [random.randint(1, 10) for _ in range(question_count)]
    total_question_options = sum(question_counts)

    private_key = base64.b64decode(voter.private_key)
    public_key = voter.public_key

    client, result = voting_factory.send.create.create(
        args=CreateArgs(
            vote_id=f"V{uuid.uuid4().hex.upper()}",
            metadata_ipfs_cid="cid",
            start_time=current_time,
            end_time=current_time + 1000,
            quorum=quorum,
            snapshot_public_key=public_key,
            nft_image_url="ipfs://cid",
            option_counts=question_counts,
        ),
        params=CommonAppCallCreateParams(static_fee=AlgoAmount.from_micro_algo(1000 + 1000 * 4)),
        compilation_params={
            "deletable": True,
        },
    )
    assert result.abi_return is None

    random_answer_ids = [random.randint(0, question_counts[i] - 1) for i in range(question_count)]
    signing_key = SigningKey(private_key[: algosdk.constants.key_len_bytes])
    signed = signing_key.sign(voter.public_key)
    signature = signed.signature

    return RandomVotingAppDeployment(
        algorand=voting_factory.algorand,
        algod=algod,
        client=client,
        total_question_options=total_question_options,
        test_account=default_deployer,
        private_key=private_key,
        quorum=quorum,
        question_count=question_count,
        question_counts=question_counts,
        public_key=public_key,
        current_time=current_time,
        signature=signature,
        random_answer_ids=random_answer_ids,
    )


def test_struct_mapping(random_voting_round_app: RandomVotingAppDeployment) -> None:
    client = random_voting_round_app.client
    test_account = random_voting_round_app.test_account
    total_question_options = random_voting_round_app.total_question_options
    signature = random_voting_round_app.signature

    input_params = algokit_utils.applications.FundAppAccountParams(
        amount=AlgoAmount.from_micro_algo(200_000 + 1_000 + 2_500 + 400 * (1 + 8 * total_question_options))
    )
    client.create_transaction.bootstrap(
        args=BootstrapArgs(fund_min_bal_req=client.app_client.create_transaction.fund_app_account(params=input_params)),
        params=CommonAppCallParams(
            box_references=["V"],
            static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 4),
        ),
    )

    preconditions_result = client.send.get_preconditions(
        args=GetPreconditionsArgs(signature=signature),
        params=CommonAppCallParams(
            box_references=[test_account.public_key],
            static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
        ),
    )

    assert preconditions_result.abi_return is not None
    assert preconditions_result.abi_return.is_allowed_to_vote == 1
    assert preconditions_result.abi_return.has_already_voted == 0
    assert preconditions_result.abi_return.is_voting_open == 0


def test_global_state(random_voting_round_app: RandomVotingAppDeployment) -> None:
    client = random_voting_round_app.client
    test_account = random_voting_round_app.test_account
    question_counts = random_voting_round_app.question_counts
    total_question_options = random_voting_round_app.total_question_options
    state = client.state.global_state.get_all()

    assert state["snapshot_public_key"] == test_account.public_key
    assert state["metadata_ipfs_cid"] == b"cid"
    assert state["start_time"] == random_voting_round_app.current_time
    assert state["end_time"] == random_voting_round_app.current_time + 1000
    assert state["quorum"] == random_voting_round_app.quorum
    assert state["is_bootstrapped"] == 0
    assert state["voter_count"] == 0
    assert state["nft_image_url"] == b"ipfs://cid"
    assert state["nft_asset_id"] == 0
    assert state["total_options"] == total_question_options
    assert algosdk.abi.ABIType.from_string("uint8[]").decode(state["option_counts"]) == question_counts


def test_works_with_separate_transactions(
    random_voting_round_app: RandomVotingAppDeployment,
) -> None:
    client = random_voting_round_app.client
    test_account = random_voting_round_app.test_account
    signature = random_voting_round_app.signature

    preconditions_result = client.send.get_preconditions(
        args=GetPreconditionsArgs(signature=signature),
        params=CommonAppCallParams(
            box_references=[test_account.address],
            static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
        ),
    )

    assert preconditions_result.abi_return is not None
    assert preconditions_result.abi_return.is_allowed_to_vote == 1
    assert preconditions_result.abi_return.has_already_voted == 0

    input_params = algokit_utils.applications.FundAppAccountParams(
        amount=AlgoAmount.from_micro_algo(
            200_000 + 1_000 + 2_500 + 400 * (1 + 8 * random_voting_round_app.total_question_options)
        )
    )
    client.send.bootstrap(
        args=BootstrapArgs(fund_min_bal_req=client.app_client.create_transaction.fund_app_account(params=input_params)),
        params=CommonAppCallParams(
            box_references=["V"],
            static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 4),
        ),
    )

    input_params = algokit_utils.applications.FundAppAccountParams(
        amount=AlgoAmount.from_micro_algo(400 * (32 + 2 + len(random_voting_round_app.random_answer_ids)) + 2_500)
    )
    client.send.vote(
        args=VoteArgs(
            answer_ids=random_voting_round_app.random_answer_ids,
            fund_min_bal_req=client.app_client.create_transaction.fund_app_account(params=input_params),
            signature=signature,
        ),
        params=CommonAppCallParams(
            box_references=["V", test_account.public_key],
            static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 16),
        ),
    )

    preconditions_result_after = client.send.get_preconditions(
        args=GetPreconditionsArgs(signature=signature),
        params=CommonAppCallParams(
            box_references=[test_account.public_key],
            static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
        ),
    )

    assert preconditions_result_after.abi_return is not None
    assert preconditions_result_after.abi_return.has_already_voted == 1


def test_it_works_with_manual_use_of_the_transaction_composer(
    random_voting_round_app: RandomVotingAppDeployment,
) -> None:
    client = random_voting_round_app.client
    test_account = random_voting_round_app.test_account
    signature = random_voting_round_app.signature

    params_1 = FundAppAccountParams(
        amount=AlgoAmount.from_micro_algo(
            200_000 + 1_000 + 2_500 + 400 * (1 + 8 * random_voting_round_app.total_question_options)
        )
    )
    params_2 = FundAppAccountParams(
        amount=AlgoAmount.from_micro_algo(400 * (32 + 2 + len(random_voting_round_app.random_answer_ids)) + 2_500)
    )

    result = (
        random_voting_round_app.algorand.new_group()
        .add_app_call_method_call(
            client.params.get_preconditions(
                args=GetPreconditionsArgs(signature=signature),
                params=CommonAppCallParams(
                    static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
                    box_references=[test_account.address],
                ),
            )
        )
        .add_app_call_method_call(
            client.params.bootstrap(
                args=BootstrapArgs(
                    fund_min_bal_req=client.app_client.create_transaction.fund_app_account(params=params_1)
                ),
                params=CommonAppCallParams(
                    box_references=["V"],
                    static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 4),
                ),
            )
        )
        .add_app_call_method_call(
            client.params.vote(
                args=VoteArgs(
                    answer_ids=random_voting_round_app.random_answer_ids,
                    fund_min_bal_req=client.app_client.create_transaction.fund_app_account(params=params_2),
                    signature=signature,
                ),
                params=CommonAppCallParams(
                    box_references=["V", test_account.public_key],
                    static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 16),
                ),
            )
        )
        .add_app_call_method_call(
            client.params.get_preconditions(
                args=GetPreconditionsArgs(signature=signature),
                params=CommonAppCallParams(
                    static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
                    box_references=[test_account.public_key],
                ),
            )
        )
        .send()
    )

    assert len(result.returns) == 4


def test_it_works_using_the_fluent_composer(
    random_voting_round_app: RandomVotingAppDeployment,
) -> None:
    client = random_voting_round_app.client
    test_account = random_voting_round_app.test_account
    signature = random_voting_round_app.signature

    params_1 = FundAppAccountParams(
        amount=AlgoAmount.from_micro_algo(
            200_000 + 1_000 + 2_500 + 400 * (1 + 8 * random_voting_round_app.total_question_options)
        )
    )
    params_2 = FundAppAccountParams(
        amount=AlgoAmount.from_micro_algo(400 * (32 + 2 + len(random_voting_round_app.random_answer_ids)) + 2_500)
    )

    result = (
        client.new_group()
        .get_preconditions(
            args=GetPreconditionsArgs(signature=signature),
            params=CommonAppCallParams(
                static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
                box_references=[test_account.public_key],
            ),
        )
        .bootstrap(
            args=BootstrapArgs(fund_min_bal_req=client.app_client.create_transaction.fund_app_account(params=params_1)),
            params=CommonAppCallParams(
                box_references=["V"],
                static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 4),
            ),
        )
        .vote(
            args=VoteArgs(
                answer_ids=random_voting_round_app.random_answer_ids,
                fund_min_bal_req=client.app_client.create_transaction.fund_app_account(params=params_2),
                signature=signature,
            ),
            params=CommonAppCallParams(
                box_references=["V", test_account.public_key],
                static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 16),
            ),
        )
        .get_preconditions(
            args=GetPreconditionsArgs(signature=signature),
            params=CommonAppCallParams(
                static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
                box_references=[test_account.public_key],
                note=b"hmmm",
            ),
        )
        .send()
    )

    assert len(result.returns) == 4
