<div align="center">
    <img src="./misc/abstract.jpg" style="width: 350px">
    <h1>StarkNet Account Abstraction</h1>
    <br>

|Exercise|Topic|
|---|---|
|[hello](contracts/hello)|hello account world|
|[signature](contracts/signature)|handling Stark signatures|
|[multicall](contracts/multicall)|multiple contract call account|
|[multisig](contracts/multisig)|multiple signature account
|[abstraction](contracts/abstraction)|unique account architecture|
</div>

# Setup

This tutorial uses the [cairo environment](https://www.cairo-lang.org/docs/quickstart.html) and [starknet.py](https://github.com/software-mansion/starknet.py). Each exercise comes with a python helper script which includes:

- mission objectives
- contract deployment functions
- [validator](./contracts/validator) interactions

```bash
# assumes you're using python3.7
python3.7 -m venv ~/cairo_venv
source ~/cairo_venv/bin/activate
pip3 install --upgrade starknet.py
pip3 install --upgrade pytest pytest-asyncio
pip3 install --upgrade cairo-lang

# libraries for abstraction demo(assumes git)
git clone git@github.com:starkware-libs/cairo-examples.git ~/cairo_venv/lib/python3.7/site-packages/cairo_examples
find ~/cairo_venv/lib/python3.7/site-packages/cairo_examples/secp -type f -exec sed -i -e 's/from big/from cairo_examples.secp.big/g' {} \;
find ~/cairo_venv/lib/python3.7/site-packages/cairo_examples/secp -type f -exec sed -i -e 's/from secp/from cairo_examples.secp.secp/g' {} \;

# set environment variables
export STARKNET_NETWORK=alpha-goerli
export VALIDATOR_ADDRESS=0x197c942a62c77d18249adef3c6a8fd89b8725330b43640a5f05850a871fb401
export WALLET_ADDRESS=<e.g. ARGENT/BRAVOS wallet address>
```

Deploying contracts can take some time, so we've implemented a cache of your deployed addresses at `contracts/account.json`. If you've made a change to your contract and wish to deploy fresh simply delete the line from `account.json` or set `export ACCOUNT_CACHE=false`.

The contract stubs and helper scripts will be mising crucial information for you to figure out and the excercises will get increasingly difficult(and worth more [points](https://goerli.voyager.online/contract/0x6f9a9435928b768b671c036e72c07d50b1af4d68c4cbfd60ed4c970bf41c77)(the points are not real and can't be transferred)).

If you hit a roadblock the first place to look is the deployed [validator contract](https://goerli.voyager.online/contract/0x197c942a62c77d18249adef3c6a8fd89b8725330b43640a5f05850a871fb401) and what it is checking for. We recommend [testing](https://www.cairo-lang.org/docs/hello_starknet/unit_tests.html?highlight=test) your contract before attempting to deploy/validate.

```bash
cd tests
pytest -s hello.py
```

***!!!DON'T CHEAT!!!***

...but if you need help you can reference the [Open Zeppelin](https://github.com/OpenZeppelin/cairo-contracts/tree/main/src/openzeppelin/account) account contracts or `hints/<TOPIC>` branch of this repository.

# Walk Through

Accounts on StarkNet are deployed via an [Account Abstraction](https://perama-v.github.io/cairo/account-abstraction) model.

TL;DR:

***accounts on StarkNet are simply contracts***

One caveat for account contract deployments is they must have a canonical entrypoint denoted with the selector `__execute__`.

***...and that's it!***

Lets deploy and test the simplest account contract we can:

```bash
cd contracts/hello
python3 hello.py
```

The job of an account contract is to execute arbitrary business logic on behalf of a sepcific entity. This is why we see a similar argument pattern for most execute functions:

```bash
    # contract we wish to execute our transaction on
    contract_address : felt
    
    # entry point of that contract we wish to call
    selector : felt

    # contracts will require varying lengths of calldata so we pass an array
    calldata_len : felt
    calldata : felt*
```

## [Signatures](./contracts/signatures)

Unlike Ethereum [EOAs](https://ethereum.org/en/developers/docs/accounts/#externally-owned-accounts-and-key-pairs), StarkNet accounts don't have a hard requirement on being managed by a public/private key pair.

Account abstraction cares more about `who`(i.e. the contract address) rather than `how`(i.e. the signature).

This leaves the ECDSA signature scheme up to the developer and is typically implemented using the [pedersen hash](https://docs.starknet.io/docs/Hashing/hash-functions) and native Stark curve:

```bash
cd contracts/signature
python3 signature_1.py
```

The `signature_1` contract has no concept of a public/private keypair. All the signing was done "off-chain" and yet with account abstraction we're still able to operate a functioning account with a populated signature field.

Let's couple the signing logic more succintly wtih the account:

***HINT: we have not yet implemented a [nonce](https://ethereum.org/en/developers/docs/accounts/#an-account-examined)***

```bash
cd contracts/signature
python3 signature_2.py
```

Although we are free to populate the signature field how we please, the StarkNet OS has a specific method for hashing [transaction data](https://docs.starknet.io/docs/Blocks/transactions#transaction-hash-1).

This transaction hash encompasses all the relevant `tx_info`, and typically the message_hash signed by account contracts. The account owner is thereby acknowledging all of the relevant transaction information:

```bash
cd contracts/signature
python3 signature_3.py
```

## [MultiCall](./contracts/multicall)

Now that we have implemented the vanilla ECDSA signing mechanisms lets see what account abstraction can really do!

A `multicall` aggregates the results from multiple contract calls. This reduces the number of seperate API Client or JSON-RPC requests that need to be sent. In addition it acts as an `atomic` invocation where all values are returned for the same block

There are many implementations of multicall that allow the caller flexibility in how they distribute and batch their transactions.

Let's implement a multicall account for StarkNet:

```bash
cd contracts/multicall
python3 multicall.py
```

## [MultiSig](./contracts/multisig)

A `multisig` or multiple signature wallet allows you to share security accross multiple signinging entities. You can think of them like bank vaults in that they require more than one key to unlock, or in this case authorize a transaction.

The amount of signing keys that belong to the account and the ammount of keys required to authorize a transaction are purely implementation details.

Lets implement a `2/3 multisig` account(i.e. 2 signatures are required out of a total 3 signers for a transaction to be executed):

```bash
cd contracts/multisig
python3 multisig.py
```

## [Abstraction](./contracts/abstraction)

As StarkNet accounts are simply contracts we can implement any signing mechanism we want. Companies like [Web3Auth](https://medium.com/toruslabs/sign-in-with-starkware-711d48f2dbbd) are using this to create `Sign-In` architectures using your StarkNet account. [JWT](https://github.com/BoBowchan/cairo-jsonwebtoken) token schems are being implemented.

Discussions on novel account architecutres are popping up more and [more](https://vitalik.ca/general/2022/01/26/soulbound.html) and it looks to be an increasingly important tool in the developer toolkit.

For an example of a unique account architecture we will build a contract that implements it's signatures scheme with the `secp256k1` curve and `sha256` instead of our native StarkNet curve:

```bash
cd contracts/abstraction
python3 abstraction.py
```
