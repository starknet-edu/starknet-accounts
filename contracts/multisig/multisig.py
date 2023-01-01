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
    blue.print("\t 1) implement a 2/3 multisig contract")
    blue.print("\t 2) implement the following interfaces expected by the validator:")
    blue.print("\t\t - get_confirmations")
    blue.print("\t\t - get_owner_confirmed")
    blue.print("\t\t - get_num_owners")
    blue.print("\t\t - get_owners")
    blue.print("\t 3) implement function for contract owner to submit a tx for the owners to sign")
    blue.print("\t 4) implement function for contract owner confirm a submitted tx")
    blue.print("\t 5) implement function to execute a transaction that has ben confirmed by at least two unique owners")
    blue.print("\t 6) deploy the signers for the multisig")
    blue.print("\t 7) deploy the multisig")
    blue.print("\t 8) submit a transaction to the multisig")
    blue.print("\t 9) confirm the tx")
    blue.print("\t 10) execute the tx\n")

    client = get_account(get_client())

    #
    # Deploy first signer
    #
    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)
    sig1, sig1_addr = await compile_deploy(client=client, contract=data['SIGNATURE_BASIC'], args=[stark_key], account=True, cache_name="sig1")
    reward_account = await fund_account(sig1_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return

    #
    # Deploy second signer
    #
    private_key_2 = private_key + 1
    stark_key_2 = private_to_stark_key(private_key_2)
    sig2, sig2_addr = await compile_deploy(client=client, contract=data['SIGNATURE_BASIC'], args=[stark_key_2], account=True, cache_name="sig2")
    reward_account = await fund_account(sig2_addr)
    
    #
    # Deploy third signer
    #
    private_key_3 = private_key + 2
    stark_key_3 = private_to_stark_key(private_key_3)
    sig3, sig3_addr = await compile_deploy(client=client, contract=data['SIGNATURE_BASIC'], args=[stark_key_3], account=True, cache_name="sig3")
    reward_account = await fund_account(sig3_addr)

    _, evaluator_address = await get_evaluator(client)

    #
    # Deploy multisig contract
    #
    _, multi_addr = await compile_deploy(client=client, contract=data['MULTISIG'], args=[[sig1_addr, sig2_addr, sig3_addr]])
    

    validator_selector = get_selector_from_name("validate_multisig")
    submit_selector = get_selector_from_name("submit_tx")
    confirm_selector = get_selector_from_name("confirm_tx")
    execute_selector = get_selector_from_name("execute")

    #
    # Submit a transaction to the multisig
    #
    nonce = await client.get_contract_nonce(sig1_addr)

    inner_calldata=[evaluator_address, validator_selector, 2, 1, reward_account]
    outer_calldata=[multi_addr, submit_selector, len(inner_calldata), *inner_calldata]

    hash = invoke_tx_hash(sig1_addr, outer_calldata, nonce)
    sub_signature = sign(hash, private_key)

    invoke = InvokeFunction(
      calldata=outer_calldata,
      signature=[*sub_signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig1_addr,
    )

    resp = await sig1.send_transaction(invoke)
    eventData = await print_n_wait(client, resp)

    #
    # Provide first tx confirmation
    #

    nonce = await client.get_contract_nonce(sig2_addr)

    conf_calldata=[multi_addr, confirm_selector, 1, eventData[1]]
    conf_hash = invoke_tx_hash(sig2_addr, conf_calldata, nonce)

    conf_signature = sign(conf_hash, private_key_2)

    invoke = InvokeFunction(
      calldata=conf_calldata,
      signature=[*conf_signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig2_addr,
    )

    resp = await sig2.send_transaction(invoke)
    await print_n_wait(client, resp)

    #
    # Provide second tx confirmation
    #
    nonce = await client.get_contract_nonce(sig3_addr)

    conf_2_calldata=[multi_addr, confirm_selector, 1, eventData[1]]
    conf_2_hash = invoke_tx_hash(sig3_addr, conf_2_calldata, nonce)
    conf_2_signature = sign(conf_2_hash, private_key_3)

    invoke = InvokeFunction(
      calldata=conf_calldata,
      signature=[*conf_2_signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig3_addr,
    )

    resp = await sig3.send_transaction(invoke)
    await print_n_wait(client, resp)

    #
    # Execute a submitted confirmed transaction
    #
    nonce = await client.get_contract_nonce(sig1_addr)

    exec_calldata=[multi_addr, execute_selector, 1, eventData[1]]
    exec_hash = invoke_tx_hash(sig1_addr, exec_calldata, nonce)
    exec_signature = sign(exec_hash, private_key)
    
    invoke = InvokeFunction(
      calldata=exec_calldata,
      signature=[*exec_signature],
      max_fee=data['MAX_FEE'],
      version=1,
      nonce=nonce,
      contract_address=sig1_addr,
    )

    resp = await sig1.send_transaction(invoke)
    await print_n_wait(client, resp)

asyncio.run(main())
