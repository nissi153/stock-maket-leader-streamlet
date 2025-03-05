import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
from datetime import datetime, timedelta
from screenshot import capture_and_send_screenshot
from AirtableAPI import AirtableAPI


# 초기 설정을 함수로 분리
def initialize_session_state():
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'last_fetch_time' not in st.session_state:
        st.session_state.last_fetch_time = None
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0
    if 'next_refresh_time' not in st.session_state:
        st.session_state.next_refresh_time = datetime.now()


# 세션 상태 초기화
initialize_session_state()

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

        # 가장 최신 분석 결과 가져오기
        results = airtable.get_table_data('analysis_results')

        if results is None or results.empty:
            st.error("데이터를 찾을 수 없습니다.")
            return None

        # 가장 최신 데이터 선택
        latest_result = results.iloc[0]['result']

        try:
            data = json.loads(latest_result)
            st.session_state.error_count = 0  # 성공시 에러 카운트 리셋
            return data

        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {str(e)}")
            st.session_state.error_count += 1
            return None

    except Exception as e:
        st.error(f"데이터 가져오기 실패: {str(e)}")
        st.session_state.error_count += 1
        return None


def should_fetch_data():
    """데이터를 새로 가져와야 하는지 확인하는 함수"""
    current_time = datetime.now()

    # 데이터가 없거나 마지막 fetch 시간이 없는 경우
    if st.session_state.data is None or st.session_state.last_fetch_time is None:
        st.session_state.next_refresh_time = current_time + timedelta(minutes=5)
        return True

    # 에러가 3번 이상 발생하면 자동 새로고침 중지
    if st.session_state.error_count >= 3:
        st.session_state.auto_refresh = False
        st.error("연속된 에러로 인해 자동 새로고침이 중지되었습니다.")
        return False

    # 현재 시간이 다음 새로고침 시간을 지났는지 확인
    if current_time >= st.session_state.next_refresh_time:
        st.session_state.next_refresh_time = current_time + timedelta(minutes=5)
        return True

    return False


def update_data():
    """데이터를 업데이트하는 함수"""
    if should_fetch_data():
        with st.spinner('데이터를 가져오는 중...'):
            new_data = fetch_market_data()
            if new_data:  # 데이터 가져오기 성공한 경우에만 업데이트
                st.session_state.data = new_data
                st.session_state.last_fetch_time = datetime.now()
                st.session_state.next_refresh_time = datetime.now() + timedelta(minutes=5)
                return True
    return False


def highlight_positive(val):
    """양수/음수 값을 하이라이트하는 함수"""
    if isinstance(val, str):
        try:
            # 문자열에서 +/- 기호 제거하고 숫자로 변환해보기
            num_val = float(val.replace('+', '').replace('%', ''))
            if num_val > 0:
                return 'background-color: #e5ffe5; color: #ff0000'  # 초록색 (양수)
            elif num_val < 0:
                return 'background-color: #ffe5e5; color: #28a745'  # 빨간색 (음수)
        except ValueError:
            pass
    return ''


def truncate_string(text, max_length=8):
    """문자열을 지정된 길이로 제한하는 함수"""
    if pd.isna(text):
        return ""
    return str(text)[:max_length] if len(str(text)) > max_length else str(text)


def show_market_analysis():
    """시장 분석 데이터를 표시하는 메인 함수"""
    # 현재 시간 표시
    current_time = datetime.now().strftime("%H:%M:%S")
    st.title(f"📊실시간 주도주 탐색기({current_time})")

    # 컨트롤 요소들을 한 줄에 배치하고 세로 중앙 정렬
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button('🔄새로고침', use_container_width=True):
            st.session_state.error_count = 0  # 수동 새로고침시 에러 카운트 리셋
            st.session_state.next_refresh_time = datetime.now() + timedelta(minutes=5)
            update_data()

    with col2:
        auto_refresh = st.checkbox(
            '자동 새로고침',
            value=st.session_state.auto_refresh,
            key='auto_refresh_checkbox'
        )
        if auto_refresh != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh
            if auto_refresh:
                st.session_state.next_refresh_time = datetime.now() + timedelta(minutes=5)

    with col3:
        timer_placeholder = st.empty()
        if st.session_state.auto_refresh:
            current_time = datetime.now()
            time_diff = (st.session_state.next_refresh_time - current_time).total_seconds()

            if time_diff <= 0:
                update_data()
                st.session_state.next_refresh_time = datetime.now() + timedelta(minutes=5)
                time_diff = 300

            minutes = int(time_diff // 60)
            seconds = int(time_diff % 60)
            time_str = f"{minutes}분 {seconds}초" if minutes > 0 else f"{seconds}초"

            timer_placeholder.markdown(f"<p class='timer-text'>⏱️ 다음 새로고침: <b>{time_str}</b></p>",
                                       unsafe_allow_html=True)

    # with col4:
    #     if st.button('📸 스크린샷', use_container_width=True):
    #         with st.spinner('스크린샷을 생성하고 전송하는 중...'):
    #             result = capture_and_send_screenshot()
    #             if result.get('success', False):
    #                 st.success('스크린샷이 성공적으로 전송되었습니다.')
    #             else:
    #                 st.error(f'스크린샷 전송 실패: {result.get("message", "알 수 없는 오류")}')

    # 데이터가 없으면 가져오기
    if st.session_state.data is None:
        update_data()

    data = st.session_state.data
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
            styled_df = df.style.applymap(highlight_positive, subset=['등락율'])
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
            styled_df = df.style.applymap(highlight_positive, subset=['등락율'])
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

    # 자동 리프레시 부분
    if st.session_state.auto_refresh:
        time.sleep(0.5)  # 대기 시간을 0.5초로 설정
        st.rerun()  # Streamlit의 rerun 사용


if __name__ == "__main__":
    show_market_analysis()