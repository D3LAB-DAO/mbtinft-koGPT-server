"""Inference daemon.
@Author: Lukepark
@Email: lukepark327@gmail.com

TODO:
    * call inference task(s) from priority queue written in Solidity.
"""
from web3 import Web3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from time import sleep


app = Flask(__name__)
CORS(app)


"""load model"""
# from https://github.com/kakaobrain/kogpt#python
tokenizer = AutoTokenizer.from_pretrained(
    # or float32 version: revision=KoGPT6B-ryan1.5b
    'kakaobrain/kogpt', revision='KoGPT6B-ryan1.5b-float16',
    bos_token='[BOS]', eos_token='[EOS]', unk_token='[UNK]', pad_token='[PAD]', mask_token='[MASK]'
)
model = AutoModelForCausalLM.from_pretrained(
    # or float32 version: revision=KoGPT6B-ryan1.5b
    'kakaobrain/kogpt', revision='KoGPT6B-ryan1.5b-float16',
    pad_token_id=tokenizer.eos_token_id, torch_dtype='auto', low_cpu_mem_usage=True
).to(device='cuda', non_blocking=True)
# _ = model.eval()
print("Model Loaded.")


SPLITTER = "---"


@app.route('/')
def hello_world():
    return 'Hello World!\n'


@app.route('/writing', methods=['POST'])
def writing():
    params = request.get_json()
    prompt = params['prompt']

    try:
        temperature = params['temperature']
    except(KeyError):
        temperature = 0.8

    try:
        max_length = params['max_length']
    except(KeyError):
        max_length = 128

    return inference(prompt, temperature, max_length, original_length=len(prompt))


@app.route('/three', methods=['POST'])
def three():
    params = request.get_json()
    prompt = params['prompt']

    original_length=len(prompt)

    prefix = """
    휴지통---
    휴: 휴지통에
    지: 지저분한 쓰레기를
    통: 통채로 집어넣었다
    ---
    홍길동---
    홍: 홍대감의 아들
    길: 길동이는
    동: 동물 사냥을 좋아했다.
    ---
    냉장고---
    냉: 냉장고는 김
    장: 장한 김치를
    고: 고이 저장할 수 있다
    ---
    코로나---
    코: 코 앞으로 다가온 올해의 마지막 끝자락, 잠시 멈추어 1년을 돌아본다.
    로: 오랜 시간 버티고 견디며 애썼을 그대들의 얼굴이 주마등처럼 지나간다. 올해가 가기 전 내 마음을 가득 담아 인사를 건네본다.
    나: 나중에 밥 한 끼 해요. 마스크 벗고.
    ---
    코로나---
    코: 코로나19로 인해 힘들고 지쳐진 우리의 삶, 우리의 인생의
    로: 로드맵이 정해져 있지 않지만,
    나: 나는 오늘도 묵묵히 주어진 삶을 살아가야지!
    ---
    서장훈---
    서: 서장훈은 성공한 농구스타다.
    장: 장훈이는 성공한 방송인이다. 그런데 그는 지금
    훈: 훈자다(혼자다).
    ---
    소나기---
    소: 소방차가 불난 집 불을 끈다.
    나: 나는 신나게 구경을 했다.
    기: 기절했다. 우리 집이었다.
    ---
    아이돌---
    아: 아저씨
    이: 이제 좀 자리로
    돌: 돌아가세요. 안 보여요.
    ---
    양세형---
    양: 양아치 양아치
    세: 세상에 이런 양아치가 있나
    형: 형편없는 자식
    ---
    """
    postfix = """
    ---
    """
    prompt = prefix + prompt + postfix

    try:
        temperature = params['temperature']
    except(KeyError):
        temperature = 0.8

    try:
        max_length = params['max_length']
    except(KeyError):
        max_length = 128

    return inference(prompt, temperature, max_length, original_length=original_length)


