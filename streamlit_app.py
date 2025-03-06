import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
from datetime import datetime, timedelta
# from screenshot import capture_and_send_screenshot
from AirtableAPI import AirtableAPI

from zoneinfo import ZoneInfo


# 한국 시간대 설정
kst = ZoneInfo('Asia/Seoul')

# 페이지 설정
st.set_page_config(
    page_title="시장 분석 대시보드",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS 스타일 정의
st.markdown("""
    <style>
        .block-container {padding-top: 3rem; padding-bottom: 0rem;}
        div[data-testid="stMarkdownContainer"] > h3 {margin-bottom: 0.5rem;}
        thead tr th:first-child {padding-left: 0;}
        tbody tr td:first-child {padding-left: 0;}
        .css-k1ih3n {padding: 0.5rem 0;}
        .theme-news {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        .overview-text {
            font-size: 16px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .error-message {
            color: #ff4b4b;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            background-color: #ffe5e5;
        }
        .success-message {
            color: #28a745;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            background-color: #e5ffe5;
        }
        .element-container {
            display: flex;
            align-items: center;
        }
        .stButton > button {
            height: 42px;
        }
        .timer-text {
            margin: 0;
            padding-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)


def fetch_market_data():
    """Airtable에서 데이터를 가져오는 함수"""
    try:
        airtable = AirtableAPI()
        results = airtable.get_table_data('analysis_results')

        if results is None or results.empty:
            st.error("데이터를 찾을 수 없습니다.")
            return None

        latest_result = results.iloc[0]['result']

        try:
            data = json.loads(latest_result)
            return data

        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {str(e)}")
            return None

    except Exception as e:
        st.error(f"데이터 가져오기 실패: {str(e)}")
        return None


def update_data():
    """데이터를 업데이트하는 함수"""
    with st.spinner('데이터를 가져오는 중...'):
        return fetch_market_data()


def highlight_positive(val):
    """양수/음수 값을 하이라이트하는 함수"""
    try:
        # 값이 문자열이면 변환
        if isinstance(val, str):
            val = float(val.replace('+', '').replace('%', ''))

        if val > 0:
            return 'background-color: #e5ffe5; color: #ff0000'  # 양수 (초록 배경, 빨강 글씨)
        elif val < 0:
            return 'background-color: #ffe5e5; color: #28a745'  # 음수 (빨강 배경, 초록 글씨)
    except (ValueError, TypeError):
        return ''
    return ''


def truncate_string(text, max_length=8):
    """문자열을 지정된 길이로 제한하는 함수"""
    if pd.isna(text):
        return ""
    return str(text)[:max_length] if len(str(text)) > max_length else str(text)


def show_market_analysis():
    """시장 분석 데이터를 표시하는 메인 함수"""
    current_time = datetime.now(kst).strftime("%H:%M:%S")
    st.title(f"📊실시간 주도주 탐색기({current_time})")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button('🔄새로고침', use_container_width=True):
            data = update_data()
        
    data = fetch_market_data()  # 초기 데이터 로드
    
    if not data or 'market_analysis' not in data:
        st.error("데이터를 불러올 수 없습니다.")
        return

    # 시장 개요
    st.info(data['market_analysis']['overview'])

    # 테마 정보를 2개의 컬럼으로 표시
    themes = data['market_analysis']['leading_themes']
    col1, col2 = st.columns(2)

    # 짝수/홀수 테마로 나누기
    with col1:
        for theme in themes[::2]:
            st.markdown(f"##### {theme['name']}")
            st.markdown(f"<p class='theme-news'>{theme['news']}</p>", unsafe_allow_html=True)

            df = pd.DataFrame(theme['stocks'],
                              columns=['종목명', '종목코드', '등락율', '거래대금'])
            # 등락율에 % 추가
            df['등락율'] = df['등락율'].astype(str) + '%'
            # 거래대금을 정수로 변환
            df['거래대금'] = df['거래대금'].str.replace(',', '').str.replace('억', '').astype(float).round(0).astype(int).astype(
                str) + '억'
            df['종목명'] = df['종목명'].apply(truncate_string)
            styled_df = df.style.map(highlight_positive, subset=['등락율'])
            st.dataframe(styled_df, hide_index=True, width=400)

    with col2:
        for theme in themes[1::2]:
            st.markdown(f"##### {theme['name']}")
            st.markdown(f"<p class='theme-news'>{theme['news']}</p>", unsafe_allow_html=True)

            df = pd.DataFrame(theme['stocks'],
                              columns=['종목명', '종목코드', '등락율', '거래대금'])
            # 등락율에 % 추가
            df['등락율'] = df['등락율'].astype(str) + '%'
            # 거래대금을 정수로 변환
            df['거래대금'] = df['거래대금'].str.replace(',', '').str.replace('억', '').astype(float).round(0).astype(int).astype(
                str) + '억'
            df['종목명'] = df['종목명'].apply(truncate_string)
            styled_df = df.style.map(highlight_positive, subset=['등락율'])
            st.dataframe(styled_df, hide_index=True, width=400)

    # 거래대금 상위 종목 차트
    st.write("### 🏆 거래대금 상위 종목")

    # 모든 종목의 거래대금 데이터 수집
    all_stocks = []
    for theme in themes:
        all_stocks.extend(theme['stocks'])

    # 거래대금 기준으로 정렬
    df_all = pd.DataFrame(all_stocks, columns=['종목명', '종목코드', '등락율', '거래대금'])
    df_all['종목명'] = df_all['종목명'].apply(truncate_string)
    df_all['거래대금_숫자'] = pd.to_numeric(
        df_all['거래대금'].str.replace(',', '').str.replace('억', ''),
        errors='coerce'
    ).round(0)  # 소수점 반올림
    df_all = df_all.sort_values('거래대금_숫자', ascending=True).tail(10)  # 상위 10개만 표시

    # Plotly를 사용한 가로 막대 차트
    fig = px.bar(df_all,
                 x='거래대금_숫자',
                 y='종목명',
                 orientation='h',
                 title='종목별 거래대금 (억원)',
                 labels={'거래대금_숫자': '거래대금 (억원)', '종목명': '종목명'})

    fig.update_layout(
        height=400,
        showlegend=False,
        margin=dict(l=20, r=50, t=40, b=20),  # 오른쪽 마진을 50으로 늘림
        uniformtext=dict(minsize=10, mode='show'),  # 텍스트 크기 조정
    )

    # x축 포맷 설정 - 소수점 제거
    fig.update_xaxes(
        tickformat=',d',  # 천 단위 구분자 사용, 소수점 없음
    )

    # 막대 차트의 텍스트 레이블 추가 및 포맷팅
    fig.update_traces(
        texttemplate='%{x:,.0f}',  # 소수점 없는 포맷
        textposition='outside',
        cliponaxis=False  # 축을 벗어나는 텍스트도 표시
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    show_market_analysis()