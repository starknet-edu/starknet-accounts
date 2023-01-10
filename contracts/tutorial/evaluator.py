 ####
# Tutorial Deployment:
# - deploy 'player_registry'
# - deploy 'TDERC20'
# - deploy 'evaluator'
 ####
import os
import sys
import json
import asyncio

sys.path.append('./')

from console import blue_strong, blue
from utils import compile_deploy, get_client, get_account, devnet_height_check

with open(os.path.abspath(os.path.dirname(__file__)) + "/../config.json", "r") as f:
  data = json.load(f)

async def main():
    devnet_height_check()
    client = get_client()
    account = get_account(client)
    
    blue_strong.print("Evaluator Deployment only run on Devnet:")

    # Deploy 
    registry, reg_addr = await compile_deploy(
        account,
        data['PLAYER_REGISTRY'],
        [account.address],
    )
    blue.print("\tRegistry - 0x{:x}".format(reg_addr))

    erc20, erc20_addr = await compile_deploy(
        account,
        data['ERC20'],
        [data['ERC20_NAME'], data['ERC20_SYMBOL'], data['ERC20_DECIMAL'], account.address],
    )
    blue.print("\tERC20 - 0x{:x}".format(erc20_addr))

    _, evaluator_addr = await compile_deploy(
        account,
        data['EVALUATOR'],
        [data['PRIVATE_KEY'], data['PUBLIC_KEY'], data['INPUT_1'], data['INPUT_2'], erc20_addr, reg_addr, account.address],
    )
    
    prep = registry.functions['set_exercise_or_admin'].prepare(evaluator_addr, 1)
    await prep.invoke(max_fee=data['MAX_FEE'])
    
    prep = erc20.functions['set_teacher'].prepare(evaluator_addr, 1)
    await prep.invoke(max_fee=data['MAX_FEE'])

    blue.print("\tEvaluator - 0x{:x}".format(evaluator_addr))

asyncio.run(main())
