import streamlit as st
import plotly.express as px

# 페이지 제목 설정
st.title('Plotly 막대 그래프')

fig = px.bar(x=["a", "b", "c"], y=[1, 2, 3])


# Streamlit에서 Plotly 그래프 표시
st.plotly_chart(fig)
