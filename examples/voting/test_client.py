# mypy: disable-error-code="no-untyped-call"

import base64
import random
import uuid
from dataclasses import dataclass

import algokit_utils
import algokit_utils.applications
import algokit_utils.transactions
import algosdk
import pytest
from algokit_utils import AlgorandClientProtocol
from algokit_utils.applications import OnUpdate
from algokit_utils.models import AlgoAmount
from algosdk.v2client.algod import AlgodClient
from nacl.signing import SigningKey

from examples.voting.client import (
    BootstrapArgs,
    CreateArgs,
    GetPreconditionsArgs,
    VoteArgs,
    VotingRoundAppClient,
    VotingRoundAppFactory,
)


@pytest.fixture
def default_deployer(algorand: AlgorandClientProtocol) -> algokit_utils.Account:
    account = algorand.account.random()
    algorand.account.ensure_funded_from_environment(account, AlgoAmount.from_algo(100))
    return account


@pytest.fixture
def voting_factory(algorand: AlgorandClientProtocol, default_deployer: algokit_utils.Account) -> VotingRoundAppFactory:
    return algorand.client.get_typed_app_factory(VotingRoundAppFactory, default_sender=default_deployer.address)


@pytest.fixture
def voting_app_client(voting_factory: VotingRoundAppFactory) -> VotingRoundAppClient:
    client, _ = voting_factory.deploy(
        deploy_time_params={"VALUE": 1}, deletable=True, updatable=True, on_update=OnUpdate.UpdateApp
    )
    return client


@dataclass
class RandomVotingAppDeployment:
    algorand: AlgorandClientProtocol
    algod: AlgodClient
    client: VotingRoundAppClient
    total_question_options: int
    test_account: algokit_utils.Account
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
    voting_factory: VotingRoundAppFactory, default_deployer: algokit_utils.Account
) -> RandomVotingAppDeployment:
    algod = voting_factory.algorand.client.algod
    status = algod.status()
    last_round = status["last-round"]  # type: ignore
    round = algod.block_info(last_round)
    current_time = round["block"]["ts"]  # type: ignore

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
        deletable=True,
        static_fee=AlgoAmount.from_micro_algo(1000 + 1000 * 4),
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
        box_references=["V"],
        static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 4),
    )

    preconditions_result = client.send.get_preconditions(
        args=GetPreconditionsArgs(signature=signature),
        box_references=[test_account.public_key],
        static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
    )

    assert preconditions_result.abi_return is not None
    assert preconditions_result.abi_return.is_allowed_to_vote == 1
    assert preconditions_result.abi_return.has_already_voted == 0
    assert preconditions_result.abi_return.is_voting_open == 0


def test_global_state(random_voting_round_app: RandomVotingAppDeployment) -> None:
    client = random_voting_round_app.client
    test_account = random_voting_round_app.test_account
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
    # TODO: decode
    # assert state['option_counts'] == question_counts


def test_works_with_separate_transactions(random_voting_round_app: RandomVotingAppDeployment) -> None:
    client = random_voting_round_app.client
    test_account = random_voting_round_app.test_account
    signature = random_voting_round_app.signature

    preconditions_result = client.send.get_preconditions(
        args=GetPreconditionsArgs(signature=signature),
        box_references=[test_account.address],
        static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
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
        box_references=["V"],
        static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 4),
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
        box_references=["V", test_account.public_key],
        static_fee=AlgoAmount.from_micro_algo(1_000 + 1_000 * 16),
    )

    preconditions_result_after = client.send.get_preconditions(
        args=GetPreconditionsArgs(signature=signature),
        box_references=[test_account.public_key],
        static_fee=AlgoAmount.from_micro_algo(1_000 + 3 * 1_000),
    )

    assert preconditions_result_after.abi_return is not None
    assert preconditions_result_after.abi_return.has_already_voted == 1


#   describe('given a usage scenario', () => {
#     test('it works with separate transactions', async () => {
#       const { signature, testAccount, totalQuestionOptions, randomAnswerIds, client } = await createRandomVotingRoundApp()

#       const preconditionsResultBefore = await client.send.getPreconditions({
#         args: {
#           signature,
#         },
#         staticFee: microAlgos(1_000 + 3 * 1_000),
#         boxReferences: [testAccount],
#       })

#       expect(preconditionsResultBefore.return?.isAllowedToVote).toBe(1n)
#       expect(preconditionsResultBefore.return?.hasAlreadyVoted).toBe(0n)

