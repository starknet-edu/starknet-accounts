#######################
# Tutorial Deployment:
# - deploy 'player_registry'
# - deploy 'TDERC20'
# - deploy 'evaluator'
#######################
import os
import json
import asyncio
import requests

from utils import compile_deploy
from starknet_py.net.client import Client

devnet="http://localhost:5000"

with open("hints.json", "r") as f:
  data = json.load(f)

client = Client(net=devnet, chain="testnet")

async def deploy_player_registry():
    return await compile_deploy(
        client,
        data['PLAYER_REGISTRY'],
        [data['DEVNET_ADDRESS']],
    )

async def deploy_erc20():
    return await compile_deploy(
        client,
        data['ERC20'],
        [data['ERC20_NAME'], data['ERC20_SYMBOL'], data['ERC20_DECIMAL'], data['DEVNET_ADDRESS']],
    )

async def deploy_evaluator(registry, erc20):
    dep = await compile_deploy(
        client,
        data['EVALUATOR'],
        [data['PRIVATE_KEY'], data['PUBLIC_KEY'], data['INPUT_1'], data['INPUT_2'], erc20, registry, data['DEVNET_ADDRESS']],
    )

    payload = json.dumps(data['REGISTRY_PERMISSION'])
    response = requests.request("POST", devnet+"/gateway/add_transaction", data=payload)

    payload = json.dumps(data['ERC20_PERMISSION'])
    response = requests.request("POST", devnet+"/gateway/add_transaction", data=payload)

    return dep

async def main():
    registry = await deploy_player_registry()
    print("\u001b[35mRegistry:\t0x{:x}".format(registry.contract_address))

    erc20 = await deploy_erc20()
    print("ERC20:\t\t0x{:x}".format(erc20.contract_address))

    evaluator = await deploy_evaluator(registry.contract_address, erc20.contract_address)
    print("Evaluator:\t0x{:x}\u001b[0m".format(evaluator.contract_address))

asyncio.run(main())
