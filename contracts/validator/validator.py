import os
import asyncio

from pathlib import Path
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.crypto.signature.signature import private_to_stark_key

async def main():
    client = Client("testnet")

    os.system("starknet-compile validator.cairo --output validator_compiled.json")

    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)

    compiled = Path("validator_compiled.json").read_text()
    validator = await Contract.deploy(
        client, compiled_contract=compiled, constructor_args=[private_key, stark_key, 2938, 4337]
    )
    os.system("rm validator_compiled.json")
    await client.wait_for_tx(validator.hash)
    res = await client.get_transaction(validator.hash)
    print("VALIDATOR: 0x{:02x}".format(res.transaction.contract_address))

    os.system("starknet-compile ACT.cairo --output ACT_compiled.json")
    compiled = Path("ACT_compiled.json").read_text()
    ACT = await Contract.deploy(
        client, compiled_contract=compiled, constructor_args=[res.transaction.contract_address]
    )
    os.system("rm ACT_compiled.json")
    await client.wait_for_tx(ACT.hash)
    act_res = await client.get_transaction(ACT.hash)
    print("ACT: 0x{:02x}".format(act_res.transaction.contract_address))

    invocation = await validator.functions["set_rewards_contract"].prepare(
        addr=ACT.contract_address
    ).invoke(max_fee=0)

    await print_n_wait(client, invocation)

asyncio.run(main())