#       await client.send.bootstrap({
#         args: {
#           fundMinBalReq: client.appClient.createTransaction.fundAppAccount({
#             amount: microAlgos(200_000 + 1_000 + 2_500 + 400 * (1 + 8 * totalQuestionOptions)),
#           }),
#         },
#         boxReferences: ['V'],
#         staticFee: microAlgos(1_000 + 1_000 * 4),
#       })

#       await client.send.vote({
#         args: {
#           answerIds: randomAnswerIds,
#           fundMinBalReq: client.appClient.createTransaction.fundAppAccount({
#             amount: microAlgos(400 * (32 + 2 + randomAnswerIds.length) + 2_500),
#           }),
#           signature,
#         },
#         boxReferences: ['V', testAccount],
#         staticFee: microAlgos(1_000 + 1_000 * 16),
#       })
#       const preconditionsResultAfter = await client.send.getPreconditions({
#         args: {
#           signature,
#         },
#         staticFee: microAlgos(1_000 + 3 * 1_000),
#         boxReferences: [testAccount],
#       })

#       expect(preconditionsResultAfter.return?.hasAlreadyVoted).toBe(1n)
#     })

#     test('it works with manual use of the TransactionComposer', async () => {
#       const { algorand, signature, testAccount, totalQuestionOptions, randomAnswerIds, client } = await createRandomVotingRoundApp()

#       const result = await algorand
#         .newGroup()
#         .addAppCallMethodCall(
#           await client.params.getPreconditions({
#             args: { signature },
#             staticFee: microAlgos(1_000 + 3 * 1_000),
#             boxReferences: [testAccount],
#           }),
#         )
#         .addAppCallMethodCall(
#           await client.params.bootstrap({
#             args: {
#               fundMinBalReq: client.appClient.createTransaction.fundAppAccount({
#                 amount: microAlgos(200_000 + 1_000 + 2_500 + 400 * (1 + 8 * totalQuestionOptions)),
#               }),
#             },
#             boxReferences: ['V'],
#             staticFee: microAlgos(1_000 + 1_000 * 4),
#           }),
#         )
#         .addAppCallMethodCall(
#           await client.params.vote({
#             args: {
#               answerIds: randomAnswerIds,
#               fundMinBalReq: client.appClient.createTransaction.fundAppAccount({
#                 amount: microAlgos(400 * (32 + 2 + randomAnswerIds.length) + 2_500),
#               }),
#               signature,
#             },
#             boxReferences: ['V', testAccount],
#             staticFee: microAlgos(1_000 + 1_000 * 16),
#           }),
#         )
#         .addAppCallMethodCall(
#           await client.params.getPreconditions({
#             args: {
#               signature,
#             },
#             staticFee: microAlgos(1_000 + 3 * 1_000),
#             boxReferences: [testAccount],
#             note: 'hmmm',
#           }),
#         )
#         .execute()

#       expect(result.returns).toBeDefined()
#     })

#     test('it works using the fluent composer', async () => {
#       const { signature, testAccount, totalQuestionOptions, randomAnswerIds, client } = await createRandomVotingRoundApp()

#       const result = await client
#         .newGroup()
#         .getPreconditions({
#           args: {
#             signature,
#           },
#           staticFee: microAlgos(1_000 + 3 * 1_000),
#           boxReferences: [testAccount],
#         })
#         .bootstrap({
#           args: {
#             fundMinBalReq: client.appClient.createTransaction.fundAppAccount({
#               amount: microAlgos(200_000 + 1_000 + 2_500 + 400 * (1 + 8 * totalQuestionOptions)),
#             }),
#           },
#           boxReferences: ['V'],
#           staticFee: microAlgos(1_000 + 1_000 * 4),
#         })
#         .vote({
#           args: {
#             answerIds: randomAnswerIds,
#             fundMinBalReq: client.appClient.createTransaction.fundAppAccount({
#               amount: microAlgos(400 * (32 + 2 + randomAnswerIds.length) + 2_500),
#             }),
#             signature,
#           },
#           boxReferences: ['V', testAccount],
#           staticFee: microAlgos(1_000 + 1_000 * 16),
#         })
#         .getPreconditions({
#           args: {
#             signature,
#           },
#           staticFee: microAlgos(1_000 + 3 * 1_000),
#           boxReferences: [testAccount],
#           note: 'hmmm',
#         })
#         .send()

#       expect(result.returns[0]?.hasAlreadyVoted).toBe(0n)
#       expect(result.returns[3]?.hasAlreadyVoted).toBe(1n)
#     })
#   })
# })


