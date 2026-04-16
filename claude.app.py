import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
# -------------------------------
# 기본 설정
# -------------------------------
st.set_page_config(page_title="AI 정산안내 어시스턴트", layout="wide")
st.title("💬 AI 정산안내 어시스턴트 (파일럿 버전)")
st.caption("롯데백화점 정산회계팀 | Self-service 기반 AI 응대 시연용 앱")
# -------------------------------
# 데이터 불러오기 (예시용)
# -------------------------------
@st.cache_data
def load_data():
    data = pd.read_csv("data/sample_data.csv")
    return data
df = load_data()
# -------------------------------
# 사이드바 메뉴
# -------------------------------
menu = st.sidebar.radio("메뉴 선택", ["거래처용 정산안내", "내부용 응대 도우미", "예외관리 대시보드"])
# -------------------------------
# 1️⃣ 거래처용 AI 정산안내
# -------------------------------
if menu == "거래처용 정산안내":
    st.header("🏢 거래처용 AI 정산안내")
    st.write("거래처가 직접 정산 상태를 조회하고, AI에게 자연어로 문의할 수 있는 시나리오입니다.")
    
    cust_name = st.text_input("거래처명 입력", "롯데상사")
    query = st.text_area("문의 내용 입력", "이번 달 지급 예정 금액이 얼마인가요?")
    
    if st.button("AI에게 물어보기"):
        # 예시 로직 (실서비스에서는 OpenAI API or 사내용 모델 연동)
        sample_responses = [
            f"{cust_name}의 2024년 5월 지급 예정 금액은 48,200,000원입니다. (승인 완료 건 기준)",
            f"현재 {cust_name}의 세금계산서는 3건 승인 대기 중이며, 예정 지급일은 {datetime.today()+timedelta(days=7):%Y-%m-%d} 입니다.",
            f"정산 금액이 전월 대비 줄어든 이유는 2건의 보완 요청(서류 미제출) 때문입니다."
        ]
        st.success(random.choice(sample_responses))
# -------------------------------
# 2️⃣ 내부용 AI 응대 도우미
# -------------------------------
elif menu == "내부용 응대 도우미":
    st.header("👩‍💼 내부용 AI 응대 도우미")
    st.write("담당자가 거래처 문의를 받을 때 빠르게 상태를 요약하고, 답변 초안을 생성하는 시나리오입니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        vendor = st.selectbox("거래처 선택", df["거래처명"].unique())
    with col2:
        inv_num = st.text_input("세금계산서 번호", "INV20240515-001")
    
    if st.button("응답 초안 생성"):
        row = df[df["거래처명"] == vendor].sample(1).iloc[0]
        st.info("📄 상태 요약")
        st.write(f"- 승인상태: {row['승인상태']}")
        st.write(f"- 금액: {row['금액']:,}원")
        st.write(f"- 지급예정일: {row['지급예정일']}")
        
        st.success(f"✉️ **AI 추천 답변 초안:**\n\n"
                   f"'{vendor}'의 '{inv_num}' 건은 현재 **{row['승인상태']}** 상태이며, "
                   f"지급 예정일은 **{row['지급예정일']}**입니다. "
                   "추가 서류가 필요한 경우 별도 안내드리겠습니다.")
# -------------------------------
# 3️⃣ 예외관리 대시보드
# -------------------------------
elif menu == "예외관리 대시보드":
    st.header("⚠️ 예외관리 대시보드")
    st.write("승인대기, 반려, 지연 등의 건을 한눈에 보고 우선순위를 정리하는 탭입니다.")
    
    exception_df = df[df["승인상태"].isin(["승인대기", "반려"])]
    st.metric("예외 건수", len(exception_df))
    
    st.dataframe(exception_df.style.highlight_max(subset=["금액"], color="#ffd6cc"))
    
    top_vendor = exception_df["거래처명"].value_counts().index[0]
    st.info(f"🔍 현재 ‘{top_vendor}’ 거래처의 문의 빈도가 가장 높습니다.")
