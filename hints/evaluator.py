import os
import json
import pytest

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract

with open("hints.json", "r") as f:
  data = json.load(f)

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def evaluator_setup(starknet: Starknet) -> StarknetContract:
    player_registry = await starknet.deploy(
        source=data['REGISTRY_FILE'],
        constructor_calldata=[data['FIRST_TEACHER']],
    )
    
    erc20 = await starknet.deploy(
        source=data['ERC20_FILE'],
        constructor_calldata=[
            data['ERC20_NAME'],
            data['ERC20_SYMBOL'],
            data['ERC20_DECIMAL'],
            data['FIRST_TEACHER'],
            ],
    )

    evaluator = await starknet.deploy(
        source=data['EVALUATOR_FILE'],
        constructor_calldata=[
            data['PRIVATE_KEY'],
            data['PUBLIC_KEY'],
            data['INPUT_1'],
            data['INPUT_2'],
            player_registry.contract_address,
            erc20.contract_address,
            data['FIRST_TEACHER']],
    )

    return evaluator, player_registry, erc20
