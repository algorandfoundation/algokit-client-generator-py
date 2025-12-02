import algokit_utils
import pytest

@pytest.fixture(scope="session")
def algorand() -> algokit_utils.AlgorandClient:
    return algokit_utils.AlgorandClient.from_environment()

