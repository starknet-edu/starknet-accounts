import sys
import json
import asyncio
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + "/../tutorial")

from console import blue_strong, blue, red
from utils import compile_deploy, invoke_tx_hash, print_n_wait, fund_account, get_evaluator, get_client, get_account
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starknet_py.net.models import InvokeFunction

with open(os.path.abspath(os.path.dirname(__file__)) + "/../config.json", "r") as f:
  data = json.load(f)

async def main():
    blue_strong.print("Your mission:")
    blue.print("\t 1) implement account execution similar to OpenZeppelin w/ AccountCallArray")
    blue.print("\t 2) deploy account contract")
    blue.print("\t 3) format and sign invocations and calldata")
    blue.print("\t 4) invoke multiple contracts in the same block\n")

    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)

    client = get_account(get_client())

    multicall, multicall_addr = await compile_deploy(client=client, contract=data['MULTICALL'], args=[stark_key], account=True)
    
    reward_account = await fund_account(multicall_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return

    _, evaluator_address = await get_evaluator(client)
    
    #
    # Format calldata
    # 
    selector = get_selector_from_name("validate_multicall")
    
    nonce = await client.get_contract_nonce(multicall_addr)

    #
    # Format the 'CalldataArray'
    #
    inner_calldata = [reward_account, reward_account, reward_account]
    calldata = [
        3,
        evaluator_address, selector, 0, 1,
        evaluator_address, selector, 1, 1,
        evaluator_address, selector, 2, 1,
        len(inner_calldata), *inner_calldata
    ]

    hash = invoke_tx_hash(multicall_addr, calldata, nonce)
    signature = sign(hash, private_key)

    invoke = InvokeFunction(
      calldata=calldata,
      signature=[*signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=multicall_addr,
    )

    resp = await multicall.send_transaction(invoke)
    await print_n_wait(client, resp)

asyncio.run(main())
