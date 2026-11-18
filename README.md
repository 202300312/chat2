# 모두를 위한 학교 콘서트장 설계하기 v17

## 변경 사항
- 일반 질문에 잘한 점/개선할 점/확인이 필요한 자료의 3단 구성을 강제하던 문제를 수정했습니다.
- LED 조명 교체의 실제 환경 효과에 필요한 자료를 묻는 경우 소비전력(W), 조명 수, 사용시간(h), 밝기(lx/lm), 전력량(kWh), 선택적 전력 배출계수를 근거로 명확히 답합니다.
- 질문에 설계도와의 비교가 필요할 때만 설계 배치 데이터를 AI에 전달하여 엉뚱한 평가 문장을 줄였습니다.
- PDF 설계도 점수 평가 기능 및 기존 레이아웃·저장 기능은 유지합니다.

## 실행
```powershell
cd "C:\Users\jh869\Desktop\eco_concert_designer_v17"
C:\Users\jh869\envchat\.venv\Scripts\python.exe -m pip install -r requirements.txt
C:\Users\jh869\envchat\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8517
```

브라우저: http://localhost:8517

교사 컴퓨터에서 Ollama 및 `qwen3:1.7b`가 실행되어야 일반 자유질문에 대한 AI 생성 답변이 동작합니다. 계정은 기존과 같습니다. v16 데이터베이스와는 독립입니다.
