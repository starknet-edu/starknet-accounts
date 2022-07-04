import sys
import json
import random
import asyncio

sys.path.append('./')

from console import blue_strong, blue, red
from utils import deploy_account, invoke_tx_hash, print_n_wait, fund_account, get_evaluator, get_client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    blue_strong.print("Your mission:")
    blue.print("\t 1) implement account contract interface 'is_valid_signature'")
    blue.print("\t 2) deploy account contract with an '__execute__' entrypoint init w/ the provided public key")
    blue.print("\t 3) sign the calldata expected by the validator")
    blue.print("\t 4) invoke the validator check with the signature in the tx_info field")
    blue.print("\t 5) call until you hit paydirt\n")

    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)

    client = get_client()

    sig2, sig2_addr = await deploy_account(client=client, contract_path=data['SIGNATURE_2'], constructor_args=[stark_key])
    
    reward_account = await fund_account(sig2_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return
      
    _, evaluator_address = await get_evaluator(client)
    
    selector = get_selector_from_name("validate_signature_2")
    calldata = [evaluator_address, selector, 2, 1, reward_account]

    hash = invoke_tx_hash(sig2_addr, calldata)
    signature = sign(hash, private_key)

    #
    # ACTION ITEM 2: provide tx signature via starknet_py
    #
    prepared1 = sig2.functions["__execute__"].prepare(
        contract_address=evaluator_address,
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key), reward_account])

    invocation1 = await prepared1.invoke(signature=0, max_fee=data['MAX_FEE'])

    await print_n_wait(client, invocation1)

    prepared2 = sig2.functions["__execute__"].prepare(
        contract_address=evaluator_address,
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key), reward_account])
    invocation2 = await prepared2.invoke(signature=signature, max_fee=data['MAX_FEE'])

    await print_n_wait(client, invocation2)

asyncio.run(main())
