import os
import asyncio
import sys

sys.path.append('../')

from utils import deploy_testnet, invoke_tx_hash, mission_statement, print_n_wait
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

VALIDATOR_ADDRESS = int(os.getenv("VALIDATOR_ADDRESS"), 16)
WALLET_ADDRESS = int(os.getenv("WALLET_ADDRESS"), 16)

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
    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)

    private_key_2 = private_key + 1
    stark_key_2 = private_to_stark_key(private_key_2)

    private_key_3 = private_key + 2
    stark_key_3 = private_to_stark_key(private_key_3)

    client = Client("testnet")
    signer_1_address = await deploy_testnet("signature_basic", [stark_key], 1)
    signer_1_contract = await Contract.from_address(signer_1_address, client)

    signer_2_address = await deploy_testnet("signature_basic", [stark_key_2], 2)
    signer_2_contract = await Contract.from_address(signer_2_address, client)

    signer_3_address = await deploy_testnet("signature_basic", [stark_key_3], 3)
    signer_3_contract = await Contract.from_address(signer_3_address, client)

    #
    # MISSION 7
    #
    multi = await deploy_testnet("multisig", [[signer_1_address, signer_2_address, signer_3_address]])
    multi_contract = await Contract.from_address(multi, client)
    
    #
    # MISSION 8
    #
    validator_selector = get_selector_from_name("validate_multisig")
    submit_selector = get_selector_from_name("submit_tx")
    submit_event_selector = get_selector_from_name("submit")

    (nonce_1, ) = await signer_1_contract.functions["get_nonce"].call()
    inner_calldata=[VALIDATOR_ADDRESS, validator_selector, 2, 1, WALLET_ADDRESS]
    outer_calldata=[multi, submit_selector, nonce_1, len(inner_calldata), *inner_calldata]

    hash = invoke_tx_hash(signer_1_address, outer_calldata)
    sub_signature = sign(hash, private_key)

    sub_prepared = signer_1_contract.functions["__execute__"].prepare(
        contract_address=multi,
        selector=submit_selector,
        nonce=nonce_1,
        calldata_len=len(inner_calldata),
        calldata=inner_calldata)
    sub_invocation = await sub_prepared.invoke(signature=sub_signature, max_fee=0)

    data = await print_n_wait(client, sub_invocation)

    #
    # MISSION 9
    #
    confirm_selector = get_selector_from_name("confirm_tx")
    confirm_event_selector = get_selector_from_name("confirm")

    (nonce_2, ) = await signer_2_contract.functions["get_nonce"].call()
    conf_calldata=[multi, confirm_selector, nonce_2, 1, data[1]]
    conf_hash = invoke_tx_hash(signer_2_address, conf_calldata)

    conf_signature = sign(conf_hash, private_key_2)

    conf_prepared = signer_2_contract.functions["__execute__"].prepare(
        contract_address=multi,
        selector=confirm_selector,
        nonce=nonce_2,
        calldata_len=2,
        calldata=[data[1]])
    conf_invocation = await conf_prepared.invoke(signature=conf_signature, max_fee=0)

    await print_n_wait(client, conf_invocation)

    (nonce_3, ) = await signer_3_contract.functions["get_nonce"].call()
    conf_2_calldata=[multi, confirm_selector, nonce_3, 1, data[1]]

    conf_2_hash = invoke_tx_hash(signer_3_address, conf_2_calldata)

    conf_2_signature = sign(conf_2_hash, private_key_3)

    conf_2_prepared = signer_3_contract.functions["__execute__"].prepare(
        contract_address=multi,
        selector=confirm_selector,
        nonce=nonce_3,
        calldata_len=1,
        calldata=[data[1]])
    conf_2_invocation = await conf_2_prepared.invoke(signature=conf_2_signature, max_fee=0)

    await print_n_wait(client, conf_2_invocation)

    #
    # MISSION 10
    #
    execute_selector = get_selector_from_name("__execute__")
    execute_event_selector = get_selector_from_name("execute")
    exec_calldata=[multi, execute_selector, nonce_1+1, 1, data[1]]

    exec_hash = invoke_tx_hash(signer_1_address, exec_calldata)
    exec_signature = sign(exec_hash, private_key)
    
    exec_prepared = signer_1_contract.functions["__execute__"].prepare(
        contract_address=multi,
        selector=execute_selector,
        nonce=nonce_1+1,
        calldata_len=1,
        calldata=[data[1]])
    exec_invocation = await exec_prepared.invoke(signature=exec_signature, max_fee=0)

    await print_n_wait(client, exec_invocation)

asyncio.run(main())
