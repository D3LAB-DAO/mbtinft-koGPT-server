"""
Author: Lukepark
Email: lukepark327@gmail.com

TODO:
- change DB to IPFS.
- support various NNs.
- add PPLM.
"""

import os
import json
from Crypto.Hash import keccak


import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    '[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s'
)
fileHandler = logging.FileHandler('./server.log')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.setLevel(level=logging.DEBUG)

logger.info('Server start.')


import rocksdb

db = rocksdb.DB("server.db", rocksdb.Options(create_if_missing=True))


# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM

# # load model
# # from https://github.com/kakaobrain/kogpt#python
# tokenizer = AutoTokenizer.from_pretrained(
#         'kakaobrain/kogpt', revision='KoGPT6B-ryan1.5b-float16',  # or float32 version: revision=KoGPT6B-ryan1.5b
#         bos_token='[BOS]', eos_token='[EOS]', unk_token='[UNK]', pad_token='[PAD]', mask_token='[MASK]'
# )
# model = AutoModelForCausalLM.from_pretrained(
#         'kakaobrain/kogpt', revision='KoGPT6B-ryan1.5b-float16',  # or float32 version: revision=KoGPT6B-ryan1.5b
#         pad_token_id=tokenizer.eos_token_id,
#         torch_dtype='auto', low_cpu_mem_usage=True
# ).to(device='cuda', non_blocking=True)
# # _ = model.eval()
# print("Model Loaded.")


from flask_cors import CORS
from flask import Flask, request, jsonify

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
    raw_key = address + str(nonce) + str(mode) + prompt + \
        str(temperature) + str(max_length)
    k = keccak.new(digest_bits=256)
    k.update(raw_key.encode())
    hashed_key = k.hexdigest()
    # print(hashed_key)

    """DB"""
    # 1. (hashed_key => (input, output))
    prev = db.get(hashed_key.encode())
    if prev is None:
        d = {"input": params, "output": dict()}
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
    logger.info('Data of key "' + hashed_key +
                '" successfully put to "' + address + '".')

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


def inference():
    """
    Same as response.
    Server responses user's request one by one.
    """

    # # inference
    # with torch.no_grad():
    #     tokens = tokenizer.encode(prompt, return_tensors='pt').to(
    #         device='cuda', non_blocking=True)
    #     gen_tokens = model.generate(
    #         tokens, do_sample=True, temperature=temperature, max_length=max_length)
    #     generated = tokenizer.batch_decode(gen_tokens)[0]

    # return generated

    pass


def check():
    pass


def download():
    # ret = db.multi_get([b"key1", b"key2", b"key3"])
    # print(ret[b"key1"])
    # print(ret[b"key3"])
    pass


def history():
    pass


def remove():
    # db.delete(b"key")
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=33327)
