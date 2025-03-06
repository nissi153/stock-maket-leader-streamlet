import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from AirtableAPI import AirtableAPI

# 한국 시간대 설정
kst = ZoneInfo('Asia/Seoul')

st.set_page_config(
    page_title="시장 분석 대시보드",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container {padding-top: 3rem; padding-bottom: 0rem;}
    </style>
""", unsafe_allow_html=True)

def fetch_market_data():
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
    with st.spinner('데이터를 가져오는 중...'):
        return fetch_market_data()

data = update_data()

st.title(f"📊 실시간 주도주 탐색기 ({datetime.now(kst).strftime('%H:%M:%S')})")

if st.button('🔄 새로고침', use_container_width=True):
    data = update_data()

if not data or 'market_analysis' not in data:
    st.error("데이터를 불러올 수 없습니다.")
else:
    st.info(data['market_analysis']['overview'])
    
    themes = data['market_analysis']['leading_themes']
    col1, col2 = st.columns(2)

    with col1:
        for theme in themes[::2]:
            st.markdown(f"##### {theme['name']}")
            st.markdown(f"<p>{theme['news']}</p>", unsafe_allow_html=True)
            df = pd.DataFrame(theme['stocks'], columns=['종목명', '종목코드', '등락율', '거래대금'])
            df['등락율'] = df['등락율'].astype(str) + '%'
            df['거래대금'] = df['거래대금'].astype(str) + '억'
            st.dataframe(df, hide_index=True, width=400)

    with col2:
        for theme in themes[1::2]:
            st.markdown(f"##### {theme['name']}")
            st.markdown(f"<p>{theme['news']}</p>", unsafe_allow_html=True)
            df = pd.DataFrame(theme['stocks'], columns=['종목명', '종목코드', '등락율', '거래대금'])
            df['등락율'] = df['등락율'].astype(str) + '%'
            df['거래대금'] = df['거래대금'].astype(str) + '억'
            st.dataframe(df, hide_index=True, width=400)

    all_stocks = [stock for theme in themes for stock in theme['stocks']]
    df_all = pd.DataFrame(all_stocks, columns=['종목명', '종목코드', '등락율', '거래대금'])
    df_all['거래대금_숫자'] = pd.to_numeric(df_all['거래대금'].str.replace('억', ''), errors='coerce').round(0)
    df_all = df_all.sort_values('거래대금_숫자', ascending=True).tail(10)

    fig = px.bar(df_all, x='거래대금_숫자', y='종목명', orientation='h', title='종목별 거래대금 (억원)')
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    show_market_analysis()