"""Inference server.
@Author: Lukepark
@Email: lukepark327@gmail.com

TODO:
    * change DB to IPFS.
    * support various NNs.
    * add PPLM.
"""
import logging
import rocksdb
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
from Crypto.Hash import keccak


# Get setting
SETTING = json.load(open('./setting.json', 'r'))
INFERENCE_URL = SETTING['inference_url']


logger = logging.getLogger(__name__)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
fileHandler = logging.FileHandler('./server.log')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.setLevel(level=logging.DEBUG)
logger.info('Server start.')


db = rocksdb.DB("server.db", rocksdb.Options(create_if_missing=True))


app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    return 'Hello World!\n'


@app.route('/upload', methods=['POST'])
def upload():
    """
    Same as request.
    User uploads text to server to request inference.

    JSON data includes:
        * "address": task giver's address.
        * "tokenId": which NFT token.
        * "nonce": task giver's counter which indicates how many txs are sent.
        * "mode":
            * 0: writing
            * 1: chatting
            * 2: QnA
            * 3: three-line acrostic poem (三行詩)
        * "prompt": input text.
        * "temperature": 0.8 as default.
        * "max_length": 128 as default. min 1. max 1024.

    :return: JSON, including hashed key of set of (request, response) in server.
    """
    logger.info('Upload start.')

    """read JSON"""
    params = request.get_json()
    address: str = params["address"]  # must
    tokenId: int = params["tokenId"]  # must
    nonce: int = params["nonce"]  # must
    mode: int = params.get("mode", 0) or 0
    prompt: str = params.get("prompt", '') or ''
    temperature: float = params.get("temperature", 0.8) or 0.8
    max_length: int = params.get("max_length", 128) or 128
    params = {
        "address": address,
        "tokenId": tokenId,
        "nonce": nonce,
        "mode": mode,
        "prompt": prompt,
        "temperature": temperature,
        "max_length": max_length
    }

    """get key"""
    # TODO: sync with solidity keccak256
    raw_key = address + str(tokenId) + str(nonce)
    k = keccak.new(digest_bits=256)
    k.update(raw_key.encode())
    hashed_key = k.hexdigest()
    # print(hashed_key)

    """DB"""
    # 1. (hashed_key => (input, output))
    prev = db.get(hashed_key.encode())
    if prev is not None:
        logger.warning('Data of key "' + hashed_key + '" already exists.')
        # logger.warning('Upload done with WARNING.')
        # return jsonify(
        #     {
        #         "error": {
        #             "code": 409,
        #             "message": 'Key "' + hashed_key + '" already exists.'
        #         }
        #     }
        # )
        db.delete(hashed_key.encode())
    d = {"input": params}
    db.put(hashed_key.encode(), json.dumps(d).encode())
    logger.info('Data of key "' + hashed_key + '" successfully put.')

    # 2. (address + tokenId => list of hashed_key)
    address_and_tokenId = address + str(tokenId)
    k = keccak.new(digest_bits=256)
    k.update(address_and_tokenId.encode())
    hashed_address_and_tokenId = k.hexdigest()
    # print(hashed_address_and_tokenId)

    prev = db.get(hashed_address_and_tokenId.encode())
    if prev is None:
        d = {"keys": [hashed_key]}
    else:
        d = json.loads(prev.decode())
        l = d.get("keys", list()) or list()  # must
        d["keys"] = l.append(hashed_key)

    db.put(hashed_address_and_tokenId.encode(), json.dumps(d).encode())
    logger.info('Data of key "' + hashed_key + '" successfully put to "' + address + '" and tokenId "' + str(tokenId) + '".')

    """return"""
    # next: user enrolls the request at contract.
    logger.info('Upload done.')
    return jsonify(
        {
            "data": {
                "key": hashed_key
            }
        }
    )


def cancle():
    pass


@app.route('/inference', methods=['POST'])
def inference():
    """
    Same as response.
    Server responses user's request one by one.

    JSON data includes:
        * "key": key of task.
        * "result": inference result.
    """
    logger.info('Inference start.')

    """read JSON"""
    params = request.get_json()
    key: str = params["key"]  # must
    # result: str = params.get("result", '') or ''  # See below `get result` comment

    """DB"""
    # (key => (input, output))
    prev = db.get(key.encode())
    if prev is None:
        logger.warning('Data of key "' + key + '" not exists.')
        logger.warning('Inference done with WARNING.')
        return jsonify(
            {
                "error": {
                    "code": 404,
                    "message": 'Data of key "' + key + '" not exists.'
                }
            }
        )
    else:
        d = json.loads(prev.decode())

        # get result
        try:
            result: str = params["result"]
        except(KeyError):
            mode = d["input"]["mode"]
            prompt = d["input"]["prompt"]
            temperature = d["input"]["temperature"]
            max_length = d["input"]["max_length"]

            if mode == 0:  # writing
                api = "writing"
            elif mode == 1:  # chatting
                api = "chat"
            elif mode == 2:  # QnA
                api = "qna"
            elif mode == 3:  # three-line acrostic poem (三行詩)
                api = "three"

            result: str = requests.post(
                INFERENCE_URL + api,
                json={
                    "mode": mode,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_length": max_length
                }
            ).text

        d["output"] = {"result": result}
        # TODO: output already exists.
        db.put(key.encode(), json.dumps(d).encode())
        logger.info('Result of key "' + key + '" successfully put."')

    """return"""
    # next: server enrolls the response at contract.
    logger.info('Inference done.')
    return jsonify({
        "data": {
            "result": result
        }
    })


