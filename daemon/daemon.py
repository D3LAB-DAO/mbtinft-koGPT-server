"""Inference daemon.
@Author: Lukepark
@Email: lukepark327@gmail.com

TODO:
    * call inference task(s) from priority queue written in Solidity.
    * logging
"""
from web3 import Web3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from time import sleep


# Get setting
SETTING = json.load(open('./setting.json', 'r'))
INFURA_HTTP_PROVIDER = SETTING['http_provider']
GAS_AMOUNT = SETTING['gas_amount']
SLEEP_TIME = SETTING['sleep_time']

DEV_MODE = SETTING['dev_mode']
DEV_INFERENCE_SERVER = SETTING['dev_server']
if DEV_MODE:
    import requests


def web3():
    w3 = Web3(Web3.HTTPProvider(INFURA_HTTP_PROVIDER))
    if not w3.isConnected():
        raise(ConnectionError)
    return w3


w3 = web3()

# Get wallet info
WALLET_ADDR = w3.toChecksumAddress(SETTING['my_addr'])
WALLET_PRIVATEKEY = SETTING['my_pk']

# Get ABIs
CGV_ABI = json.load(open('./abis/CGV.json'))['abi']
ChingGu_ABI = json.load(open('./abis/ChingGu.json'))['abi']
MbtiNft_ABI = json.load(open('./abis/MbtiNft.json'))['abi']

# Get contract addresses.
CGV_ADDR = w3.toChecksumAddress(SETTING['cgv'])
ChingGu_ADDR = w3.toChecksumAddress(SETTING['chinggu'])
MbtiNft_ADDR = w3.toChecksumAddress(SETTING['mbtinft'])

# Set contract
CGV_CONTRACT = w3.eth.contract(address=CGV_ADDR, abi=CGV_ABI)
ChingGu_CONTRACT = w3.eth.contract(address=ChingGu_ADDR, abi=ChingGu_ABI)
MbtiNft_CONTRACT = w3.eth.contract(address=MbtiNft_ADDR, abi=MbtiNft_ABI)


def send_tx(tx, gas):
    print("Send Tx Enter")
    tx.update({
        "gas": gas,
        "nonce": w3.eth.getTransactionCount(WALLET_ADDR, "pending")  # TODO: why pending?
    })
    signed_tx = w3.eth.account.signTransaction(tx, WALLET_PRIVATEKEY)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return tx_hash.hex()


def send_inference():
    tx = MbtiNft_CONTRACT.functions.inference(
        # ...
    ).buildTransaction({
        "from": WALLET_ADDR
    })

    tx_hash = send_tx(tx, GAS_AMOUNT)
    print("Tx Hash\t\t:", tx_hash)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    status = receipt["status"]
    print("Tx Status\t:", "Success" if status == 1 else "False")

    return True if status == 1 else False


def get_max():
    return MbtiNft_CONTRACT.functions.getMax(
        # ...
    ).call()


def get_key(id_):
    return MbtiNft_CONTRACT.functions.keys(
        id_
    ).call()


def main():
    counter = 0
    while True:
        id_, p_ = get_max()  # See queue
        if id_ != 0:  # If some elements exist
            """Test Purpose Only
            Instead of using Brain-chain, for a comfortability,
            (Ethereum testnet) + (Inference server) can be used.
            """
            # TODO: [async] aiohttp
            result: str = requests.post(
                DEV_INFERENCE_SERVER + 'inference',
                json={
                    "key": get_key(id_).hex()
                }
            ).text
            # TODO: logging

            """inference"""
            try:
                send_inference()  # Request inference to Brain-chain
            except:
                pass

            print("===")
        else:
            print("Skip:", counter, end='\r')
            counter += 1

        sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
