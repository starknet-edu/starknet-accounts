import asyncio
import sys
import json
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + "/../tutorial")

from console import blue_strong, blue, red
from utils import compile_deploy, print_n_wait, get_evaluator, fund_account, get_client, get_account
from starkware.starknet.public.abi import get_selector_from_name
from starknet_py.net.models import InvokeFunction

with open(os.path.abspath(os.path.dirname(__file__)) + "/../config.json", "r") as f:
  data = json.load(f)

async def main():
    blue_strong.print("Your mission:")
    blue.print("\t 1) deploy an account contract with '__validate__', '__validate_declare__', '__execute__' entrypoints")
    blue.print("\t 2) fetch the 'random' storage_variable from the validator contract")
    blue.print("\t 3) pass 'random' via calldata to your account contract\n")

    #
    # Initialize StarkNet Client
    #
    client = get_account(get_client())

    #
    # Compile and Deploy `hello.cairo`
    #
    hello, hello_addr = await compile_deploy(client=client, contract=data['HELLO'], account=True)

    #
    # Transfer ETH to pay for fees
    #
    reward_account = await fund_account(hello_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return
    
    #
    # Check answer against 'evaluator.cairo'
    #    
    evaluator, evaluator_address = await get_evaluator(client)
    (random, ) = await evaluator.functions["get_random"].call()

    #
    # Format calldata
    #   
    calldata = [evaluator_address, get_selector_from_name("validate_hello"), 2, random, reward_account]

    #
    # Submit the invoke transaction
    #  
    nonce = await client.get_contract_nonce(hello_addr)

    invoke = InvokeFunction(
      calldata=calldata,
      signature=[],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=hello_addr,
    )

    resp = await hello.send_transaction(invoke)
    await print_n_wait(hello, resp)

asyncio.run(main())
