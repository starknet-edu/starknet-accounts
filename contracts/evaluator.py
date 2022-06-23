import os
import asyncio

from pathlib import Path
from starknet_py.contract import Contract
from starknet_py.net.client import Client

#######################
# Tutorial Deployment:
# - deploy 'player_registry'
# - deploy 'TDERC20'
# - deploy 'evaluator'
#######################

# client = Client("testnet")
client = Client(net="http://localhost:5000", chain="testnet")
first_teacher = 0x0769f21aa31b543e971a5eb0501aa781da55e71e907e2fe3800ce18de7535645
PRIVATE_KEY = 28269553036454149273332760011886696253239742350009903329945699224417844975
PUBLIC_KEY = 1397467974901608740509397132501478376338248400622004458128166743350896051882
INPUT_1 = 2938
INPUT_2 = 4337

async def deploy_player_registry():
    registry_path = "utils/player_registry_compiled.json"
    os.system("starknet-compile utils/player_registry.cairo --output "+registry_path)

    compiled = Path(registry_path).read_text()
    registry = await Contract.deploy(
        client, compiled_contract=compiled, constructor_args=[first_teacher]
    )
    os.system("rm "+registry_path)
    await client.wait_for_tx(registry.hash)

    res = await client.get_transaction(registry.hash)
    return res.transaction.contract_address

async def deploy_erc20():
    erc20_path = "token/ACT_compiled.json"
    os.system("starknet-compile token/TDERC20.cairo --output "+erc20_path)

    compiled = Path(erc20_path).read_text()
    erc20 = await Contract.deploy(
        client, compiled_contract=compiled, constructor_args=[4711718965522363507, 4277076, 18, first_teacher]
    )
    os.system("rm "+erc20_path)
    await client.wait_for_tx(erc20.hash)

    res = await client.get_transaction(erc20.hash)
    return res.transaction.contract_address

async def deploy_evaluator(registry, erc20):
    evaluator_path = "evaluator_compiled.json"
    os.system("starknet-compile evaluator.cairo --output "+evaluator_path)

    compiled = Path(evaluator_path).read_text()
    evaluator = await Contract.deploy(
        client, 
        compiled_contract=compiled, 
        constructor_args=[PRIVATE_KEY, PUBLIC_KEY, INPUT_1, INPUT_2, registry, erc20, first_teacher]
    )
    os.system("rm "+evaluator_path)
    await client.wait_for_tx(evaluator.hash)

    res = await client.get_transaction(evaluator.hash)
    return res.transaction.contract_address

async def main():
    regAddr = await deploy_player_registry()
    print("Player Registry: ".format(regAddr))

    erc20Addr = await deploy_erc20()

    evaluatorAddr = await deploy_evaluator(regAddr, erc20Addr)
    print("Evaluator: 0x{:x}".format(evaluatorAddr))

asyncio.run(main())
