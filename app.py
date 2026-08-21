import io

import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="업무지원 요청 현황 대시보드",
    page_icon="📊",
    layout="wide",
)

REQUIRED_COLUMNS = [
    "request_id",
    "request_date",
    "category",
    "summary",
    "urgency",
    "status",
    "ai_handling",
]


# ---------------------------------------------------------
# 화면 스타일
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        [data-testid="stMetric"] {
            background-color: #f7f9fc;
            border: 1px solid #e5e9f0;
            border-radius: 12px;
            padding: 16px 18px;
        }

        [data-testid="stMetricLabel"] {
            font-weight: 600;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #e5e9f0;
            border-radius: 10px;
            overflow: hidden;
        }

        .small-note {
            color: #6b7280;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 함수
# ---------------------------------------------------------
def read_uploaded_csv(uploaded_file):
    """UTF-8/CP949 계열 CSV를 최대한 안전하게 읽는다."""
    raw = uploaded_file.getvalue()

    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError(
        "CSV 인코딩을 확인할 수 없습니다. UTF-8 또는 CP949 형식으로 저장한 후 다시 업로드해 주세요."
    )


def validate_columns(dataframe):
    missing = [col for col in REQUIRED_COLUMNS if col not in dataframe.columns]
    return missing


def clean_data(dataframe):
    df = dataframe.copy()

    # 문자 컬럼 공백 정리
    text_columns = [
        "request_id",
        "category",
        "summary",
        "urgency",
        "status",
        "ai_handling",
    ]

    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # 날짜 변환
    df["request_date"] = pd.to_datetime(
        df["request_date"],
        errors="coerce",
    )

    return df


def make_count_table(dataframe, column_name):
    result = (
        dataframe[column_name]
        .replace("", "미입력")
        .value_counts()
        .rename_axis(column_name)
        .reset_index(name="요청건수")
    )
    return result


# ---------------------------------------------------------
# 제목
# ---------------------------------------------------------
st.title("업무지원 요청 현황 대시보드")
st.caption("업무지원 요청 CSV 파일을 업로드하면 현황을 자동으로 집계하고 시각화합니다.")


# ---------------------------------------------------------
# 파일 업로드
# ---------------------------------------------------------
uploaded_file = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"],
    help="필수 컬럼: request_id, request_date, category, summary, urgency, status, ai_handling",
)

if uploaded_file is None:
    st.info("분석할 CSV 파일을 업로드해 주세요.")

    st.markdown("#### 필요한 CSV 형식")
    st.code(
        "request_id,request_date,category,summary,urgency,status,ai_handling\n"
        "REQ-001,2026-07-02,교육,교육 신청 방법 문의,보통,완료,전용AI가능",
        language="text",
    )
    st.stop()


# ---------------------------------------------------------
# CSV 읽기 / 검증
# ---------------------------------------------------------
try:
    raw_df = read_uploaded_csv(uploaded_file)
except Exception as e:
    st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()

missing_columns = validate_columns(raw_df)

if missing_columns:
    st.error(
        "필수 컬럼이 부족합니다.\n\n"
        f"누락 컬럼: {', '.join(missing_columns)}"
    )
    st.write("현재 CSV 컬럼:", list(raw_df.columns))
    st.stop()

df = clean_data(raw_df)


# ---------------------------------------------------------
# 사이드바 필터
# ---------------------------------------------------------
with st.sidebar:
    st.header("조회 조건")

    category_options = sorted(
        [x for x in df["category"].dropna().unique().tolist() if x]
    )
    status_options = sorted(
        [x for x in df["status"].dropna().unique().tolist() if x]
    )
    urgency_options = sorted(
        [x for x in df["urgency"].dropna().unique().tolist() if x]
    )
    ai_options = sorted(
        [x for x in df["ai_handling"].dropna().unique().tolist() if x]
    )

    selected_categories = st.multiselect(
        "업무분류",
        category_options,
        default=category_options,
    )

    selected_statuses = st.multiselect(
        "상태",
        status_options,
        default=status_options,
    )

    selected_urgencies = st.multiselect(
        "긴급도",
        urgency_options,
        default=urgency_options,
    )

    selected_ai = st.multiselect(
        "AI 처리기준",
        ai_options,
        default=ai_options,
    )

    search_text = st.text_input(
        "검색",
        placeholder="요청번호 또는 문의내용 검색",
    )

    urgent_incomplete_only = st.checkbox(
        "긴급 미완료만 보기",
        help="긴급도가 '상'이면서 상태가 '완료'가 아닌 요청만 표시합니다.",
    )


