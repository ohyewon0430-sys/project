import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


st.set_page_config(
    page_title="AI 정산안내 어시스턴트",
    page_icon="💼",
    layout="wide"
)


# -----------------------------
# 샘플 데이터
# -----------------------------
def load_sample_data() -> pd.DataFrame:
    today = datetime.today().date()

    data = [
        {
            "거래처명": "에이스푸드",
            "전표번호": "SLIP-2026-001",
            "세금계산서번호": "TAX-2026-001",
            "정산예정액": 12500000,
            "실제지급예정액": 12500000,
            "승인상태": "승인완료",
            "지급예정일": today + timedelta(days=3),
            "보완필요": "없음",
            "반려사유": "",
            "승인지연일수": 0,
            "전월대비증감률": 8,
            "문의이력": 2,
        },
        {
            "거래처명": "한빛리테일",
            "전표번호": "SLIP-2026-002",
            "세금계산서번호": "TAX-2026-002",
            "정산예정액": 9800000,
            "실제지급예정액": 9100000,
            "승인상태": "승인대기",
            "지급예정일": today + timedelta(days=7),
            "보완필요": "사업자등록증 사본",
            "반려사유": "",
            "승인지연일수": 4,
            "전월대비증감률": -12,
            "문의이력": 5,
        },
        {
            "거래처명": "그린로지스",
            "전표번호": "SLIP-2026-003",
            "세금계산서번호": "TAX-2026-003",
            "정산예정액": 15400000,
            "실제지급예정액": 12000000,
            "승인상태": "보완요청",
            "지급예정일": today + timedelta(days=10),
            "보완필요": "거래명세서 누락",
            "반려사유": "",
            "승인지연일수": 6,
            "전월대비증감률": 15,
            "문의이력": 6,
        },
        {
            "거래처명": "미래유통",
            "전표번호": "SLIP-2026-004",
            "세금계산서번호": "TAX-2026-004",
            "정산예정액": 7000000,
            "실제지급예정액": 7000000,
            "승인상태": "반려",
            "지급예정일": today + timedelta(days=14),
            "보완필요": "재제출 필요",
            "반려사유": "세금계산서 발행일 오류",
            "승인지연일수": 8,
            "전월대비증감률": -5,
            "문의이력": 4,
        },
        {
            "거래처명": "동서상사",
            "전표번호": "SLIP-2026-005",
            "세금계산서번호": "TAX-2026-005",
            "정산예정액": 20300000,
            "실제지급예정액": 19800000,
            "승인상태": "승인대기",
            "지급예정일": today + timedelta(days=5),
            "보완필요": "없음",
            "반려사유": "",
            "승인지연일수": 3,
            "전월대비증감률": 22,
            "문의이력": 7,
        },
    ]

    df = pd.DataFrame(data)
    return df


# -----------------------------
# 유틸
# -----------------------------
def format_currency(value: int) -> str:
    return f"{value:,.0f}원"


def build_vendor_answer(row: pd.Series, question: str) -> str:
    q = question.strip().lower()

    if not q:
        return "질문을 입력해 주세요."

    if "얼마" in question or "금액" in question or "정산" in question:
        return (
            f"{row['거래처명']}의 현재 정산예정액은 {format_currency(row['정산예정액'])}이며, "
            f"실제지급예정액은 {format_currency(row['실제지급예정액'])}입니다."
        )

    if "승인" in question or "상태" in question:
        return f"현재 세금계산서 승인상태는 '{row['승인상태']}'입니다."

    if "지급" in question or "언제" in question or "예정일" in question:
        return f"현재 지급예정일은 {row['지급예정일']}입니다."

    if "보완" in question or "서류" in question or "누락" in question:
        if row["보완필요"] == "없음":
            return "현재 기준으로 추가 보완이 필요한 서류는 없습니다."
        return f"현재 보완이 필요한 항목은 '{row['보완필요']}'입니다."

    if "왜" in question or "전월" in question or "다른" in question:
        diff = row["전월대비증감률"]
        if diff > 0:
            return f"현재 금액은 전월 대비 약 {diff}% 증가했습니다. 거래 규모 또는 반영 시점 차이를 확인해 주세요."
        elif diff < 0:
            return f"현재 금액은 전월 대비 약 {abs(diff)}% 감소했습니다. 일부 차감 또는 반영 기준 차이가 있을 수 있습니다."
        return "현재 금액은 전월과 큰 차이가 없습니다."

    return (
        "현재 질문에 대해 확인 가능한 정보는 정산예정액, 실제지급예정액, 승인상태, 지급예정일, "
        "보완 필요 여부입니다. 더 구체적으로 질문해 주세요."
    )


