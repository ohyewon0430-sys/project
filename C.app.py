import streamlit as st
import random
from datetime import datetime, timedelta
 
try:
    import anthropic
except ImportError:
    st.error("anthropic 패키지가 설치되지 않았습니다. requirements.txt에 `anthropic>=0.28.0`을 추가해 주세요.")
    st.stop()
 
st.set_page_config(
    page_title="AI 정산안내 어시스턴트",
    page_icon="🏬",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #c8102e 0%, #9b0c24 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    .header-banner {
        background: linear-gradient(135deg, #c8102e 0%, #9b0c24 100%);
        padding: 1.5rem 2rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;
    }
    .header-banner h1 { margin: 0; font-size: 1.6rem; }
    .header-banner p  { margin: 0; opacity: 0.85; font-size: 0.9rem; }
    .kpi-card {
        background: white; border-radius: 12px; padding: 1.2rem;
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #c8102e;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #c8102e; }
    .kpi-label { font-size: 0.8rem; color: #666; margin-top: 4px; }
    .kpi-change { font-size: 0.75rem; color: #28a745; font-weight: 600; }
    .user-bubble {
        background: #c8102e; color: white; padding: 0.8rem 1.1rem;
        border-radius: 18px 18px 4px 18px; margin: 0.4rem 0 0.4rem 20%; font-size: 0.9rem;
    }
    .ai-bubble {
        background: white; color: #333; padding: 0.8rem 1.1rem;
        border-radius: 18px 18px 18px 4px; margin: 0.4rem 20% 0.4rem 0;
        font-size: 0.9rem; box-shadow: 0 2px 6px rgba(0,0,0,0.08); border-left: 3px solid #c8102e;
    }
    .badge-pending  { background:#fff3cd; color:#856404; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-approved { background:#d1e7dd; color:#0f5132; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-rejected { background:#f8d7da; color:#842029; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .exception-card { background:white; border-radius:10px; padding:1rem 1.2rem; margin-bottom:0.8rem;
        box-shadow:0 1px 4px rgba(0,0,0,0.07); border-left:4px solid #dc3545; }
    .exception-card.medium { border-left-color: #fd7e14; }
    .exception-card.low    { border-left-color: #ffc107; }
    .stTabs [data-baseweb="tab"] { border-radius:8px 8px 0 0; background:#f0f0f0; color:#555; }
    .stTabs [aria-selected="true"] { background:#c8102e !important; color:white !important; }
</style>
""", unsafe_allow_html=True)
 
VENDORS = {
    "현대식품(주)":       {"code": "V001", "amount": 12450000, "status": "승인 대기", "days": 3, "invoice": "INV-2024-0892"},
    "대한유통(주)":       {"code": "V002", "amount":  8320000, "status": "승인 완료", "days": 1, "invoice": "INV-2024-0901"},
    "롯데상사(주)":       {"code": "V003", "amount": 21780000, "status": "보완 요청", "days": 5, "invoice": "INV-2024-0876"},
    "신세계물산(주)":     {"code": "V004", "amount": 15600000, "status": "승인 대기", "days": 2, "invoice": "INV-2024-0915"},
    "한국푸드서비스(주)": {"code": "V005", "amount":  6900000, "status": "승인 완료", "days": 0, "invoice": "INV-2024-0922"},
}
 
EXCEPTION_ITEMS = [
    {"vendor": "롯데상사(주)",   "issue": "보완 서류 미제출 (사업자등록증 갱신본)",           "days": 5, "amount": "21,780,000원", "priority": "high"},
    {"vendor": "현대식품(주)",   "issue": "승인 대기 3영업일 초과",                           "days": 3, "amount": "12,450,000원", "priority": "high"},
    {"vendor": "삼성통상(주)",   "issue": "정산 예정액과 지급 예정액 차이 발생 (+840,000원)", "days": 2, "amount":  "7,200,000원", "priority": "medium"},
    {"vendor": "LG생활건강(주)", "issue": "세금계산서 전자 발행 오류",                        "days": 4, "amount": "18,900,000원", "priority": "medium"},
    {"vendor": "CJ제일제당(주)", "issue": "반복 문의 3회 이상 (지급 예정 불일치)",            "days": 1, "amount":  "9,450,000원", "priority": "low"},
]
 
def get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY가 설정되지 않았습니다.\nStreamlit Cloud → Settings → Secrets에 추가해 주세요.\n\nANTHROPIC_API_KEY = \"sk-ant-...\"")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)
 
def build_system_prompt(mode, vendor_info=None):
    base = """당신은 롯데백화점 정산회계팀의 AI 정산안내 어시스턴트입니다.
정확하고 친절하게 답변하며, 모호하거나 판단이 필요한 사안은 담당자 확인을 권유합니다.
답변은 간결하게 핵심만 전달하고, 필요 시 항목을 나눠 안내합니다."""
    if mode == "vendor":
        ctx = ""
        if vendor_info:
            ctx = f"""
현재 로그인 거래처 정보:
- 거래처명: {vendor_info['name']}
- 거래처 코드: {vendor_info['data']['code']}
- 이번 달 정산 예정액: {vendor_info['data']['amount']:,}원
- 세금계산서 번호: {vendor_info['data']['invoice']}
- 승인 상태: {vendor_info['data']['status']}
- 승인 대기 영업일: {vendor_info['data']['days']}일
- 지급 예정일: {(datetime.now() + timedelta(days=5)).strftime('%Y년 %m월 %d일')}"""
        return base + f"\n당신은 거래처 담당자와 대화합니다.{ctx}\n위 정보를 기반으로 정산 현황을 쉽게 설명하세요. 절대로 다른 거래처 정보를 노출하지 마세요."
    else:
        return base + "\n당신은 내부 담당자를 보조합니다.\n거래처 문의가 들어오면: ① 현재 상태 한 줄 요약 ② 거래처 전달용 답변 초안 ③ 확인 필요 항목 ④ 관련 근거를 제시합니다.\n판단·승인·예외 처리는 담당자의 몫임을 명시합니다."
 
def get_ai_response(messages, system):
    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=messages,
    )
    return response.content[0].text
 
if "vendor_messages"   not in st.session_state: st.session_state.vendor_messages   = []
if "internal_messages" not in st.session_state: st.session_state.internal_messages = []
if "quick_question"    not in st.session_state: st.session_state.quick_question    = ""
 
with st.sidebar:
    st.markdown("## 🏬 롯데백화점")
    st.markdown("### 정산회계팀 AI 어시스턴트")
    st.markdown("---")
    page = st.radio("메뉴", ["📊 대시보드", "💬 거래처용 AI 정산안내", "🛠️ 내부 담당자 응대 도우미", "⚠️ 예외 건 관리"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown(f"**오늘 날짜** `{datetime.now().strftime('%Y년 %m월 %d일')}`")
    st.markdown(f"**마감 예정일** `{(datetime.now() + timedelta(days=3)).strftime('%m월 %d일')}`")
    st.markdown("---")
    st.caption("AI는 설명·정리 역할을 담당합니다.\n판단·승인은 담당자가 수행합니다.")
 
# ─── 대시보드 ────────────────────────────────────────────────
if page == "📊 대시보드":
    st.markdown('<div class="header-banner"><h1>📊 AI 정산안내 어시스턴트 대시보드</h1><p>롯데백화점 정산회계팀 · 파일럿 운영 현황</p></div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (val, label, chg) in zip([c1,c2,c3,c4,c5], [
        ("1,540→1,100건","월 정산 문의 건수","▼ 29% 감소 목표"),
        ("6분 → 4분","건당 평균 처리시간","▼ 33% 단축 목표"),
        ("200h → 90h","월 총 응대시간","▼ 55% 절감 목표"),
        ("2.5→2.0일","승인 평균 리드타임","▼ 20% 단축 목표"),
        ("30% → 20%","재문의율","▼ 10%p 감소 목표"),
    ]):
        col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">{label}</div><div class="kpi-change">{chg}</div></div>', unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📈 프로젝트 개요", "🗓️ 실행 계획 (8주)", "📋 거래처 현황"])
 
    with tab1:
        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### 🎯 솔루션 구조")
            st.markdown("| 구분 | AI 역할 | 사람 역할 |\n|------|---------|----------|\n| 거래처 안내 | 데이터 조회·FAQ | 예외 응대·관계 관리 |\n| 내부 응대 | 답변 초안·추천 | 최종 검토·승인 판단 |\n| 리스크 관리 | 지연 건 탐지 | 정책 결정·책임 승인 |")
        with cr:
            st.markdown("#### ⚠️ 리스크 대응")
            for t, d in [("🤖 AI 오답","답변 범위를 승인 데이터·FAQ로 제한"),("🔒 보안·권한","기존 로그인 권한 활용, 본인 데이터만 조회"),("📉 현장 정착 실패","기존 사이트 통합, 상위 20개 FAQ 우선 적용")]:
                st.info(f"**{t}** — {d}")
 
    with tab2:
        for p, t, c, o in [
            ("1~2주","현황 진단 및 기준 수립","문의 유형 정리, 반복 질문 도출, KPI 기준선 확정","현황분석 보고서, KPI 기준선, FAQ 초안"),
            ("3~4주","데이터 연결 및 AI 설계","조회 사이트 데이터 매핑, 답변 시나리오 설계","AI 답변 시나리오, 데이터 맵, 응대 템플릿"),
            ("5~6주","파일럿 구축","거래처용 AI 안내 화면, 내부 응대 도우미 구현","파일럿 버전, 테스트 결과, 개선사항"),
            ("7~8주","시범 운영 및 효과 검증","실제 문의 대응 적용, KPI 측정, 오류 보정","파일럿 결과 보고서, 전사 확대안"),
        ]:
            with st.expander(f"**{p}** | {t}"):
                ca, cb = st.columns(2)
                ca.markdown(f"**주요 내용**\n\n{c}")
                cb.markdown(f"**산출물**\n\n{o}")
 
    with tab3:
        st.markdown("#### 이번 달 거래처별 정산 현황")
        for name, info in VENDORS.items():
            bcls = "badge-approved" if info["status"]=="승인 완료" else ("badge-rejected" if info["status"]=="보완 요청" else "badge-pending")
            st.markdown(f'<div style="background:white;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.6rem;box-shadow:0 1px 4px rgba(0,0,0,0.07);display:flex;justify-content:space-between;align-items:center;"><div><strong>{name}</strong> <span style="color:#888;font-size:0.8rem">{info["code"]}</span></div><div style="display:flex;gap:1.5rem;align-items:center;"><span style="font-weight:600">{info["amount"]:,}원</span><span class="{bcls}">{info["status"]}</span><span style="color:#888;font-size:0.8rem">{info["invoice"]}</span></div></div>', unsafe_allow_html=True)
 
# ─── 거래처용 AI 정산안내 ─────────────────────────────────────
elif page == "💬 거래처용 AI 정산안내":
    st.markdown('<div class="header-banner"><h1>💬 거래처용 AI 정산안내</h1><p>정산 현황을 자연어로 바로 확인하세요</p></div>', unsafe_allow_html=True)
    col_login, col_chat = st.columns([1, 2])
 
    with col_login:
        st.markdown("#### 🔐 거래처 로그인")
        selected = st.selectbox("거래처 선택 (데모)", list(VENDORS.keys()))
        info = VENDORS[selected]
        bcls = "badge-approved" if info["status"]=="승인 완료" else ("badge-rejected" if info["status"]=="보완 요청" else "badge-pending")
        st.markdown(f'<div style="background:white;border-radius:10px;padding:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-top:1rem;"><div style="font-size:0.8rem;color:#888;margin-bottom:0.5rem">내 정산 현황</div><div style="font-weight:700;font-size:1.1rem;color:#c8102e;margin-bottom:0.3rem">{info["amount"]:,}원</div><div><span class="{bcls}">{info["status"]}</span></div><div style="font-size:0.8rem;color:#666;margin-top:0.5rem">📄 {info["invoice"]}</div><div style="font-size:0.8rem;color:#666">📅 지급 예정: {(datetime.now()+timedelta(days=5)).strftime("%m/%d")}</div></div>', unsafe_allow_html=True)
 
        st.markdown("#### ❓ 자주 묻는 질문")
        for q in ["이번 달 정산 금액이 얼마인가요?","세금계산서 승인 상태가 어떻게 되나요?","지급 예정일이 언제인가요?","보완 서류가 필요한가요?","전월과 금액이 왜 다른가요?"]:
            if st.button(q, key=f"qq_{q}", use_container_width=True):
                st.session_state.quick_question = q
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.vendor_messages = []
            st.rerun()
 
    with col_chat:
        st.markdown("#### 🤖 AI 정산 안내 채팅")
        with st.container(height=420):
            if not st.session_state.vendor_messages:
                st.markdown(f'<div class="ai-bubble">안녕하세요, <strong>{selected}</strong> 담당자님! 👋<br>정산 관련 궁금하신 점을 자유롭게 질문해 주세요.</div>', unsafe_allow_html=True)
            for msg in st.session_state.vendor_messages:
                cls = "user-bubble" if msg["role"]=="user" else "ai-bubble"
                st.markdown(f'<div class="{cls}">{msg["content"]}</div>', unsafe_allow_html=True)
 
        user_input = st.chat_input("정산 관련 질문을 입력하세요...", key="vendor_input")
        if st.session_state.quick_question and not user_input:
            user_input = st.session_state.quick_question
            st.session_state.quick_question = ""
 
        if user_input:
            st.session_state.vendor_messages.append({"role":"user","content":user_input})
            system = build_system_prompt("vendor", {"name":selected,"data":info})
            api_msgs = [{"role":m["role"],"content":m["content"]} for m in st.session_state.vendor_messages]
            with st.spinner("AI가 답변을 생성 중입니다..."):
                response = get_ai_response(api_msgs, system)
            st.session_state.vendor_messages.append({"role":"assistant","content":response})
            st.rerun()
 
# ─── 내부 담당자 응대 도우미 ─────────────────────────────────
elif page == "🛠️ 내부 담당자 응대 도우미":
    st.markdown('<div class="header-banner"><h1>🛠️ 내부 담당자 응대 도우미</h1><p>문의 내용을 입력하면 AI가 답변 초안과 확인 포인트를 즉시 제시합니다</p></div>', unsafe_allow_html=True)
    col_form, col_result = st.columns([1, 2])
 
    with col_form:
        st.markdown("#### 📋 문의 정보 입력")
        vendor_name  = st.selectbox("거래처명", list(VENDORS.keys()))
        inquiry_type = st.selectbox("문의 유형", ["정산 금액 확인","세금계산서 승인 상태","지급 예정일 문의","보완 서류 안내","금액 불일치 문의","기타"])
        inquiry_text = st.text_area("문의 내용 요약", height=120, placeholder="예: 이번 달 지급 예정이라고 들었는데 시스템에서 승인 대기로 보인다고 문의함")
        submit = st.button("🔍 AI 답변 초안 생성", type="primary", use_container_width=True)
        st.markdown("---")
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.internal_messages = []
            st.rerun()
 
    with col_result:
        if submit and inquiry_text:
            info = VENDORS[vendor_name]
            context = f"거래처: {vendor_name} ({info['code']})\n문의 유형: {inquiry_type}\n문의 내용: {inquiry_text}\n현재 승인 상태: {info['status']}\n정산 예정액: {info['amount']:,}원\n세금계산서: {info['invoice']}\n승인 대기 영업일: {info['days']}일"
            prompt = f"아래 문의 건에 대해 ① 현재 상태 한 줄 요약 ② 거래처 전달 답변 초안 ③ 담당자 확인 필요 항목 ④ 관련 근거를 제시해 주세요.\n\n{context}"
            system = build_system_prompt("internal")
            st.markdown("#### 🤖 AI 응대 초안")
            with st.spinner("AI가 분석 중입니다..."):
                result = get_ai_response([{"role":"user","content":prompt}], system)
            st.session_state.internal_messages.append({"role":"user","content":prompt})
            st.session_state.internal_messages.append({"role":"assistant","content":result})
            st.markdown(f'<div style="background:white;border-radius:10px;padding:1.2rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #c8102e;">{result.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)
        elif submit:
            st.warning("문의 내용을 입력해 주세요.")
 
        if st.session_state.internal_messages:
            st.markdown("#### 💬 추가 질문")
            with st.container(height=250):
                for msg in st.session_state.internal_messages[-6:]:
                    cls = "user-bubble" if msg["role"]=="user" else "ai-bubble"
                    preview = msg["content"][:200] + ("..." if len(msg["content"])>200 else "")
                    st.markdown(f'<div class="{cls}">{preview}</div>', unsafe_allow_html=True)
            follow_up = st.chat_input("추가로 궁금한 점을 입력하세요...", key="internal_input")
            if follow_up:
                st.session_state.internal_messages.append({"role":"user","content":follow_up})
                system   = build_system_prompt("internal")
                api_msgs = [{"role":m["role"],"content":m["content"]} for m in st.session_state.internal_messages]
                with st.spinner("AI가 분석 중입니다..."):
                    resp = get_ai_response(api_msgs, system)
                st.session_state.internal_messages.append({"role":"assistant","content":resp})
                st.rerun()
 
# ─── 예외 건 관리 ─────────────────────────────────────────────
elif page == "⚠️ 예외 건 관리":
    st.markdown('<div class="header-banner"><h1>⚠️ 예외 건 우선순위 대시보드</h1><p>반복 문의 발생 가능성이 높은 건을 먼저 처리하세요</p></div>', unsafe_allow_html=True)
    high   = [e for e in EXCEPTION_ITEMS if e["priority"]=="high"]
    medium = [e for e in EXCEPTION_ITEMS if e["priority"]=="medium"]
    low    = [e for e in EXCEPTION_ITEMS if e["priority"]=="low"]
    cs, cm, cl = st.columns(3)
    cs.metric("🔴 긴급 처리 필요", f"{len(high)}건",   "즉시 조치")
    cm.metric("🟠 주의 관찰",       f"{len(medium)}건", "금일 내 처리")
    cl.metric("🟡 모니터링",         f"{len(low)}건",   "주간 리뷰")
    st.markdown("---")
 
    def render_exceptions(items, card_cls, label):
        if not items: return
        st.markdown(f"#### {label}")
        for item in items:
            st.markdown(f'<div class="exception-card {card_cls}"><div style="display:flex;justify-content:space-between;align-items:center;"><strong>{item["vendor"]}</strong><span style="color:#888;font-size:0.8rem">대기 {item["days"]}영업일 · {item["amount"]}</span></div><div style="color:#555;font-size:0.85rem;margin-top:0.3rem">⚠️ {item["issue"]}</div></div>', unsafe_allow_html=True)
 
    render_exceptions(high,   "",       "🔴 긴급 — 즉시 처리 필요")
    render_exceptions(medium, "medium", "🟠 주의 — 금일 내 처리 권장")
    render_exceptions(low,    "low",    "🟡 모니터링 — 주간 리뷰")
    st.markdown("---")
    st.markdown("#### 🤖 AI 예외 건 분석")
    if st.button("AI로 이번 주 예외 건 종합 분석 생성", type="primary"):
        summary = "\n".join([f"- {e['vendor']}: {e['issue']} (대기 {e['days']}일, {e['amount']})" for e in EXCEPTION_ITEMS])
        prompt  = f"아래 예외 건 목록에 대해 우선순위별 처리 권고안과 반복 문의 예방을 위한 선제적 조치 방안을 제시해 주세요.\n\n{summary}"
        system  = build_system_prompt("internal")
        with st.spinner("AI가 분석 중입니다..."):
            result = get_ai_response([{"role":"user","content":prompt}], system)
        st.markdown(f'<div style="background:white;border-radius:10px;padding:1.2rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #c8102e;margin-top:1rem;">{result.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)
