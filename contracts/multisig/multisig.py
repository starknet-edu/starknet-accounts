import sys
import json
import asyncio

sys.path.append('./')

from utils import deploy_account, invoke_tx_hash, print_n_wait, mission_statement, fund_account, get_evaluator
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    mission_statement()
    print("\t 1) implement a 2/3 multisig contract")
    print("\t 2) implement the following interfaces expected by the validator:")
    print("\t\t - get_confirmations")
    print("\t\t - get_owner_confirmed")
    print("\t\t - get_num_owners")
    print("\t\t - get_owners")
    print("\t 3) implement function for contract owner to submit a tx for the owners to sign")
    print("\t 4) implement function for contract owner confirm a submitted tx")
    print("\t 5) implement function to execute a transaction that has ben confirmed by at least two unique owners")
    print("\t 6) deploy the signers for the multisig")
    print("\t 7) deploy the multisig")
    print("\t 8) submit a transaction to the multisig")
    print("\t 9) confirm the tx")
    print("\t 10) execute the tx\u001b[0m\n")

    #
    # MISSION 6
    #
    # client = Client("testnet")
    client = Client(net=data['DEVNET_URL'], chain="testnet")

    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)
    sig1, sig1_addr = await deploy_account(client=client, contract_path=data['SIGNATURE_BASIC'], constructor_args=[stark_key], additional_data=1)
    await fund_account(sig1_addr)

    private_key_2 = private_key + 1
    stark_key_2 = private_to_stark_key(private_key_2)
    sig2, sig2_addr = await deploy_account(client=client, contract_path=data['SIGNATURE_BASIC'], constructor_args=[stark_key_2], additional_data=2)
    await fund_account(sig2_addr)
    
    private_key_3 = private_key + 2
    stark_key_3 = private_to_stark_key(private_key_3)
    sig3, sig3_addr = await deploy_account(client=client, contract_path=data['SIGNATURE_BASIC'], constructor_args=[stark_key_3], additional_data=3)
    await fund_account(sig3_addr)

    _, evaluator_address = await get_evaluator(client)

    #
    # MISSION 7
    #
    _, multi_addr = await deploy_account(client=client, contract_path=data['MULTISIG'], constructor_args=[[sig1_addr, sig2_addr, sig3_addr]])
    
    #
    # MISSION 8
    #
    validator_selector = get_selector_from_name("validate_multisig")
    submit_selector = get_selector_from_name("submit_tx")

    (nonce_1, ) = await sig1.functions["get_nonce"].call()
    inner_calldata=[evaluator_address, validator_selector, 2, 1, data['DEVNET_ACCOUNT']['ADDRESS']]
    outer_calldata=[multi_addr, submit_selector, nonce_1, len(inner_calldata), *inner_calldata]

    hash = invoke_tx_hash(sig1_addr, outer_calldata)
    sub_signature = sign(hash, private_key)

    sub_prepared = sig1.functions["__execute__"].prepare(
        contract_address=multi_addr,
        selector=submit_selector,
        nonce=nonce_1,
        calldata_len=len(inner_calldata),
        calldata=inner_calldata)
    sub_invocation = await sub_prepared.invoke(signature=sub_signature, max_fee=data['MAX_FEE'])

    eventData = await print_n_wait(client, sub_invocation)

    #
    # MISSION 9
    #
    confirm_selector = get_selector_from_name("confirm_tx")

    (nonce_2, ) = await sig2.functions["get_nonce"].call()
    conf_calldata=[multi_addr, confirm_selector, nonce_2, 1, eventData[1]]
    conf_hash = invoke_tx_hash(sig2_addr, conf_calldata)

    conf_signature = sign(conf_hash, private_key_2)

    conf_prepared = sig2.functions["__execute__"].prepare(
        contract_address=multi_addr,
        selector=confirm_selector,
        nonce=nonce_2,
        calldata_len=2,
        calldata=[eventData[1]])
    conf_invocation = await conf_prepared.invoke(signature=conf_signature, max_fee=data['MAX_FEE'])

    await print_n_wait(client, conf_invocation)

    (nonce_3, ) = await sig3.functions["get_nonce"].call()
    conf_2_calldata=[multi_addr, confirm_selector, nonce_3, 1, eventData[1]]

    conf_2_hash = invoke_tx_hash(sig3_addr, conf_2_calldata)

    conf_2_signature = sign(conf_2_hash, private_key_3)

    conf_2_prepared = sig3.functions["__execute__"].prepare(
        contract_address=multi_addr,
        selector=confirm_selector,
        nonce=nonce_3,
        calldata_len=1,
        calldata=[eventData[1]])
    conf_2_invocation = await conf_2_prepared.invoke(signature=conf_2_signature, max_fee=data['MAX_FEE'])

    await print_n_wait(client, conf_2_invocation)

    #
    # MISSION 10
    #
    execute_selector = get_selector_from_name("__execute__")
    exec_calldata=[multi_addr, execute_selector, nonce_1+1, 1, eventData[1]]

    exec_hash = invoke_tx_hash(sig1_addr, exec_calldata)
    exec_signature = sign(exec_hash, private_key)
    
    exec_prepared = sig1.functions["__execute__"].prepare(
        contract_address=multi_addr,
        selector=execute_selector,
        nonce=nonce_1+1,
        calldata_len=1,
        calldata=[eventData[1]])
    exec_invocation = await exec_prepared.invoke(signature=exec_signature, max_fee=data['MAX_FEE'])

    await print_n_wait(client, exec_invocation)

asyncio.run(main())
