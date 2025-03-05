@ECHO OFF
CALL conda activate py38_64 || (
    ECHO conda 환경 활성화 실패
    EXIT /b 1
)

CD /D "C:\Users\user\Documents\GitHub\AutoTrading\frontMiniProject" || (
    ECHO 디렉토리 변경 실패
    EXIT /b 1
)

streamlit run streamlit_app.py