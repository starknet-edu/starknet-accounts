<div align="center">
    <img src="./misc/abstract.jpg" style="width: 350px">
    <h1>StarkNet Account Abstraction</h1>
    <br>
</div>

Welcome! This is an automated workshop that will explain what [account Abstraction](https://perama-v.github.io/cairo/account-abstraction)  is and how you can leverage it to create powerful custom acounts contracts.

## Introduction

### Disclaimer

​
Don't expect any kind of benefit from using this, other than learning a bunch of cool stuff about StarkNet, the first general purpose validity rollup on the Ethereum Mainnnet.
​
StarkNet is still in Alpha. This means that development is ongoing, and the paint is not dry everywhere. Things will get better, and in the meanwhile, we make things work with a bit of duct tape here and there!
​

### How it works

TL;DR: accounts on StarkNet are simply regular smart contracts. One caveat is that they MUST have canonical entrypoint denoted with the selectors:

- `__validate__`
- `__validate_declare__`
- `__execute__`

Your goal is to design account contracts that pass all the [evaluator.cairo](contracts/evaluator.cairo) checks and collect all the points available on StarkNet(Goerli).

This tutorial consists of various StarkNet `account contracts` and `starknet_py` helper scripts for compilation, deployment, and testing. It also includes an evaluator smart contract, that will check that the code you write in your account contract is correct.

To understand what is expected of you, execute the specified python script for each exercise and read the `mission statement` that will appear in your terminal. The exercises will get more difficult and will require you to:

- manipulate the python files
- write the relevant Cairo code.

These tasks will be annotated with the comment `# ACTION ITEM <NUM>`

### Where am I?

This workshop is the sixth in a series aimed at teaching how to build on StarkNet. Checkout out the following:

|Topic|GitHub repo|
|---|---|
|Learn how to read Cairo code |[Cairo 101](https://github.com/starknet-edu/starknet-cairo-101)|
|Deploy and customize an ERC721 NFT|[StarkNet ERC721](https://github.com/starknet-edu/starknet-erc721)|
|Deploy and customize an ERC20 token|[StarkNet ERC20](https://github.com/starknet-edu/starknet-erc20)|
|Build a cross layer application|[StarkNet messaging bridge](https://github.com/starknet-edu/starknet-messaging-bridge)|
|Debug your Cairo contracts easily|[StarkNet debug](https://github.com/starknet-edu/starknet-debug)|
|Design your own account contract (you are here)|[StarkNet account abstraction](https://github.com/starknet-edu/starknet-accounts)|

### Providing feedback & getting help

Once you are done working on this tutorial, your feedback would be greatly appreciated!

**Please fill out [this form](https://forms.reform.app/starkware/untitled-form-4/kaes2e) to let us know what we can do to make it better.**

​
And if you struggle to move forward, do let us know! This workshop is meant to be as accessible as possible; we want to know if it's not the case.

​
Do you have a question? Join our [Discord server](https://starknet.io/discord), register, and join channel #tutorials-support
​
Are you interested in following online workshops about learning how to dev on StarkNet? [Subscribe here](http://eepurl.com/hFnpQ5)

### Contributing

This project can be made better and will evolve as StarkNet matures. Your contributions are welcome! Here are things that you can do to help:

- Create a branch with a translation to your language
- Correct bugs if you find some
- Add an explanation in the comments of the exercise if you feel it needs more explanation
- Add exercises showcasing your favorite Cairo feature

## Getting ready to work

### Step 1 - Clone the repo

```bash
git clone https://github.com/starknet-edu/starknet-accounts
cd starknet-accounts
```

### Step 2 - Set up your environment

This tutorial uses the [cairo environment](https://www.cairo-lang.org/docs/quickstart.html), [starknet-devnet](https://github.com/Shard-Labs/starknet-devnet), and [starknet.py](https://github.com/software-mansion/starknet.py).

***Install the cairo environment***

Set up the environment following [these instructions](https://starknet.io/docs/quickstart.html#quickstart)

***Install dependencies***

```bash
pip3 install --upgrade -r requirements.txt
```

### Step 3 - Set up your devnet

Transactions take time to complete on [testnet](https://goerli.voyager.online) so you should develop and debug locally first.

Let's try it out with the `hello/hello.cairo` exercise. There are no `# ACTION ITEM`s that need to be completed for this exercise and we can simply test that it works.

#### 1) init devnet

```bash
starknet-devnet
```

#### 2) deploy evaluator

```bash
# NOTE: 
# - you do not have to deploy the validator for `testnet`
# - devnet contract details can be found in `contracts/accounts.json`
python3 contracts/tutorial/evaluator.py
```

#### 3) deploy/test hello contract

```bash
python3 contracts/hello/hello.py
```

The relevant evaluator contract addresses are saved to the `contracts/accounts.json` cache. For devnet testing the devnet contracts `MUST BE DELETED` everytime devnet is restarted. If you would like to disable this constract cache run:

```bash
export ACCOUNT_CACHE=false
```

There were no `action items` for you to complete so you should see a succesfull `PAYDAY!!!` response from the devnet evaluator contract.

### Step 4 - Deploying to testnet

When deploying to testnet fill out the relevant details in the `config.json` file under `TESTNET_ACCOUNT` for your StarkNet account to transfer fees and receive rewards.

#### [Argent-X](https://chrome.google.com/webstore/detail/argent-x/dlcobpjiigpikoobohmabehhmhfoodbb) Example

<div align="center">
    <img src="./misc/argent.png" style="width: 350px">
</div>

***ADDRESS***

- From the example wallet above you can copy the address(`0x0742B5662...6476f8f`)
- Paste the felt representation in the `config.json` `TESTNET_ACCOUNT` -> `ADDRESS`
- To get the felt represenation you can paste the address in this [conversion tool](https://util.turbofish.co).

***PRIVATE***

- Select the three vertical dots to display the wallet options
- Select `Export private key`
- Copy the private key from this screen and paste it in `config.json` `TESTNET_ACCOUNT` -> `PRIVATE`.

***PUBLIC***

- Select the three vertical dots to display the wallet options
- Select `View on Voyager`
- From the Voyager Block Explorer select the `READ Contract` -> `IMPLEMENTATION` tab
- Drop down the `get_signer` selector
- Select `Decimal` query
- Copy the public key from this screen and paste it in `config.json` `TESNET_ACCOUNT` -> `PUBLIC`

***Example `config.json`***
<div align="center">
    <img src="./misc/hints.png" style="width: 350px">
</div>

### Step 5 - Accounting for fees

Accounts on StarkNet must pay [fees](https://docs.starknet.io/docs/Fees/fee-mechanism) to cover the L1 footprint of their transaction. So the account details you enter must have Goerli ETH(~0.5 ETH) and can be funded either through the [starkgate bridge](https://goerli.starkgate.starknet.io) or [StarkNet Faucet](https://faucet.goerli.starknet.io).

After you have tested your contract locally you can test on `testnet` by passing the `--testnet` flag to the starknet_py script:

```bash
python3 hello/hello.py --testnet
```

### Step 6 - Using `answers`

If you need hints on tutorial solutions you can find them in the `answers` branch. These will include a pytest for you to run, the completed starknet_py, and the completed cairo contract.

### Contracts code and addresses

| Contract code | Contract on voyager   |
| -------------------------------------------------------------------- | --------- |
| [Points counter ERC20](contracts/tutorial/token/TDERC20.cairo)          | [0x0134b89cfb9735a407c58b1a454c40634b600ab1e5a37d8138015f025cc8af4f](https://goerli.voyager.online/contract/0x0134b89cfb9735a407c58b1a454c40634b600ab1e5a37d8138015f025cc8af4f) |
| [Evaluator](contracts/tutorial/evaluator.cairo)                               | [0x01bb626c068310ba990db71f7d51fe999c37053d42470aee35698577a44baec6](https://goerli.voyager.online/contract/0x01bb626c068310ba990db71f7d51fe999c37053d42470aee35698577a44baec6) |

## Working on the tutorial

### Exercise 1 - [Hello](./contracts/hello)

Lets deploy and test the simplest account contract we can, [`hello.cairo`](contracts/hello/hello.cairo):

```bash
python3 contracts/hello/hello.py
```

The job of an account contract is to execute arbitrary business logic on behalf of a sepcific entity. This is why we see a similar argument pattern for most [execute functions](contracts/hello/hello.cairo#L11).

Follow the prompt and collect 100 points.

### Exercise 2 - [Signatures](./contracts/signatures)

#### Signature 1

Unlike Ethereum [EOAs](https://ethereum.org/en/developers/docs/accounts/#externally-owned-accounts-and-key-pairs), StarkNet accounts don't have a hard requirement on being managed by a public/private key pair.

Account abstraction cares more about `who`(i.e. the contract address) rather than `how`(i.e. the signature).

This leaves the ECDSA signature scheme up to the developer and is typically implemented using the [pedersen hash](https://docs.starknet.io/docs/Hashing/hash-functions) and native Stark curve:

```bash
python3 contracts/signature/signature_1.py
```

The `signature_1` contract has no concept of a public/private keypair. All the signing was done "off-chain" and yet with account abstraction we're still able to operate a functioning account with a populated signature field.

Follow the prompt and collect 100 points.

#### Signature 2 - 200 pts

Let's couple the signing logic more succintly wtih the account:

***HINT: we have not yet implemented a [nonce](https://ethereum.org/en/developers/docs/accounts/#an-account-examined)***

```bash
python3 contracts/signature/signature_2.py
```

Although we are free to populate the signature field how we please, the StarkNet OS has a specific method for hashing [transaction data](https://docs.starknet.io/docs/Blocks/transactions#transaction-hash-1).

Follow the prompt and collect 200 points.

#### Signature 3 - 300 pts

As StarkNet accounts are simply contracts we can implement any signing mechanism we want. Companies like [Web3Auth](https://medium.com/toruslabs/sign-in-with-starkware-711d48f2dbbd) are using this to create `Sign-In` architectures using your StarkNet account. [JWT](https://github.com/BoBowchan/cairo-jsonwebtoken) token schems are being implemented.

Discussions on novel account architecutres are popping up more and [more](https://vitalik.ca/general/2022/01/26/soulbound.html) and it looks to be an increasingly important tool in the developer toolkit.

For an example of a unique account architecture we will build a contract that implements it's signatures scheme with the `secp256k1` curve and `sha256` instead of our native StarkNet curve:

```bash
python3 contracts/signature/signature_3.py
```

Follow the prompt and collect 300 points.

### Exercise 3 - [MultiCall](./contracts/multicall)

Now that we have implemented the vanilla ECDSA signing mechanisms lets see what account abstraction can really do!

A `multicall` aggregates the results from multiple contract calls. This reduces the number of seperate API Client or JSON-RPC requests that need to be sent. In addition it acts as an `atomic` invocation where all values are returned for the same block.

Popular wallet providers like [Argent](https://github.com/argentlabs/argent-contracts-starknet/blob/develop/contracts/ArgentAccount.cairo) and [Braavos](https://github.com/myBraavos/braavos-account-cairo) use this design to implement account contracts on StarkNet to accomodate a multicall or a single call with one scheme.

There are many implementations of multicall that allow the caller flexibility in how they distribute and batch their transactions.

Let's implement a multicall account for StarkNet:

```bash
python3 contracts/multicall/multicall.py
```

Follow the prompt and collect 500 points.

### Exercise 4 - [MultiSig](./contracts/multisig)

A `multisig` or multiple signature wallet like [Braavos](https://github.com/myBraavos/braavos-account-cairo) allows you to share security accross multiple signinging entities. You can think of them like bank vaults in that they require more than one key to unlock, or in this case authorize a transaction.

The amount of signing keys that belong to the account and the ammount of keys required to authorize a transaction are purely implementation details.

Lets implement a `2/3 multisig` account(i.e. 2 signatures are required out of a total 3 signers for a transaction to be executed):

```bash
python3 contracts/multisig/multisig.py
```

Follow the prompt and collect 1000 points.
