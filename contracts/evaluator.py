#######################
# Tutorial Deployment:
# - deploy 'player_registry'
# - deploy 'TDERC20'
# - deploy 'evaluator'
#######################
import json
import asyncio

from utils import compile_deploy, get_account_client, devnet_height_check

with open("hints.json", "r") as f:
  data = json.load(f)

async def main():
    devnet_height_check()
    
    print("\u001b[35mEvaluator Deployment only run on Devnet:")
    acc_client, acc_addr = get_account_client()

    # Deploy 
    registry, reg_addr = await compile_deploy(
        acc_client,
        data['PLAYER_REGISTRY'],
        [acc_addr],
    )
    print("\tRegistry - 0x{:x}".format(reg_addr))

    erc20, erc20_addr = await compile_deploy(
        acc_client,
        data['ERC20'],
        [data['ERC20_NAME'], data['ERC20_SYMBOL'], data['ERC20_DECIMAL'], acc_addr],
    )
    print("\tERC20 - 0x{:x}".format(erc20_addr))

    _, evaluator_addr = await compile_deploy(
        acc_client,
        data['EVALUATOR'],
        [data['PRIVATE_KEY'], data['PUBLIC_KEY'], data['INPUT_1'], data['INPUT_2'], erc20_addr, reg_addr, acc_addr],
    )

    await(
        await registry.functions['set_exercise_or_admin'].invoke(evaluator_addr, 1, max_fee=data['MAX_FEE'])
    ).wait_for_acceptance()

    await(
        await erc20.functions['set_teacher'].invoke(evaluator_addr, 1, max_fee=data['MAX_FEE'])
    ).wait_for_acceptance()

    print("\tEvaluator - 0x{:x}\u001b[0m".format(evaluator_addr))

asyncio.run(main())
