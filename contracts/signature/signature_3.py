import sys
import json
import asyncio

sys.path.append('./')

from console import blue_strong, blue, red
from utils import deploy_account, invoke_tx_hash, print_n_wait, fund_account, get_evaluator, get_client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    blue_strong.print("Your mission:")
    blue.print("\t 1) implement account contract interface 'get_nonce'")
    blue.print("\t 2) implement account contract interface 'get_signer'")
    blue.print("\t 3) deploy account contract")
    blue.print("\t 4) sign calldata")
    blue.print("\t 5) invoke check\n")

    #
    # MISSION 3
    #
    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)

    client = get_client()

    sig3, sig3_addr = await deploy_account(client=client, contract_path=data['SIGNATURE_3'], constructor_args=[stark_key])

    reward_account = await fund_account(sig3_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return
      
    _, evaluator_address = await get_evaluator(client)
    
    #
    # MISSION 4
    #
    (nonce, ) = await sig3.functions["get_nonce"].call()
    selector = get_selector_from_name("validate_signature_3")
    calldata = [evaluator_address, selector, 2, nonce, reward_account]

    hash = invoke_tx_hash(sig3_addr, calldata)
    hash_final = pedersen_hash(hash, nonce)
    signature = sign(hash_final, private_key)

    prepared = sig3.functions["__execute__"].prepare(
        contract_address=evaluator_address,
        selector=selector,
        calldata_len=2,
        calldata=[nonce, reward_account])
    
    #
    # MISSION 5
    #
    invocation = await prepared.invoke(signature=signature, max_fee=data['MAX_FEE'])

    await print_n_wait(client, invocation)

asyncio.run(main())
