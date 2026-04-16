import streamlit as st
import anthropic
import random
from datetime import datetime, timedelta
 
# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI 정산안내 어시스턴트",
    page_icon="🏬",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stApp > header { background-color: transparent; }
 
    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #c8102e 0%, #9b0c24 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stRadio label { color: white !important; }
 
    /* 헤더 배너 */
    .header-banner {
        background: linear-gradient(135deg, #c8102e 0%, #9b0c24 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .header-banner h1 { margin: 0; font-size: 1.6rem; }
    .header-banner p  { margin: 0; opacity: 0.85; font-size: 0.9rem; }
 
    /* KPI 카드 */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #c8102e;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #c8102e; }
    .kpi-label { font-size: 0.8rem; color: #666; margin-top: 4px; }
    .kpi-change { font-size: 0.75rem; color: #28a745; font-weight: 600; }
 
    /* 채팅 버블 */
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
 
    /* 상태 배지 */
    .badge-pending  { background:#fff3cd; color:#856404; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-approved { background:#d1e7dd; color:#0f5132; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-rejected { background:#f8d7da; color:#842029; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
 
    /* 예외 건 카드 */
    .exception-card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        border-left: 4px solid #dc3545;
    }
    .exception-card.medium { border-left-color: #fd7e14; }
    .exception-card.low    { border-left-color: #ffc107; }
 
    /* 탭 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        background: #f0f0f0;
        color: #555;
    }
    .stTabs [aria-selected="true"] {
        background: #c8102e !important;
        color: white !important;
    }
 
    /* 빠른 질문 버튼 */
    .quick-btn button {
        border-radius: 20px !important;
        border: 1px solid #c8102e !important;
        color: #c8102e !important;
        background: white !important;
        font-size: 0.8rem !important;
        padding: 0.3rem 0.8rem !important;
    }
    .quick-btn button:hover {
        background: #c8102e !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)
 
# ── 더미 데이터 ───────────────────────────────────────────────
VENDORS = {
    "현대식품(주)":     {"code": "V001", "amount": 12_450_000, "status": "승인 대기", "days": 3, "invoice": "INV-2024-0892"},
    "대한유통(주)":     {"code": "V002", "amount":  8_320_000, "status": "승인 완료", "days": 1, "invoice": "INV-2024-0901"},
    "롯데상사(주)":     {"code": "V003", "amount": 21_780_000, "status": "보완 요청", "days": 5, "invoice": "INV-2024-0876"},
    "신세계물산(주)":   {"code": "V004", "amount": 15_600_000, "status": "승인 대기", "days": 2, "invoice": "INV-2024-0915"},
    "한국푸드서비스(주)": {"code": "V005", "amount":  6_900_000, "status": "승인 완료", "days": 0, "invoice": "INV-2024-0922"},
}
 
EXCEPTION_ITEMS = [
    {"vendor": "롯데상사(주)",     "issue": "보완 서류 미제출 (사업자등록증 갱신본)",  "days": 5, "amount": "21,780,000원", "priority": "high"},
    {"vendor": "현대식품(주)",     "issue": "승인 대기 3영업일 초과",                   "days": 3, "amount": "12,450,000원", "priority": "high"},
    {"vendor": "삼성통상(주)",     "issue": "정산 예정액과 지급 예정액 차이 발생 (+840,000원)", "days": 2, "amount":  "7,200,000원", "priority": "medium"},
    {"vendor": "LG생활건강(주)",   "issue": "세금계산서 전자 발행 오류",                "days": 4, "amount": "18,900,000원", "priority": "medium"},
    {"vendor": "CJ제일제당(주)",   "issue": "반복 문의 3회 이상 (지급 예정 불일치)",   "days": 1, "amount":  "9,450,000원", "priority": "low"},
]
 
MONTHLY_STATS = {
    "total_inquiries": 1_540, "resolved_by_ai": 980, "avg_process_min": 4.2,
    "total_hours_saved": 110, "approval_lead_days": 2.1, "re_inquiry_rate": 22,
}
 
# ── 시스템 프롬프트 (AI) ──────────────────────────────────────
def build_system_prompt(mode: str, vendor_info: dict = None) -> str:
    base = """당신은 롯데백화점 정산회계팀의 AI 정산안내 어시스턴트입니다.
정확하고 친절하게 답변하며, 모호하거나 판단이 필요한 사안은 반드시 담당자 확인을 권유합니다.
답변은 간결하게 핵심만 전달하고, 필요 시 항목을 나눠 안내합니다.
"""
    if mode == "vendor":
        vendor_ctx = ""
        if vendor_info:
            vendor_ctx = f"""
현재 로그인 거래처 정보:
- 거래처명: {vendor_info['name']}
- 거래처 코드: {vendor_info['data']['code']}
- 이번 달 정산 예정액: {vendor_info['data']['amount']:,}원
- 세금계산서 번호: {vendor_info['data']['invoice']}
- 승인 상태: {vendor_info['data']['status']}
- 승인 대기 영업일: {vendor_info['data']['days']}일
- 지급 예정일: {(datetime.now() + timedelta(days=5)).strftime('%Y년 %m월 %d일')}
"""
        return base + f"""
당신은 거래처 담당자와 대화합니다.{vendor_ctx}
위 정보를 기반으로 정산 현황을 쉽게 설명하고, 승인 상태·지급 예정·서류 안내를 제공합니다.
절대로 다른 거래처 정보를 노출하지 마세요.
"""
    else:  # internal
        return base + """
당신은 내부 담당자를 보조합니다.
거래처 문의가 들어오면: ① 현재 상태 한 줄 요약 ② 거래처 전달용 답변 초안 ③ 확인 필요 항목 ④ 관련 근거를 제시합니다.
판단·승인·예외 처리는 담당자의 몫임을 명시합니다.
"""
 
# ── Anthropic 스트리밍 ────────────────────────────────────────
def stream_ai_response(messages: list, system: str):
    client = anthropic.Anthropic()
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
 
# ── 세션 초기화 ───────────────────────────────────────────────
if "vendor_messages"   not in st.session_state: st.session_state.vendor_messages   = []
if "internal_messages" not in st.session_state: st.session_state.internal_messages = []
if "selected_vendor"   not in st.session_state: st.session_state.selected_vendor   = list(VENDORS.keys())[0]
if "quick_question"    not in st.session_state: st.session_state.quick_question    = ""
 
# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏬 롯데백화점")
    st.markdown("### 정산회계팀 AI 어시스턴트")
    st.markdown("---")
 
    page = st.radio(
        "메뉴",
        ["📊 대시보드", "💬 거래처용 AI 정산안내", "🛠️ 내부 담당자 응대 도우미", "⚠️ 예외 건 관리"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**오늘 날짜**")
    st.markdown(f"`{datetime.now().strftime('%Y년 %m월 %d일')}`")
    st.markdown("**마감 예정일**")
    st.markdown(f"`{(datetime.now() + timedelta(days=3)).strftime('%m월 %d일')}`")
    st.markdown("---")
    st.caption("AI는 설명·정리 역할을 담당합니다.\n판단·승인은 담당자가 수행합니다.")
 
# ══════════════════════════════════════════════════════════════
# 📊 대시보드
# ══════════════════════════════════════════════════════════════
if page == "📊 대시보드":
    st.markdown("""
    <div class="header-banner">
        <div>
            <h1>📊 AI 정산안내 어시스턴트 대시보드</h1>
            <p>롯데백화점 정산회계팀 · 파일럿 운영 현황</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    # KPI 카드
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        ("1,540건 → 1,100건", "월 정산 문의 건수", "▼ 29% 감소 목표"),
        ("6분 → 4분",         "건당 평균 처리시간", "▼ 33% 단축 목표"),
        ("200h → 90h",        "월 총 응대시간",    "▼ 55% 절감 목표"),
        ("2.5일 → 2.0일",     "승인 평균 리드타임", "▼ 20% 단축 목표"),
        ("30% → 20%",         "재문의율",           "▼ 10%p 감소 목표"),
    ]
    for col, (val, label, chg) in zip([c1, c2, c3, c4, c5], kpis):
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{val}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-change">{chg}</div>
        </div>""", unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # 탭
    tab1, tab2, tab3 = st.tabs(["📈 프로젝트 개요", "🗓️ 실행 계획 (8주)", "📋 거래처 현황"])
 
    with tab1:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### 🎯 솔루션 구조")
            st.markdown("""
| 구분 | AI 역할 | 사람 역할 |
|------|---------|----------|
| 거래처 안내 | 데이터 조회·상태 설명·FAQ 답변 | 예외 응대·민감 이슈·관계 관리 |
| 내부 응대 | 답변 초안·정보 요약·우선순위 추천 | 최종 검토·승인 판단·예외 처리 |
| 리스크 관리 | 지연 건 탐지·반려 분류·패턴 분석 | 정책 결정·기준 변경·책임 승인 |
""")
        with col_r:
            st.markdown("#### ⚠️ 리스크 대응")
            risks = [
                ("🤖 AI 오답", "답변 범위를 승인 데이터·FAQ로 제한, 불확실 건은 담당자 연결"),
                ("🔒 보안·권한", "기존 로그인 권한 활용, 본인 거래처 데이터만 조회"),
                ("📉 현장 정착 실패", "기존 사이트에 통합, 파일럿 기간 상위 20개 FAQ 중심 적용"),
            ]
            for icon_title, desc in risks:
                st.info(f"**{icon_title}** — {desc}")
 
    with tab2:
        steps = [
            ("1~2주", "1단계. 현황 진단 및 기준 수립", "문의 유형 정리, 반복 질문 도출, KPI 기준선 확정, 승인 프로세스 맵 작성", "현황분석 보고서, KPI 기준선, FAQ 초안"),
            ("3~4주", "2단계. 데이터 연결 및 AI 설계", "조회 사이트 데이터 매핑, 답변 시나리오 설계, 내부 응대 문구 표준화", "AI 답변 시나리오, 데이터 맵, 응대 템플릿"),
            ("5~6주", "3단계. 파일럿 구축", "거래처용 AI 안내 화면, 내부용 응대 도우미, 예외 건 대시보드 구현", "파일럿 버전, 테스트 결과, 개선사항 목록"),
            ("7~8주", "4단계. 시범 운영 및 효과 검증", "실제 문의 대응 적용, KPI 측정, 오류 보정, 확대 적용 여부 판단", "파일럿 결과 보고서, 전사 확대안, 운영 가이드"),
        ]
        for period, title, content, output in steps:
            with st.expander(f"**{period}** | {title}"):
                c_a, c_b = st.columns(2)
                c_a.markdown(f"**주요 내용**\n\n{content}")
                c_b.markdown(f"**산출물**\n\n{output}")
 
    with tab3:
        st.markdown("#### 이번 달 거래처별 정산 현황")
        for name, info in VENDORS.items():
            badge_cls  = "badge-approved" if info["status"] == "승인 완료" else ("badge-rejected" if info["status"] == "보완 요청" else "badge-pending")
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.6rem;
                        box-shadow:0 1px 4px rgba(0,0,0,0.07);display:flex;justify-content:space-between;align-items:center;">
                <div><strong>{name}</strong> <span style="color:#888;font-size:0.8rem">{info['code']}</span></div>
                <div style="display:flex;gap:1.5rem;align-items:center;">
                    <span style="font-weight:600">{info['amount']:,}원</span>
                    <span class="{badge_cls}">{info['status']}</span>
                    <span style="color:#888;font-size:0.8rem">{info['invoice']}</span>
                </div>
            </div>""", unsafe_allow_html=True)
 
# ══════════════════════════════════════════════════════════════
# 💬 거래처용 AI 정산안내
# ══════════════════════════════════════════════════════════════
elif page == "💬 거래처용 AI 정산안내":
    st.markdown("""
    <div class="header-banner">
        <div>
            <h1>💬 거래처용 AI 정산안내</h1>
            <p>정산 현황을 자연어로 바로 확인하세요</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    col_login, col_chat = st.columns([1, 2])
 
    with col_login:
        st.markdown("#### 🔐 거래처 로그인")
        selected = st.selectbox("거래처 선택 (데모)", list(VENDORS.keys()))
        st.session_state.selected_vendor = selected
        info = VENDORS[selected]
 
        badge_cls = "badge-approved" if info["status"] == "승인 완료" else ("badge-rejected" if info["status"] == "보완 요청" else "badge-pending")
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-top:1rem;">
            <div style="font-size:0.8rem;color:#888;margin-bottom:0.5rem">내 정산 현황</div>
            <div style="font-weight:700;font-size:1.1rem;color:#c8102e;margin-bottom:0.3rem">{info['amount']:,}원</div>
            <div><span class="{badge_cls}">{info['status']}</span></div>
            <div style="font-size:0.8rem;color:#666;margin-top:0.5rem">📄 {info['invoice']}</div>
            <div style="font-size:0.8rem;color:#666">📅 지급 예정: {(datetime.now()+timedelta(days=5)).strftime('%m/%d')}</div>
        </div>""", unsafe_allow_html=True)
 
        st.markdown("#### ❓ 자주 묻는 질문")
        quick_qs = [
            "이번 달 정산 금액이 얼마인가요?",
            "세금계산서 승인 상태가 어떻게 되나요?",
            "지급 예정일이 언제인가요?",
            "보완 서류가 필요한가요?",
            "전월과 금액이 왜 다른가요?",
        ]
        for q in quick_qs:
            if st.button(q, key=f"quick_{q}", use_container_width=True):
                st.session_state.quick_question = q
 
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.vendor_messages = []
            st.rerun()
 
    with col_chat:
        st.markdown("#### 🤖 AI 정산 안내 채팅")
 
        chat_container = st.container(height=420)
        with chat_container:
            if not st.session_state.vendor_messages:
                st.markdown(f"""
                <div class="ai-bubble">
                    안녕하세요, <strong>{selected}</strong> 담당자님! 👋<br>
                    정산 관련 궁금하신 점을 자유롭게 질문해 주세요.<br>
                    <small style="color:#999">예: "이번 달 정산 금액이 얼마인가요?"</small>
                </div>""", unsafe_allow_html=True)
            for msg in st.session_state.vendor_messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="ai-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
 
        # 입력
        default_val = st.session_state.quick_question
        user_input  = st.chat_input("정산 관련 질문을 입력하세요...", key="vendor_input")
 
        # 빠른 질문 처리
        if default_val and not user_input:
            user_input = default_val
            st.session_state.quick_question = ""
 
        if user_input:
            st.session_state.vendor_messages.append({"role": "user", "content": user_input})
            system = build_system_prompt("vendor", {"name": selected, "data": info})
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.vendor_messages]
 
            with st.spinner("AI가 답변을 생성 중입니다..."):
                response = "".join(stream_ai_response(api_msgs, system))
 
            st.session_state.vendor_messages.append({"role": "assistant", "content": response})
            st.rerun()
 
# ══════════════════════════════════════════════════════════════
# 🛠️ 내부 담당자 응대 도우미
# ══════════════════════════════════════════════════════════════
elif page == "🛠️ 내부 담당자 응대 도우미":
    st.markdown("""
    <div class="header-banner">
        <div>
            <h1>🛠️ 내부 담당자 응대 도우미</h1>
            <p>문의 내용을 입력하면 AI가 답변 초안과 확인 포인트를 즉시 제시합니다</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    col_form, col_result = st.columns([1, 2])
 
    with col_form:
        st.markdown("#### 📋 문의 정보 입력")
        vendor_name = st.selectbox("거래처명", list(VENDORS.keys()))
        inquiry_type = st.selectbox("문의 유형", [
            "정산 금액 확인", "세금계산서 승인 상태", "지급 예정일 문의",
            "보완 서류 안내", "금액 불일치 문의", "기타",
        ])
        inquiry_text = st.text_area("문의 내용 (전화·메일 내용 요약)", height=120,
                                    placeholder="예: 이번 달 지급 예정이라고 들었는데 시스템에서 승인 대기로 보인다고 문의함")
        submit = st.button("🔍 AI 답변 초안 생성", type="primary", use_container_width=True)
 
        st.markdown("---")
        st.markdown("#### 💬 담당자 채팅")
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.internal_messages = []
            st.rerun()
 
    with col_result:
        if submit and inquiry_text:
            info = VENDORS[vendor_name]
            context = f"""
거래처: {vendor_name} ({info['code']})
문의 유형: {inquiry_type}
문의 내용: {inquiry_text}
현재 승인 상태: {info['status']}
정산 예정액: {info['amount']:,}원
세금계산서: {info['invoice']}
승인 대기 영업일: {info['days']}일
"""
            prompt = f"아래 문의 건에 대해 ① 현재 상태 한 줄 요약 ② 거래처 전달 답변 초안 ③ 담당자 확인 필요 항목 ④ 관련 근거를 제시해 주세요.\n\n{context}"
            system = build_system_prompt("internal")
 
            st.markdown("#### 🤖 AI 응대 초안")
            with st.spinner("AI가 분석 중입니다..."):
                result = "".join(stream_ai_response([{"role": "user", "content": prompt}], system))
 
            st.session_state.internal_messages.append({"role": "user",      "content": prompt})
            st.session_state.internal_messages.append({"role": "assistant", "content": result})
 
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:1.2rem;
                        box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #c8102e;">
                {result.replace(chr(10), '<br>')}
            </div>""", unsafe_allow_html=True)
 
        elif submit:
            st.warning("문의 내용을 입력해 주세요.")
 
        # 추가 질문 채팅
        if st.session_state.internal_messages:
            st.markdown("#### 💬 추가 질문")
            chat_box = st.container(height=250)
            with chat_box:
                for msg in st.session_state.internal_messages[-6:]:
                    if msg["role"] == "user":
                        st.markdown(f'<div class="user-bubble">{msg["content"][:200]}{"..." if len(msg["content"])>200 else ""}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="ai-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
 
            follow_up = st.chat_input("추가로 궁금한 점을 입력하세요...", key="internal_input")
            if follow_up:
                st.session_state.internal_messages.append({"role": "user", "content": follow_up})
                system = build_system_prompt("internal")
                api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.internal_messages]
                with st.spinner("AI가 분석 중입니다..."):
                    resp = "".join(stream_ai_response(api_msgs, system))
                st.session_state.internal_messages.append({"role": "assistant", "content": resp})
                st.rerun()
 
# ══════════════════════════════════════════════════════════════
# ⚠️ 예외 건 관리 대시보드
# ══════════════════════════════════════════════════════════════
elif page == "⚠️ 예외 건 관리":
    st.markdown("""
    <div class="header-banner">
        <div>
            <h1>⚠️ 예외 건 우선순위 대시보드</h1>
            <p>반복 문의 발생 가능성이 높은 건을 먼저 처리하세요</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    high   = [e for e in EXCEPTION_ITEMS if e["priority"] == "high"]
    medium = [e for e in EXCEPTION_ITEMS if e["priority"] == "medium"]
    low    = [e for e in EXCEPTION_ITEMS if e["priority"] == "low"]
 
    col_s, col_m, col_l_col = st.columns(3)
    col_s.metric("🔴 긴급 처리 필요", f"{len(high)}건",  "즉시 조치")
    col_m.metric("🟠 주의 관찰",       f"{len(medium)}건", "금일 내 처리")
    col_l_col.metric("🟡 모니터링",     f"{len(low)}건",   "주간 리뷰")
 
    st.markdown("---")
 
    def render_exceptions(items, card_class, label):
        if not items: return
        st.markdown(f"#### {label}")
        for item in items:
            st.markdown(f"""
            <div class="exception-card {'' if card_class=='high' else card_class}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong>{item['vendor']}</strong>
                    <span style="color:#888;font-size:0.8rem">대기 {item['days']}영업일 · {item['amount']}</span>
                </div>
                <div style="color:#555;font-size:0.85rem;margin-top:0.3rem">⚠️ {item['issue']}</div>
            </div>""", unsafe_allow_html=True)
 
    render_exceptions(high,   "high",   "🔴 긴급 — 즉시 처리 필요")
    render_exceptions(medium, "medium", "🟠 주의 — 금일 내 처리 권장")
    render_exceptions(low,    "low",    "🟡 모니터링 — 주간 리뷰")
 
    st.markdown("---")
    st.markdown("#### 🤖 AI 예외 건 분석")
    if st.button("AI로 이번 주 예외 건 종합 분석 생성", type="primary"):
        exception_summary = "\n".join([f"- {e['vendor']}: {e['issue']} (대기 {e['days']}일, {e['amount']})" for e in EXCEPTION_ITEMS])
        prompt = f"아래는 이번 주 예외 건 목록입니다. 우선순위별 처리 권고안과 반복 문의 예방을 위한 선제적 조치 방안을 제시해 주세요.\n\n{exception_summary}"
        system = build_system_prompt("internal")
 
        with st.spinner("AI가 분석 중입니다..."):
            result = "".join(stream_ai_response([{"role": "user", "content": prompt}], system))
 
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:1.2rem;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #c8102e;margin-top:1rem;">
            {result.replace(chr(10), '<br>')}
        </div>""", unsafe_allow_html=True)
