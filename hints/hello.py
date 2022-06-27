import json
import pytest

from evaluator import evaluator_setup, starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name

with open("hints.json", "r") as f:
  data = json.load(f)

@pytest.mark.asyncio
async def test_hello(evaluator_setup: StarknetContract):
    (evaluator, registry, erc20) = evaluator_setup

    hello = await starknet.deploy(
        source=data['HELLO_FILE'],
        constructor_calldata=[],
    )

    proxy = await starknet.deploy(
        source=data['PROXY_FILE'],
        constructor_calldata=[hello.contract_address],
    )
    print("GOT HERE", proxy.contract_address)

    # rand_info = await evaluator.get_random().call()
    # print("RAND_INFO: ", eval.contract_address, registry.contract_address, hello.contract_address)
    # selector = get_selector_from_name("validate_hello")

    # exec_info = await hello.__execute__(
    #     contract_address=validator.contract_address,
    #     selector=selector,
    #     calldata=[rand_info.result.rand, data['DUMMY_ACCOUNT']],
    # ).invoke()
    # assert exec_info.result.retdata[0] == 1

    # balance = await ACT.balanceOf(account=data['DUMMY_ACCOUNT']).call()
    # assert balance.result.balance.low == 100000000000000000000