def build_internal_reply(row: pd.Series) -> dict:
    summary = (
        f"{row['거래처명']} / {row['전표번호']} / {row['세금계산서번호']} 기준, "
        f"현재 상태는 '{row['승인상태']}'입니다."
    )

    if row["승인상태"] == "승인완료":
        draft = (
            f"안녕하세요. 확인 결과 현재 세금계산서는 승인 완료 상태이며, "
            f"지급예정일은 {row['지급예정일']}입니다. "
            f"정산예정액은 {format_currency(row['정산예정액'])}입니다."
        )
    elif row["승인상태"] == "승인대기":
        draft = (
            f"안녕하세요. 현재 세금계산서는 승인 대기 상태입니다. "
            f"예정 지급일은 {row['지급예정일']}이며, 내부 승인 진행 상황에 따라 변동될 수 있습니다."
        )
    elif row["승인상태"] == "보완요청":
        draft = (
            f"안녕하세요. 현재 건은 보완 요청 상태입니다. "
            f"보완 필요 항목은 '{row['보완필요']}'이며, 서류 제출 후 재확인 예정입니다."
        )
    else:
        draft = (
            f"안녕하세요. 현재 건은 반려 상태입니다. "
            f"반려 사유는 '{row['반려사유']}'이며, 수정 후 재제출이 필요합니다."
        )

    checks = []
    if row["승인지연일수"] >= 3:
        checks.append(f"승인 지연 {row['승인지연일수']}일")
    if row["보완필요"] != "없음":
        checks.append(f"보완 필요: {row['보완필요']}")
    if abs(row["정산예정액"] - row["실제지급예정액"]) >= 1000000:
        checks.append("정산예정액과 실제지급예정액 차이 큼")
    if row["반려사유"]:
        checks.append(f"반려 사유: {row['반려사유']}")

    if not checks:
        checks.append("특이 예외 없음")

    evidence = [
        f"승인상태: {row['승인상태']}",
        f"정산예정액: {format_currency(row['정산예정액'])}",
        f"실제지급예정액: {format_currency(row['실제지급예정액'])}",
        f"지급예정일: {row['지급예정일']}",
    ]

    return {
        "summary": summary,
        "draft": draft,
        "checks": checks,
        "evidence": evidence,
    }