@app.route('/download', methods=['POST'])
def download():
    """
    Same as check.
    User checks existence of server's response about key.
    Server gets task params.

    JSON data includes:
        * "key": key of task.

    :return: JSON, including response.
    """
    logger.info('Download start.')

    """read JSON"""
    params = request.get_json()
    key: str = params["key"]  # must

    """DB"""
    # (key => (input, output))
    prev = db.get(key.encode())
    if prev is None:
        logger.warning('Data of key "' + key + '" not exists.')
        logger.warning('Download done with WARNING.')
        return jsonify(
            {
                "error": {
                    "code": 404,
                    "message": 'Data of key "' + key + '" not exists.'
                }
            }
        )
    else:
        d = json.loads(prev.decode())
        try:
            prompt = d["input"]["prompt"]
            result = d["output"]["result"]
        except(KeyError):
            logger.warning('Result of key "' + key + '" not exists.')
            logger.warning('Download done with WARNING.')
            return jsonify(
                {
                    "error": {
                        "code": 404,
                        "message": 'Result of key "' + key + '" not exists.'
                    }
                }
            )
        logger.info('Result of key "' + key + '" successfully get."')

    """return"""
    logger.info('Download done.')
    return jsonify(
        {
            "data": {
                "prompt": prompt,
                "result": result
            }
        }
    )


@app.route('/keys', methods=['POST'])
def keys():
    """
    User gets list of keys.

    JSON data includes:
        * "address": address to get keys.
        * "tokenId": tokenId to get keys.

    :return: JSON, keys.
    """
    logger.info('Keys start.')

    """read JSON"""
    params = request.get_json()
    address: str = params["address"]  # must
    tokenId: str = params["tokenId"]  # must
    # TODO: boundary

    """DB"""
    # (address _ tokenId => list of hashed_key)
    address_and_tokenId = address + str(tokenId)
    k = keccak.new(digest_bits=256)
    k.update(address_and_tokenId.encode())
    hashed_address_and_tokenId = k.hexdigest()
    # print(hashed_address_and_tokenId)

    prev = db.get(hashed_address_and_tokenId.encode())
    d = json.loads(prev.decode())
    l = d.get("keys", list()) or list()
    # TODO: Exception

    logger.info('Address "' + address + '"and tokenId "' + str(tokenId) + '" is inquired.')

    """return"""
    # next: user enrolls the request at contract.
    logger.info('Keys done.')
    return jsonify(
        {
            "data": {
                "keys": l
            }
        }
    )


@app.route('/history', methods=['POST'])
def history():
    """
    Same as batch_download.

    JSON data includes:
        * "address": address to get history.
        * "tokenId": tokenId to get history.

    :return: JSON, batch of (input, output).
    """
    logger.info('History start.')

    """read JSON"""
    params = request.get_json()
    address: str = params["address"]  # must
    tokenId: str = params["tokenId"]  # must
    # TODO: boundary

    """DB"""
    # (address _ tokenId => list of hashed_key)
    address_and_tokenId = address + str(tokenId)
    k = keccak.new(digest_bits=256)
    k.update(address_and_tokenId.encode())
    hashed_address_and_tokenId = k.hexdigest()
    # print(hashed_address_and_tokenId)

    prev = db.get(hashed_address_and_tokenId.encode())
    d = json.loads(prev.decode())
    l = d.get("keys", list()) or list()
    # TODO: Exception

    logger.info('Address "' + address + '" and tokenId "' + str(tokenId) + '" is inquired.')

    history = db.multi_get([b.encode() for b in l])
    history = {k.decode(): v.decode() for k, v in history.items()}  # decode

    """return"""
    # next: user enrolls the request at contract.
    logger.info('History done.')
    return jsonify(
        {
            "data": {
                "history": history
            }
        }
    )


@app.route('/remove', methods=['POST'])
def remove():
    # db.delete(b"key")
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=33327)
