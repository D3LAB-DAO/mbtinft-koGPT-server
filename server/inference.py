"""Inference server.
@Author: Lukepark
@Email: lukepark327@gmail.com
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import koGPT


app = Flask(__name__)
CORS(app)


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

    return koGPT.inference(prompt, temperature, max_length, cutFrom=0)


@app.route('/three', methods=['POST'])
def three():
    params = request.get_json()
    prompt = params['prompt']

    prefix =\
        """휴지통
휴: 휴지통에
지: 지저분한 쓰레기를
통: 통채로 집어넣었다

홍길동
홍: 홍대감의 아들
길: 길동이는
동: 동물 사냥을 좋아했다.

냉장고
냉: 냉장고는 김
장: 장한 김치를
고: 고이 저장할 수 있다

코로나
코: 코 앞으로 다가온 올해의 마지막 끝자락, 잠시 멈추어 1년을 돌아본다.
로: 오랜 시간 버티고 견디며 애썼을 그대들의 얼굴이 주마등처럼 지나간다. 올해가 가기 전 내 마음을 가득 담아 인사를 건네본다.
나: 나중에 밥 한 끼 해요. 마스크 벗고.

코로나
코: 코로나19로 인해 힘들고 지쳐진 우리의 삶, 우리의 인생의
로: 로드맵이 정해져 있지 않지만,
나: 나는 오늘도 묵묵히 주어진 삶을 살아가야지!

서장훈
서: 서장훈은 성공한 농구스타다.
장: 장훈이는 성공한 방송인이다. 그런데 그는 지금
훈: 훈자다(혼자다).

소나기
소: 소방차가 불난 집 불을 끈다.
나: 나는 신나게 구경을 했다.
기: 기절했다. 우리 집이었다.

아이돌
아: 아저씨
이: 이제 좀 자리로
돌: 돌아가세요. 안 보여요.

양세형
양: 양아치 양아치
세: 세상에 이런 양아치가 있나
형: 형편없는 자식

"""
    postfix =\
        """
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

    return koGPT.inference(prompt, temperature, max_length, cutFrom=len(prompt))


@app.route('/qna', methods=['POST'])
def qna():
    params = request.get_json()
    prompt = params['prompt']

    if prompt[-1] != '?':
        prompt = prompt + '?'
    if prompt[:3] != 'Q: ':
        prompt = 'Q: ' + prompt

    # refer: https://support.google.com
    # refer: https://www.navercorp.com/investment/faq
    # refer: https://www.gov.kr/portal/faq
    prefix =\
        """Q: 대한민국의 날씨는 어때?
A: 사계절이 뚜렷합니다.

Q: Google Workspace 계정 외부의 사용자를 그룹에 추가할 수 있나요?
A: 예. 관리자는 외부 공급업체, 클라이언트, 고객 등을 그룹에 추가할 수 있습니다. Google 관리 콘솔에서 추가하면 됩니다. 관리자가 Groups for Business 공유 설정에서 외부 회원을 허용하면 다른 사용자도 그룹에 외부 회원을 추가할 수 있습니다.

Q: 그룹이 사용자의 주소록 페이지에 표시되나요?
A: 예. 하지만 사용자가 그룹에 메일을 보낸 후에만 표시되며 사용자가 메일을 보낸 그룹은 전체 주소록 아래에 표시됩니다.

Q: Google 그룹스에서 만든 그룹은 Google 주소록의 그룹 기능과 어떻게 다른가요?
A: 그룹스와 Google 주소록에서는 모두 메일링 리스트를 사용하는 사용자 그룹에 손쉽게 이메일을 보낼 수 있습니다. 차이점이 있다면 주소록에서 만든 메일링 리스트는 공유할 수 없다는 것입니다. 주소록의 메일링 리스트는 개인 용도로 사용되지만 그룹스에 있는 이메일 주소는 모든 사용자가 사용할 수 있습니다.

Q: 그룹에 보내는 메일을 검토할 수 있나요?
A: 예. 그룹에 메일이 게시되기 전에 검토할 수 있습니다.

Q: 관리자가 게시한 메일도 검토되나요?
A: 아니요. 검토 대상 그룹에 관리자가 전송한 메일은 관리자가 해당 그룹의 회원이라고 해도 검토되지 않습니다. 이러한 정책은 다른 관리자가 만든 검토 대상 그룹에도 적용됩니다. 단, 스팸으로 표시된 메시지는 예외입니다. 이러한 메시지는 시스템에서 전송되지 않습니다.

Q: 네이버(주) 설립 연도는?
A: 네이버(주)는 1999년 네이버컴 설립을 시작으로 2000년 한게임과의 합병으로 엔에이치엔주식회사가 되었습니다. 이어 2013년 8월 1일, 한게임 사업부문의 인적분할로 네이버 주식회사로 사명이 변경되었습니다.

Q: 보조금24란 어떤 서비스인가요?
A: 정부에서 개인·가구에게 제공하는 각종 혜택(보조금)을 확인하기 위해 행정기관이나 부처별 누리집을 방문하여 서비스 내용을 확인하지 않고도 정부24를 통해 내가 받을 수 있는 혜택을 쉽고 편리하게 확인할 수 있는 맞춤안내 서비스입니다.

"""
    postfix =\
        """
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

    result = koGPT.inference(prompt, temperature, max_length, cutFrom=len(prompt))

    if result[:3] == 'A: ':
        result = result[3:]

    return result


@app.route('/chat', methods=['POST'])
def chat():
    params = request.get_json()
    prompt = params['prompt']

    if prompt[:3] != 'A: ':
        prompt = 'A: ' + prompt

    prefix =\
        """
A: 나 가끔 롤하는 동영상 봐
B: 와 재미있겠다!

A: 오늘 스트레스 받은거 풀려고 감자 2봉지나 먹었다
B: 맛있게 먹었어?

A: 사무용품 중에 뭐 필요한거 없어?
B: 딱히 필요없어

A: 님들 한손 모션에서 두손 모션은 안돼요?
B: 나도 두손무기 쓰고싶다

A: 언제 출발한다고요?
B: 5시 반 좀 넘으면 출발할려고 합니다

A: 저희서비스 앱vs웹중에 웹이라고 해야하는거죠?
B: 네, 둘중에선 웹이 더 자연스러운 것 같습니다!

A: 3시 정도까지 결과 제출 페이지 좀 꾸미고 있을게요
B: 네 감사합니다

A: 이 말풍선들이 나오는 과정이 탈중앙화된 AI의 추론과정을 거쳐서 나오는거다 라고 설명해도 괜찮나요?
B: 응 맞아ㅋㅋㅋㅋㅋㅋㅋㅋ

A: 저희 아까 얘기 나눴던거는 다 고쳤고 마지막 페이지만 마무리하면 됩니다!
B: 굳굳굳

"""
    postfix =\
        """
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

    result = koGPT.inference(prompt, temperature, max_length, cutFrom=len(prompt))

    if result[:3] == 'B: ':
        result = result[3:]

    return result


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=33328)
