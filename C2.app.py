import streamlit as st
from datetime import datetime, timedelta

try:
    import anthropic
except ImportError:
    st.error("anthropic 패키지가 설치되지 않았습니다. requirements.txt에 `anthropic>=0.28.0`을 추가해 주세요.")
    st.stop()


st.set_page_config(
    page_title="거래처용 AI 정산안내",
    page_icon="🏬",
    layout="wide",
)

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }

    .header-banner {
        background: linear-gradient(135deg, #c8102e 0%, #9b0c24 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .header-banner h1 { margin: 0; font-size: 1.6rem; }
    .header-banner p  { margin: 0; opacity: 0.85; font-size: 0.9rem; }

    .user-bubble {
        background: #c8102e;
        color: white;
        padding: 0.8rem 1.1rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.4rem 0 0.4rem 20%;
        font-size: 0.9rem;
    }

    .ai-bubble {
        background: white;
        color: #333;
        padding: 0.8rem 1.1rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.4rem 20% 0.4rem 0;
        font-size: 0.9rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        border-left: 3px solid #c8102e;
    }

    .badge-pending  {
        background:#fff3cd;
        color:#856404;
        padding:2px 8px;
        border-radius:12px;
        font-size:0.75rem;
        font-weight:600;
    }

    .badge-approved {
        background:#d1e7dd;
        color:#0f5132;
        padding:2px 8px;
        border-radius:12px;
        font-size:0.75rem;
        font-weight:600;
    }

    .badge-rejected {
        background:#f8d7da;
        color:#842029;
        padding:2px 8px;
        border-radius:12px;
        font-size:0.75rem;
        font-weight:600;
    }
</style>
""", unsafe_allow_html=True)


VENDORS = {
    "현대식품(주)": {
        "code": "V001",
        "amount": 12450000,
        "status": "승인 대기",
        "days": 3,
        "invoice": "INV-2024-0892",
    },
    "대한유통(주)": {
        "code": "V002",
        "amount": 8320000,
        "status": "승인 완료",
        "days": 1,
        "invoice": "INV-2024-0901",
    },
    "롯데상사(주)": {
        "code": "V003",
        "amount": 21780000,
        "status": "보완 요청",
        "days": 5,
        "invoice": "INV-2024-0876",
    },
    "신세계물산(주)": {
        "code": "V004",
        "amount": 15600000,
        "status": "승인 대기",
        "days": 2,
        "invoice": "INV-2024-0915",
    },
    "한국푸드서비스(주)": {
        "code": "V005",
        "amount": 6900000,
        "status": "승인 완료",
        "days": 0,
        "invoice": "INV-2024-0922",
    },
}


def get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error(
            "ANTHROPIC_API_KEY가 설정되지 않았습니다.\n"
            "Streamlit Cloud → Settings → Secrets에 추가해 주세요.\n\n"
            'ANTHROPIC_API_KEY = "sk-ant-..."'
        )
        st.stop()
    return anthropic.Anthropic(api_key=api_key)


def build_system_prompt(vendor_name: str, vendor_data: dict) -> str:
    return f"""
당신은 롯데백화점 정산회계팀의 거래처용 AI 정산안내 어시스턴트입니다.
정확하고 친절하게 답변하며, 모호하거나 판단이 필요한 사안은 담당자 확인을 권유합니다.
답변은 간결하게 핵심만 전달하고, 필요 시 항목을 나눠 안내합니다.

현재 로그인 거래처 정보:
- 거래처명: {vendor_name}
- 거래처 코드: {vendor_data['code']}
- 이번 달 정산 예정액: {vendor_data['amount']:,}원
- 세금계산서 번호: {vendor_data['invoice']}
- 승인 상태: {vendor_data['status']}
- 승인 대기 영업일: {vendor_data['days']}일
- 지급 예정일: {(datetime.now() + timedelta(days=5)).strftime('%Y년 %m월 %d일')}

중요 원칙:
- 반드시 현재 로그인한 거래처 정보만 기준으로 답변하세요.
- 다른 거래처 정보는 절대로 노출하지 마세요.
- 승인 여부를 임의 판단하지 말고, 현재 상태를 쉽게 설명하는 데 집중하세요.
- 불확실한 경우 담당자 확인이 필요하다고 안내하세요.
""".strip()


def get_ai_response(messages: list, system_prompt: str) -> str:
    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


if "vendor_messages" not in st.session_state:
    st.session_state.vendor_messages = []

if "quick_question" not in st.session_state:
    st.session_state.quick_question = ""


st.markdown(
    """
    <div class="header-banner">
        <h1>💬 거래처용 AI 정산안내</h1>
        <p>정산 현황을 자연어로 바로 확인하세요</p>
    </div>
    """,
    unsafe_allow_html=True
)

col_login, col_chat = st.columns([1, 2])

with col_login:
    st.markdown("#### 🔐 거래처 선택")
    selected_vendor = st.selectbox("거래처 선택 (데모)", list(VENDORS.keys()))
    selected_info = VENDORS[selected_vendor]

    badge_class = (
        "badge-approved"
        if selected_info["status"] == "승인 완료"
        else "badge-rejected" if selected_info["status"] == "보완 요청"
        else "badge-pending"
    )

    st.markdown(
        f"""
        <div style="background:white;border-radius:10px;padding:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-top:1rem;">
            <div style="font-size:0.8rem;color:#888;margin-bottom:0.5rem">내 정산 현황</div>
            <div style="font-weight:700;font-size:1.1rem;color:#c8102e;margin-bottom:0.3rem">
                {selected_info["amount"]:,}원
            </div>
            <div><span class="{badge_class}">{selected_info["status"]}</span></div>
            <div style="font-size:0.8rem;color:#666;margin-top:0.5rem">📄 {selected_info["invoice"]}</div>
            <div style="font-size:0.8rem;color:#666">📅 지급 예정: {(datetime.now() + timedelta(days=5)).strftime("%m/%d")}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### ❓ 자주 묻는 질문")
    faq_list = [
        "이번 달 정산 금액이 얼마인가요?",
        "세금계산서 승인 상태가 어떻게 되나요?",
        "지급 예정일이 언제인가요?",
        "보완 서류가 필요한가요?",
        "전월과 금액이 왜 다른가요?",
    ]

    for question in faq_list:
        if st.button(question, key=f"faq_{question}", use_container_width=True):
            st.session_state.quick_question = question

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.vendor_messages = []
        st.session_state.quick_question = ""
        st.rerun()

with col_chat:
    st.markdown("#### 🤖 AI 정산 안내 채팅")

    with st.container(height=420):
        if not st.session_state.vendor_messages:
            st.markdown(
                f'<div class="ai-bubble">안녕하세요, <strong>{selected_vendor}</strong> 담당자님! 👋<br>정산 관련 궁금하신 점을 자유롭게 질문해 주세요.</div>',
                unsafe_allow_html=True
            )

        for msg in st.session_state.vendor_messages:
            bubble_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
            st.markdown(
                f'<div class="{bubble_class}">{msg["content"]}</div>',
                unsafe_allow_html=True
            )

    user_input = st.chat_input("정산 관련 질문을 입력하세요...", key="vendor_input")

    if st.session_state.quick_question and not user_input:
        user_input = st.session_state.quick_question
        st.session_state.quick_question = ""

    if user_input:
        st.session_state.vendor_messages.append({
            "role": "user",
            "content": user_input
        })

        system_prompt = build_system_prompt(selected_vendor, selected_info)
        api_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.vendor_messages
        ]

        with st.spinner("AI가 답변을 생성 중입니다..."):
            response = get_ai_response(api_messages, system_prompt)

        st.session_state.vendor_messages.append({
            "role": "assistant",
            "content": response
        })

        st.rerun()
