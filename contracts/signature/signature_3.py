import sys
import json
import asyncio
import eth_keys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + "/../tutorial")

from console import blue_strong, blue, red
from utils import compile_deploy, invoke_tx_hash, print_n_wait, fund_account, get_evaluator, get_client, to_uint, get_account
from starkware.starknet.public.abi import get_selector_from_name
from starknet_py.net.models import InvokeFunction

with open(os.path.abspath(os.path.dirname(__file__)) + "/../config.json", "r") as f:
  data = json.load(f)

async def main():
    blue_strong.print("Your mission:")
    blue.print("\t 1) implement account contract interface 'is_valid_eth_signature'")
    blue.print("\t 2) deploy account contract with with '__validate__', '__validate_declare__', '__execute__' entrypoints")
    blue.print("\t 3) sign the calldata using secp256k1 curve")
    blue.print("\t 4) invoke the validator check with the signature in the tx_info field")
    blue.print("\t 5) call until you hit payday\n")

    pk = eth_keys.keys.PrivateKey(b'\x01' * 32)

    client = get_account(get_client())

    sig3, sig3_addr = await compile_deploy(client=client, contract=data['SIGNATURE_3'], args=[data['ETHEREUM_ADDRESS']], account=True)

    reward_account = await fund_account(sig3_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return
      
    _, evaluator_address = await get_evaluator(client)
    #
    # Format calldata
    # 

    calldata = [evaluator_address, get_selector_from_name("validate_signature_3"), 1, reward_account]

    #
    # Submit the invoke transaction
    #
    nonce = await client.get_contract_nonce(sig3_addr)

    hash = invoke_tx_hash(sig3_addr, calldata, nonce)

    signature = pk.sign_msg_hash((hash).to_bytes(32, byteorder="big"))
    sig_r = to_uint(signature.r)
    sig_s = to_uint(signature.s)

    invoke = InvokeFunction(
      calldata=calldata,
      signature=[signature.v, *sig_r, *sig_s],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig3_addr,
    )

    resp = await sig3.send_transaction(invoke)
    await print_n_wait(client, resp)

asyncio.run(main())