# ---------------------------------------------------------
# 필터 적용
# ---------------------------------------------------------
filtered_df = df.copy()

filtered_df = filtered_df[
    filtered_df["category"].isin(selected_categories)
    & filtered_df["status"].isin(selected_statuses)
    & filtered_df["urgency"].isin(selected_urgencies)
    & filtered_df["ai_handling"].isin(selected_ai)
]

if search_text.strip():
    keyword = search_text.strip()
    filtered_df = filtered_df[
        filtered_df["request_id"].str.contains(
            keyword,
            case=False,
            na=False,
            regex=False,
        )
        | filtered_df["summary"].str.contains(
            keyword,
            case=False,
            na=False,
            regex=False,
        )
    ]

if urgent_incomplete_only:
    filtered_df = filtered_df[
        (filtered_df["urgency"] == "상")
        & (filtered_df["status"] != "완료")
    ]


# ---------------------------------------------------------
# 핵심 지표
# ---------------------------------------------------------
total_count = len(filtered_df)
completed_count = int((filtered_df["status"] == "완료").sum())
open_count = int(filtered_df["status"].isin(["처리중", "대기"]).sum())
urgent_incomplete_count = int(
    (
        (filtered_df["urgency"] == "상")
        & (filtered_df["status"] != "완료")
    ).sum()
)

m1, m2, m3, m4 = st.columns(4)

m1.metric("전체 요청", f"{total_count:,}건")
m2.metric("완료", f"{completed_count:,}건")
m3.metric("처리중 / 대기", f"{open_count:,}건")
m4.metric("긴급 미완료", f"{urgent_incomplete_count:,}건")

st.markdown("")


# ---------------------------------------------------------
# 차트 1: 업무분류 / 상태
# ---------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("업무분류별 요청건수")

    if filtered_df.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        category_chart = (
            filtered_df["category"]
            .replace("", "미입력")
            .value_counts()
            .sort_values(ascending=False)
        )
        st.bar_chart(category_chart)

with right:
    st.subheader("상태별 요청건수")

    if filtered_df.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        status_chart = (
            filtered_df["status"]
            .replace("", "미입력")
            .value_counts()
        )
        st.bar_chart(status_chart)


# ---------------------------------------------------------
# 차트 2: 긴급도 / AI 처리기준
# ---------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("긴급도별 요청건수")

    if filtered_df.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        urgency_order = ["상", "보통", "하"]
        urgency_chart = (
            filtered_df["urgency"]
            .replace("", "미입력")
            .value_counts()
            .reindex(urgency_order)
            .dropna()
        )
        st.bar_chart(urgency_chart)

with right:
    st.subheader("AI 처리기준별 요청건수")

    if filtered_df.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        ai_chart = (
            filtered_df["ai_handling"]
            .replace("", "미입력")
            .value_counts()
            .sort_values(ascending=False)
        )
        st.bar_chart(ai_chart)


# ---------------------------------------------------------
# 날짜별 추이
# ---------------------------------------------------------
st.subheader("일자별 요청 추이")

date_df = filtered_df.dropna(subset=["request_date"]).copy()

if date_df.empty:
    st.info("유효한 request_date 데이터가 없습니다.")
else:
    daily_chart = (
        date_df.groupby(date_df["request_date"].dt.date)
        .size()
        .rename("요청건수")
    )
    daily_chart.index = pd.to_datetime(daily_chart.index)

    st.line_chart(daily_chart)


# ---------------------------------------------------------
# 상세 데이터
# ---------------------------------------------------------
st.subheader("요청 상세 목록")

display_df = filtered_df.copy()

if not display_df.empty:
    display_df = display_df.sort_values(
        by=["request_date", "request_id"],
        ascending=[False, True],
    )

    display_df["request_date"] = display_df["request_date"].dt.strftime(
        "%Y-%m-%d"
    )

display_columns = {
    "request_id": "요청번호",
    "request_date": "요청일자",
    "category": "업무분류",
    "summary": "요청내용",
    "urgency": "긴급도",
    "status": "상태",
    "ai_handling": "AI 처리기준",
}

display_df = display_df.rename(columns=display_columns)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# 다운로드
# ---------------------------------------------------------
download_df = display_df.copy()

csv_data = download_df.to_csv(
    index=False,
    encoding="utf-8-sig",
).encode("utf-8-sig")

st.download_button(
    label="필터 결과 CSV 다운로드",
    data=csv_data,
    file_name="업무지원요청_필터결과.csv",
    mime="text/csv",
)

st.markdown(
    f'<div class="small-note">현재 표시 중인 요청: {len(filtered_df):,}건</div>',
    unsafe_allow_html=True,
)