@app.route('/qna', methods=['POST'])
def qna():
    params = request.get_json()
    prompt = params['prompt']

    original_length=len(prompt)

    if prompt[-1] != '?':
        prompt = prompt + '?'

    # refer: https://support.google.com
    # refer: https://www.navercorp.com/investment/faq
    # refer: https://www.gov.kr/portal/faq
    prefix = """
    대한민국의 날씨는 어때?---
    사계절이 뚜렷합니다.
    ---
    밥 먹었어?---
    네 먹었어요. 당신은 밥 먹었나요?
    ---
    Google Workspace 계정 외부의 사용자를 그룹에 추가할 수 있나요?---
    예. 관리자는 외부 공급업체, 클라이언트, 고객 등을 그룹에 추가할 수 있습니다. Google 관리 콘솔에서 추가하면 됩니다. 관리자가 Groups for Business 공유 설정에서 외부 회원을 허용하면 다른 사용자도 그룹에 외부 회원을 추가할 수 있습니다.
    ---
    그룹이 사용자의 주소록 페이지에 표시되나요?---
    예. 하지만 사용자가 그룹에 메일을 보낸 후에만 표시되며 사용자가 메일을 보낸 그룹은 전체 주소록 아래에 표시됩니다.
    ---
    Google 그룹스에서 만든 그룹은 Google 주소록의 그룹 기능과 어떻게 다른가요?---
    그룹스와 Google 주소록에서는 모두 메일링 리스트를 사용하는 사용자 그룹에 손쉽게 이메일을 보낼 수 있습니다. 차이점이 있다면 주소록에서 만든 메일링 리스트는 공유할 수 없다는 것입니다. 주소록의 메일링 리스트는 개인 용도로 사용되지만 그룹스에 있는 이메일 주소는 모든 사용자가 사용할 수 있습니다.
    ---
    그룹에 보내는 메일을 검토할 수 있나요?---
    예. 그룹에 메일이 게시되기 전에 검토할 수 있습니다.
    ---
    관리자가 게시한 메일도 검토되나요?---
    아니요. 검토 대상 그룹에 관리자가 전송한 메일은 관리자가 해당 그룹의 회원이라고 해도 검토되지 않습니다. 이러한 정책은 다른 관리자가 만든 검토 대상 그룹에도 적용됩니다. 단, 스팸으로 표시된 메시지는 예외입니다. 이러한 메시지는 시스템에서 전송되지 않습니다.
    ---
    네이버(주) 설립 연도는?---
    네이버(주)는 1999년 네이버컴 설립을 시작으로 2000년 한게임과의 합병으로 엔에이치엔주식회사가 되었습니다. 이어 2013년 8월 1일, 한게임 사업부문의 인적분할로 네이버 주식회사로 사명이 변경되었습니다.
    ---
    보조금24란 어떤 서비스인가요?---
    정부에서 개인·가구에게 제공하는 각종 혜택(보조금)을 확인하기 위해 행정기관이나 부처별 누리집을 방문하여 서비스 내용을 확인하지 않고도 정부24를 통해 내가 받을 수 있는 혜택을 쉽고 편리하게 확인할 수 있는 맞춤안내 서비스입니다.
    ---
    """
    postfix = """
    ---
    """
    prompt = prefix + prompt + postfix

    try:
        temperature = params['temperature']
    except(KeyError):
        temperature = 0.8

    try:
        max_length = params['max_length']
    except(KeyError):
        max_length = 128

    return inference(prompt, temperature, max_length, original_length=original_length)


@app.route('/chat', methods=['POST'])
def chat():
    params = request.get_json()
    prompt = params['prompt']

    original_length=len(prompt)

    prefix = """
    나 가끔 롤하는 동영상 봐---
    와 재미있겠다!
    ---
    오늘 스트레스 받은거 풀려고 감자 2봉지나 먹었다---
    맛있게 먹었어?
    ---
    사무용품 중에 뭐 필요한거 없어?---
    딱히 필요없어.
    ---
    님들 한손에서 두손은 안돼요?---
    나도 두손 하고싶다.
    ---
    언제 출발한다고요?---
    5시 반 좀 넘으면 출발할려고 합니다.
    ---
    저희서비스 앱vs웹중에 웹이라고 해야하는거죠?---
    네, 둘중에선 웹이 더 자연스러운 것 같습니다!
    ---
    3시 정도까지 노션 결과제출 페이지 좀 꾸미고 있을게요---
    네 감사합니다.
    ---
    이 말풍선들이 나오는 과정이 탈중앙화된 AI의 추론과정을 거쳐서 나오는거다 라고 설명해도 괜찮나요?---
    응 맞아ㅋㅋㅋ
    ---
    저희 아까 얘기 나눴던거는 다 고쳤고 마지막 페이지만 마무리하면 됩니다!---
    굳굳굳
    ---
    """
    postfix = """
    ---
    """
    prompt = prefix + prompt + postfix

    try:
        temperature = params['temperature']
    except(KeyError):
        temperature = 0.8

    try:
        max_length = params['max_length']
    except(KeyError):
        max_length = 128

    return inference(prompt, temperature, max_length, original_length=original_length)


def inference(prompt, temperature, max_length, original_length=0):
    send_inference()

    with torch.no_grad():
        tokens = tokenizer.encode(prompt, return_tensors='pt').to(device='cuda', non_blocking=True)
        gen_tokens = model.generate(tokens, do_sample=True, temperature=temperature, max_length=len(prompt) + max_length)
        generated = tokenizer.batch_decode(gen_tokens)[0]

    return generated[len(prompt)-original_length:].split(SPLITTER)[0]


# Get setting
SETTING = json.load(open('./setting.json', 'r'))

# Get http provider
INFURA_HTTP_PROVIDER = SETTING['http_provider']


def web3():
    w3 = Web3(Web3.HTTPProvider(INFURA_HTTP_PROVIDER))
    if not w3.isConnected():
        raise(ConnectionError)
    return w3


# web3 connection
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

    tx_hash = send_tx(tx, 800000)  # GAS_AMOUNT
    print("Tx Hash\t\t:", tx_hash)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    status = receipt["status"]
    print("Tx Status\t:", "Success" if status == 1 else "False")

    return True if status == 1 else False


def get_max():
    return MbtiNft_CONTRACT.functions.getMax(
        # ...
    ).call()


def main():
    while True:
        id_, p_ = get_max()
        if id_ != 0:
            send_inference()
        sleep(5)


if __name__ == "__main__":
    # main()
    app.run(host='0.0.0.0', port=33328)