# ====

# NUM_QUESTIONS = 10


# @pytest.fixture(scope="session")
# def create_args(algod_client: AlgodClient, voter: Account) -> CreateArgs:
#     quorum = math.ceil(random.randint(1, 9) * 1000)
#     question_counts = [1] * NUM_QUESTIONS

#     health = algod_client.status()
#     assert isinstance(health, dict)
#     response = algod_client.block_info(health["last-round"])
#     assert isinstance(response, dict)
#     block = response["block"]
#     block_ts = block["ts"]

#     return CreateArgs(
#         vote_id="1",
#         metadata_ipfs_cid="cid",
#         start_time=int(block_ts),
#         end_time=int(block_ts) + 1000,
#         quorum=quorum,
#         snapshot_public_key=voter.public_key,
#         nft_image_url="ipfs://cid",
#         option_counts=question_counts,
#     )


# @pytest.fixture
# def deploy_create_args(algod_client: AlgodClient, create_args: CreateArgs) -> DeployCreate[CreateArgs]:
#     sp = algod_client.suggested_params()
#     sp.fee = algosdk.util.algos_to_microalgos(4)
#     sp.flat_fee = True
#     return DeployCreate(args=create_args, suggested_params=sp)


# @pytest.fixture
# def deploy_voting_client(
#     algod_client: AlgodClient,
#     indexer_client: IndexerClient,
#     funded_account: Account,
#     deploy_create_args: DeployCreate[CreateArgs],
# ) -> VotingRoundAppClient:
#     algokit_utils.transfer(
#         client=algod_client,
#         parameters=algokit_utils.TransferParameters(
#             from_account=algokit_utils.get_localnet_default_account(algod_client),
#             to_address=funded_account.address,
#             micro_algos=algosdk.util.algos_to_microalgos(1),
#         ),
#     )

#     client = VotingRoundAppClient(
#         algod_client=algod_client, indexer_client=indexer_client, creator=funded_account, app_name=get_unique_name()
#     )
#     client.deploy(allow_delete=True, create_args=deploy_create_args)

#     return client


# @pytest.fixture(scope="session")
# def voter(algod_client: AlgodClient) -> Account:
#     voter = algosdk.account.generate_account()
#     voter_account = Account(private_key=voter[0], address=voter[1])
#     algokit_utils.transfer(
#         client=algod_client,
#         parameters=algokit_utils.TransferParameters(
#             from_account=algokit_utils.get_localnet_default_account(algod_client),
#             to_address=voter_account.address,
#             micro_algos=algosdk.util.algos_to_microalgos(10),
#         ),
#     )
#     return voter_account


# @pytest.fixture(scope="session")
# def voter_signature(voter: Account) -> bytes:
#     private_key = base64.b64decode(voter.private_key)
#     signing_key = SigningKey(private_key[: algosdk.constants.key_len_bytes])
#     signed = signing_key.sign(voter.public_key)
#     return signed.signature


# @pytest.fixture
# def fund_min_bal_req(algod_client: AlgodClient, deploy_voting_client: VotingRoundAppClient) -> TransactionWithSigner:
#     from_account = algokit_utils.get_localnet_default_account(algod_client)
#     payment = algosdk.transaction.PaymentTxn(
#         sender=from_account.address,
#         receiver=deploy_voting_client.app_address,
#         amt=(100000 * 2) + 1000 + 2500 + 400 * (1 + 8 * NUM_QUESTIONS),
#         note=b"Bootstrap payment",
#         sp=algod_client.suggested_params(),
#     )
#     return TransactionWithSigner(txn=payment, signer=from_account.signer)


# @pytest.fixture
# def bootstrap_response(
#     deploy_voting_client: VotingRoundAppClient,
#     fund_min_bal_req: TransactionWithSigner,
# ) -> algokit_utils.ABITransactionResponse[None]:
#     return deploy_voting_client.bootstrap(
#         fund_min_bal_req=fund_min_bal_req,
#         transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")]),
#     )


# def test_get_preconditions(
#     deploy_voting_client: VotingRoundAppClient, algod_client: AlgodClient, voter: Account, voter_signature: bytes
# ) -> None:
#     sp = algod_client.suggested_params()
#     sp.fee = 12000
#     sp.flat_fee = True
#     response = deploy_voting_client.get_preconditions(
#         signature=voter_signature,
#         transaction_parameters=algokit_utils.TransactionParameters(
#             boxes=[(0, voter.public_key)],
#             suggested_params=sp,
#             sender=voter.address,
#             signer=AccountTransactionSigner(voter.private_key),
#         ),
#     )

