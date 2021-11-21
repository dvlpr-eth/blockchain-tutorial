import json

from web3 import Web3
from solcx import compile_standard, install_solc
import os
from dotenv import load_dotenv

load_dotenv()

with open("./SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()

# We add these two lines that we forgot from the video!
print("Installing...")
install_solc("0.6.0")

# Solidity source code
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                }
            }
        },
    },
    solc_version="0.6.0",
)

with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)


# get bytecode
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

# get abi
abi = json.loads(
    compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["metadata"]
)["output"]["abi"]


# For connecting to ganache
w3 = Web3(Web3.HTTPProvider(os.getenv("HTTP_PROIVIDER")))
chain_id = int(os.getenv("CHAIN_ID"))
my_address = os.getenv("OWNER_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")

# Create the contract in Python
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)
# Get the latest transaction
nonce = w3.eth.getTransactionCount(my_address)

transactionProps = {
    "gasPrice": w3.eth.gas_price,
    "chainId": chain_id,
    "from": my_address,
}

# Submit the transaction that deploys the contract
transaction = SimpleStorage.constructor().buildTransaction(
    {
        **transactionProps,
        "nonce": nonce,
    }
)

# Sign the transaction
print("Signing contract...")
signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
print("Deploting contract...")
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
print("Waiting for transaction receipt...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("Contract deployed! 🚀")
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
print(f"Initial Stored Value {simple_storage.functions.retrieve().call()}")

print("Updating contract ...")
greeting_transaction = simple_storage.functions.store(15).buildTransaction(
    {
        **transactionProps,
        "nonce": nonce + 1,
    }
)
signed_greeting_txn = w3.eth.account.sign_transaction(greeting_transaction, private_key)
tx_greeting_hash = w3.eth.send_raw_transaction(signed_greeting_txn.rawTransaction)
print("Updating stored Value...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_greeting_hash)
print(f"Updated Stored Value {simple_storage.functions.retrieve().call()}")
