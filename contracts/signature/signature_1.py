import asyncio
import sys
import json
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + "/../tutorial")

from console import blue_strong, blue, red
from utils import compile_deploy, print_n_wait, get_evaluator, fund_account, get_client, get_account
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash
from starknet_py.net.models import InvokeFunction

with open(os.path.abspath(os.path.dirname(__file__)) + "/../config.json", "r") as f:
  data = json.load(f)

async def main():
    blue_strong.print("Your mission:")
    blue.print("\t 1) find the first two EIP numbers discussing account abstraction")
    blue.print("\t 2) deploy account contract with '__validate__', '__validate_declare__', '__execute__' entrypoints")
    blue.print("\t 3) use the private key to sign the values using the Stark curve")
    blue.print("\t 4) invoke the validator check with the signature in the tx_info field\n")

    #
    # The first EIP number discussing account abstraction
    #
    INPUT_1 = 2938

    #
    # The second EIP number discussing account abstraction
    #
    INPUT_2 = 4337
    blue.print(f"First account abstraction EIP: \n\thttps://eips.ethereum.org/EIPS/eip-{INPUT_1}")
    blue.print(f"Second account abstraction EIP: \n\thttps://eips.ethereum.org/EIPS/eip-{INPUT_2}\n")

    client = get_account(get_client())
    sig1, sig1_addr = await compile_deploy(client=client, contract=data['SIGNATURE_1'], account=True)

    reward_account = await fund_account(sig1_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return
      
    _, evaluator_address = await get_evaluator(client)
    
    #
    # Format calldata
    #  
    hash = pedersen_hash(INPUT_1, INPUT_2)
    hash_final = pedersen_hash(hash, sig1_addr)
    signature = sign(hash_final, data['PRIVATE_KEY'])

    calldata = [evaluator_address, get_selector_from_name("validate_signature_1"), 3, INPUT_1, INPUT_2, reward_account]

    #
    # Submit the invoke transaction
    #
    nonce = await client.get_contract_nonce(sig1_addr)

    invoke = InvokeFunction(
      calldata=calldata,
      signature=[*signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig1_addr,
    )

    resp = await sig1.send_transaction(invoke)
    await print_n_wait(client, resp)

asyncio.run(main())
