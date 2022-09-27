import asyncio
import json
import sys

from starknet_py.net.models import InvokeFunction
from starkware.crypto.signature.signature import private_to_stark_key
from starkware.starknet.public.abi import get_selector_from_name

sys.path.append("./tutorial")

from console import blue, blue_strong, red
from utils import compile_deploy, fund_account, get_client, get_evaluator, print_n_wait

with open("./config.json", "r") as f:
    data = json.load(f)


async def main():
    blue_strong.print("Your mission:")
    blue.print(
        "\t 1) implement factory function that will allow you to deploy contracts"
    )
    blue.print("\t 2) deploy account contract")
    blue.print("\t 3) deploy another account contract through your account contract")
    blue.print("\t 4) deploy a contract that the evaluator has chosen\n")

    private_key = data["PRIVATE_KEY"]
    stark_key = private_to_stark_key(private_key)

    #
    # Initialize StarkNet Client
    #
    client = get_client()
    #
    # Compile and Deploy `factory.cairo`
    #
    account, factory_addr = await compile_deploy(
        client=client, contract=data["FACTORY"], args=[stark_key], account=True
    )

    #
    # Transfer ETH to pay for fees
    #
    reward_account = await fund_account(factory_addr)
    if not reward_account:
        red.print("Account must have ETH to cover transaction fees")
        return

    _, evaluator_address = await get_evaluator(client)
    declare_tx = await account.sign_declare_transaction(
        compilation_source=["./factory/factoried.cairo"], max_fee=data["MAX_FEE"]
    )
    declared = await account.declare(declare_tx)

    # TODO: Deploy factory from factory
    calldata = [
        factory_addr,
        get_selector_from_name("deploy_contract"),
        5,
        declared.class_hash,
        1,
        1,
        2,
        0,
    ]
    nonce = await account.get_contract_nonce(factory_addr)
    invoke = InvokeFunction(
        calldata=calldata,
        signature=[],
        max_fee=data["MAX_FEE"],
        version=1,
        nonce=nonce,
        contract_address=factory_addr,
    )
    resp = await account.send_transaction(invoke)
    await print_n_wait(account, resp)

    #
    # Check answer against 'evaluator.cairo'
    #
    calldata = [
        evaluator_address,
        get_selector_from_name("validate_factory"),
        1,
        reward_account,
    ]

    nonce = await account.get_contract_nonce(factory_addr)

    invoke = InvokeFunction(
        calldata=calldata,
        signature=[],
        max_fee=data["MAX_FEE"],
        version=1,
        nonce=nonce,
        contract_address=factory_addr,
    )

    resp = await account.send_transaction(invoke)
    await print_n_wait(account, resp)


asyncio.run(main())
