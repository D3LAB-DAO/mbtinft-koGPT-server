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
import os
import json
from Crypto.Hash import keccak


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
        * "nonce": task giver's counter which indicates how many txs are sent.
        * "mode":
            * 0: writing
            * 1: chatting
            * 2: QnA
            * 3: three-line acrostic poem (三行詩)
        * "prompt": input text.
        * "temperature": 0.8 as default.
        * "max_length": 128 as default. min 1. max 1024.
        * "deadline": deadline of request.

    :return: JSON, including hashed key of set of (request, response) in server.
    """
    logger.info('Upload start.')

    """read JSON"""
    params = request.get_json()
    address: str = params["address"]  # must
    nonce: int = params["nonce"]  # must
    mode: int = params.get("mode", 0)
    prompt: str = params.get("prompt", '')
    temperature: float = params.get("temperature", 0.8)
    max_length: int = params.get("max_length", 128)

    """get key"""
    raw_key = address + str(nonce) + str(deadline)
    k = keccak.new(digest_bits=256)
    k.update(raw_key.encode())
    hashed_key = k.hexdigest()
    # print(hashed_key)

    """DB"""
    # 1. (hashed_key => (input, output))
    prev = db.get(hashed_key.encode())
    if prev is None:
        d = {"input": params}
        db.put(hashed_key.encode(), json.dumps(d).encode())
        logger.info('Data of key "' + hashed_key + '" successfully put.')
    else:
        logger.warning('Data of key "' + hashed_key + '" already exists.')
        logger.warning('Upload done with WARNING.')
        return jsonify(
            {
                "error": {
                    "code": 409,
                    "message": 'Key "' + hashed_key + '" already exists.'
                }
            }
        )
    # 2. (address => list of hashed_key)
    prev = db.get(address.encode())
    if prev is None:
        d = {"keys": [hashed_key]}
    else:
        d = json.loads(prev.decode())
        l = d.get("keys", list())  # must
        d["keys"] = l.append(hashed_key)
    db.put(address.encode(), json.dumps(d).encode())
    logger.info('Data of key "' + hashed_key + '" successfully put to "' + address + '".')

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
    result: str = params.get("result", '')

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
        d["output"] = {"result": result}
        # TODO: output already exists.
        db.put(key.encode(), json.dumps(d).encode())
        logger.info('Result of key "' + key + '" successfully put."')

    """return"""
    # next: server enrolls the response at contract.
    logger.info('Inference done.')
    return jsonify({})


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
                "result": result
            }
        }
    )


def history():
    """
    Same as batch_download.
    """
    # ret = db.multi_get([b"key1", b"key2", b"key3"])
    # print(ret[b"key1"])
    # print(ret[b"key3"])
    pass


def remove():
    # db.delete(b"key")
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=33327)