#     assert isinstance(response.return_value, VotingPreconditions)
#     assert response.return_value.is_voting_open == 0
#     assert response.return_value.has_already_voted == 0
#     assert response.return_value.is_allowed_to_vote == 1


# def test_vote(
#     deploy_voting_client: VotingRoundAppClient,
#     algod_client: AlgodClient,
#     voter: Account,
#     voter_signature: bytes,
#     bootstrap_response: algokit_utils.ABITransactionResponse[None],
# ) -> None:
#     # bootstrap app
#     assert bootstrap_response.confirmed_round

#     # vote payment
#     question_counts = [0] * NUM_QUESTIONS
#     payment = algosdk.transaction.PaymentTxn(
#         sender=voter.address,
#         receiver=deploy_voting_client.app_address,
#         amt=400 * (32 + 2 + len(question_counts) * 1) + 2500,
#         sp=deploy_voting_client.algod_client.suggested_params(),
#     )
#     fund_min_bal_req = TransactionWithSigner(payment, voter.signer)

#     # vote fee
#     sp = algod_client.suggested_params()
#     sp.fee = 12000
#     sp.flat_fee = True
#     response = deploy_voting_client.vote(
#         fund_min_bal_req=fund_min_bal_req,
#         signature=voter_signature,
#         answer_ids=question_counts,
#         transaction_parameters=algokit_utils.TransactionParameters(
#             suggested_params=sp,
#             boxes=[(0, "V"), (0, voter.public_key)],
#             sender=voter.address,
#             signer=voter.signer,
#         ),
#     )
#     assert response.return_value is None


# def test_create(algod_client: AlgodClient, funded_account: Account, create_args: CreateArgs) -> None:
#     voting_round_app_client = VotingRoundAppClient(
#         algod_client=algod_client,
#         signer=funded_account,
#         template_values={"VALUE": 1, "DELETABLE": 1},
#     )

#     sp = algod_client.suggested_params()
#     sp.fee = algosdk.util.algos_to_microalgos(4)
#     sp.flat_fee = True

#     response = voting_round_app_client.create_create(
#         vote_id=create_args.vote_id,
#         snapshot_public_key=create_args.snapshot_public_key,
#         metadata_ipfs_cid=create_args.metadata_ipfs_cid,
#         start_time=create_args.start_time,
#         end_time=create_args.end_time,
#         option_counts=create_args.option_counts,
#         quorum=create_args.quorum,
#         nft_image_url=create_args.nft_image_url,
#         transaction_parameters=algokit_utils.CreateTransactionParameters(suggested_params=sp),
#     )

#     assert response.confirmed_round


# def test_boostrap(
#     bootstrap_response: algokit_utils.ABITransactionResponse[None],
# ) -> None:
#     # bootstrap app
#     assert bootstrap_response.confirmed_round


# def test_close(
#     deploy_voting_client: VotingRoundAppClient,
#     bootstrap_response: algokit_utils.ABITransactionResponse[None],
# ) -> None:
#     # bootstrap app
#     assert bootstrap_response.confirmed_round

#     sp = deploy_voting_client.app_client.algod_client.suggested_params()
#     sp.fee = algosdk.util.algos_to_microalgos(1)
#     sp.flat_fee = True
#     deploy_voting_client.close(
#         transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")], suggested_params=sp)
#     )


# def test_compose(
#     algod_client: AlgodClient,
#     deploy_voting_client: VotingRoundAppClient,
#     fund_min_bal_req: TransactionWithSigner,
#     voter: Account,
#     voter_signature: bytes,
# ) -> None:
#     sp = algod_client.suggested_params()
#     sp.fee = 12000
#     sp.flat_fee = True

#     response = (
#         deploy_voting_client.compose()
#         .bootstrap(
#             fund_min_bal_req=fund_min_bal_req,
#             transaction_parameters=algokit_utils.TransactionParameters(boxes=[(0, "V")]),
#         )
#         .get_preconditions(
#             signature=voter_signature,
#             transaction_parameters=algokit_utils.TransactionParameters(
#                 boxes=[(0, voter.public_key)],
#                 suggested_params=sp,
#                 sender=voter.address,
#                 signer=AccountTransactionSigner(voter.private_key),
#             ),
#         )
#     ).execute()

#     bootstrap_response, get_preconditions = response.abi_results
#     assert bootstrap_response.tx_id

#     assert get_preconditions.return_value[:3] == [1, 1, 0]
