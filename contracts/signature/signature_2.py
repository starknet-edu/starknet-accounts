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
    blue.print("\t 1) implement account contract interface 'is_valid_signature'")
    blue.print("\t 2) deploy account contract with with '__validate__', '__validate_declare__', '__execute__' entrypoints")
    blue.print("\t 3) sign the calldata expected by the validator")
    blue.print("\t 4) invoke the validator check with the signature in the tx_info field")
    blue.print("\t 5) call until you hit payday\n")

    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)

    client = get_account(get_client())

    sig2, sig2_addr = await compile_deploy(client=client, contract=data['SIGNATURE_2'], args=[stark_key], account=True)
    
    reward_account = await fund_account(sig2_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return
      
    _, evaluator_address = await get_evaluator(client)
    
    #
    # Format calldata
    # 
    calldata = [evaluator_address, get_selector_from_name("validate_signature_2"), 1, reward_account]

    #
    # Provide tx signature via starknet_py
    #
    nonce = await client.get_contract_nonce(sig2_addr)
    
    hash = invoke_tx_hash(sig2_addr, calldata, nonce)
    signature = sign(hash, private_key)
    
    invoke = InvokeFunction(
      calldata=calldata,
      signature=[*signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig2_addr,
    )

    resp = await sig2.send_transaction(invoke)
    await print_n_wait(client, resp)

    nonce = await client.get_contract_nonce(sig2_addr)
    
    hash = invoke_tx_hash(sig2_addr, calldata, nonce)
    signature = sign(hash, private_key)
    
    invoke = InvokeFunction(
      calldata=calldata,
      signature=[*signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig2_addr,
    )
    resp = await sig2.send_transaction(invoke)
    await print_n_wait(client, resp)

asyncio.run(main())