def build_exception_table(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["예외유형"] = result.apply(classify_exception, axis=1)
    result = result[result["예외유형"] != "정상"]
    return result[
        [
            "거래처명",
            "전표번호",
            "세금계산서번호",
            "승인상태",
            "승인지연일수",
            "보완필요",
            "정산예정액",
            "실제지급예정액",
            "예외유형",
            "문의이력",
        ]
    ]


def classify_exception(row: pd.Series) -> str:
    if row["승인지연일수"] >= 3 and row["승인상태"] == "승인대기":
        return "3영업일 이상 승인대기"
    if row["보완필요"] != "없음":
        return "보완 요청 후 미제출 가능"
    if abs(row["정산예정액"] - row["실제지급예정액"]) >= 1000000:
        return "정산예정액-실지급액 차이 큼"
    if row["승인상태"] == "반려":
        return "반려 건"
    return "정상"


# -----------------------------
# 화면
# -----------------------------
df = load_sample_data()

st.title("💼 AI 정산안내 어시스턴트")
st.caption("롯데백화점 정산회계팀 AI 활용 프로젝트 기획서 기반 데모")

with st.sidebar:
    st.header("기본 설정")
    selected_vendor = st.selectbox("거래처 선택", df["거래처명"].tolist())
    selected_row = df[df["거래처명"] == selected_vendor].iloc[0]

    st.markdown("---")
    st.subheader("프로젝트 목표")
    st.write("반복 문의 감소")
    st.write("응대시간 단축")
    st.write("승인 리드타임 개선")

tab1, tab2, tab3, tab4 = st.tabs(
    ["거래처용 AI 정산안내", "내부 응대 도우미", "예외관리 대시보드", "프로젝트 개요"]
)

with tab1:
    st.subheader("거래처용 AI 정산안내")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("정산예정액", format_currency(selected_row["정산예정액"]))
    c2.metric("실제지급예정액", format_currency(selected_row["실제지급예정액"]))
    c3.metric("승인상태", selected_row["승인상태"])
    c4.metric("지급예정일", str(selected_row["지급예정일"]))

    st.markdown("### 질문 입력")
    user_question = st.text_input(
        "예시: 이번 달 정산 대상 금액이 얼마인가요? / 세금계산서 승인 상태가 어떻게 되나요?"
    )

    if st.button("답변 보기", key="vendor_answer"):
        answer = build_vendor_answer(selected_row, user_question)
        st.success(answer)

    st.markdown("### 자주 묻는 질문")
    faq_cols = st.columns(3)
    faq_questions = [
        "이번 달 정산 대상 금액이 얼마인가요?",
        "세금계산서가 승인 대기인지 승인 완료인지 알려주세요.",
        "보완이 필요한 서류가 있나요?",
        "지급 예정 시점이 언제인가요?",
        "현재 금액이 전월과 왜 다른가요?",
        "지금 바로 처리 가능한 상태인가요?",
    ]

    for idx, question in enumerate(faq_questions):
        with faq_cols[idx % 3]:
            if st.button(question, key=f"faq_{idx}"):
                answer = build_vendor_answer(selected_row, question)
                st.info(answer)

with tab2:
    st.subheader("내부 담당자용 AI 응대 도우미")

    col_a, col_b, col_c = st.columns(3)
    slip_no = col_a.text_input("전표번호", value=selected_row["전표번호"])
    tax_no = col_b.text_input("세금계산서번호", value=selected_row["세금계산서번호"])
    vendor_name = col_c.text_input("거래처명", value=selected_row["거래처명"])

    filtered = df[
        (df["거래처명"] == vendor_name)
        & (df["전표번호"] == slip_no)
        & (df["세금계산서번호"] == tax_no)
    ]

    if st.button("응대 초안 생성", key="internal_reply"):
        if filtered.empty:
            st.error("일치하는 데이터가 없습니다. 거래처명, 전표번호, 세금계산서번호를 확인해 주세요.")
        else:
            row = filtered.iloc[0]
            result = build_internal_reply(row)

            st.markdown("### 현재 상태 한 줄 요약")
            st.write(result["summary"])

            st.markdown("### 거래처 전달용 답변 초안")
            st.text_area("답변 초안", value=result["draft"], height=140)

            st.markdown("### 꼭 확인해야 할 예외 항목")
            for item in result["checks"]:
                st.write(f"- {item}")

            st.markdown("### 관련 근거 항목")
            for item in result["evidence"]:
                st.write(f"- {item}")

with tab3:
    st.subheader("반복 문의 예방형 예외관리 대시보드")

    exception_df = build_exception_table(df)

    total_cases = len(df)
    exception_cases = len(exception_df)
    delayed_cases = len(df[(df["승인지연일수"] >= 3) & (df["승인상태"] == "승인대기")])
    supplement_cases = len(df[df["보완필요"] != "없음"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전체 건수", total_cases)
    m2.metric("예외 건수", exception_cases)
    m3.metric("승인지연 건수", delayed_cases)
    m4.metric("보완 필요 건수", supplement_cases)

    st.markdown("### 우선 확인 대상")
    st.dataframe(exception_df, use_container_width=True)

    st.markdown("### 필터")
    filter_type = st.selectbox(
        "예외 유형 선택",
        ["전체", "3영업일 이상 승인대기", "보완 요청 후 미제출 가능", "정산예정액-실지급액 차이 큼", "반려 건"]
    )

    if filter_type != "전체":
        filtered_exception_df = exception_df[exception_df["예외유형"] == filter_type]
    else:
        filtered_exception_df = exception_df

    st.dataframe(filtered_exception_df, use_container_width=True)

with tab4:
    st.subheader("프로젝트 개요")

    st.markdown(
        """
        ### 핵심 방향
        - 거래처가 사이트에서 **스스로 이해하고 해결**하는 Self-service 구조
        - 내부 담당자는 **답변 초안과 확인 포인트**를 빠르게 확보
        - 반복 문의가 발생하기 전 **예외 건을 선제적으로 정리**

        ### 사람과 AI 역할 분담
        - **AI**: 데이터 조회, 상태 설명, FAQ 응답, 초안 생성, 예외 탐지
        - **사람**: 최종 승인 판단, 예외 처리, 민감 이슈 대응

        ### 기대 효과
        - 월 문의 건수 감소
        - 문의 1건당 처리시간 단축
        - 승인 평균 리드타임 개선
        """
    )

    st.markdown("### KPI 예시")
    kpi_df = pd.DataFrame(
        [
            ["정산·승인 관련 월 문의 건수", "1,540건", "1,100건", "29% 감소"],
            ["재문의율", "30%", "20%", "같은 질문 반복 감소"],
            ["문의 1건 평균 처리시간", "6분", "4분", "33% 단축"],
            ["월 총 응대 투입시간", "200시간", "90시간", "55% 절감"],
            ["승인 평균 리드타임", "2.5일", "2.0일", "20% 단축"],
        ],
        columns=["KPI", "기준선", "목표", "기대효과"]
    )
    st.dataframe(kpi_df, use_container_width=True)

st.markdown("---")
st.caption("※ 본 화면은 기획안 시연용 데모이며, 실제 운영 환경에서는 ERP/정산 시스템 및 권한 체계 연동이 필요합니다.")
