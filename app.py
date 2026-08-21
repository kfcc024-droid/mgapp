import streamlit as st
import pandas as pd
import requests
import datetime
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="팀 예산 관리 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished appearance
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

if "db_url" not in st.session_state:
    st.session_state["db_url"] = ""

if "budget_data" not in st.session_state:
    # Initialize with sample data if empty
    st.session_state["budget_data"] = pd.DataFrame([
        {"id": 101, "month": "2026-08", "member": "김부장", "category": "수선유지비", "amount": 250000, "note": "사무실 장비 수리"},
        {"id": 102, "month": "2026-08", "member": "이팀장", "category": "비품", "amount": 120000, "note": "듀얼 모니터 거치대"},
        {"id": 103, "month": "2026-08", "member": "박사원", "category": "개량공사", "amount": 450000, "note": "회의실 파티션 보수"}
    ])

def fetch_from_apps_script(url):
    """Fetch data from Google Apps Script Web App endpoint."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                df = pd.DataFrame(data)
                if not df.empty:
                    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0).astype(int)
                return df, None
            return pd.DataFrame(), "수신된 데이터가 리스트 형식이 아닙니다."
        return pd.DataFrame(), f"HTTP 오류: {response.status_code}"
    except Exception as e:
        return pd.DataFrame(), f"연동 실패: {str(e)}"

def send_to_apps_script(url, payload):
    """Send payload to Google Apps Script Web App endpoint."""
    try:
        # Google Apps Script handles POST requests via JSON payload
        response = requests.post(
            url, 
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return True, "데이터가 구글 시트에 정상 업데이트되었습니다."
    except Exception as e:
        return False, f"데이터 전송 실패: {str(e)}"

with st.sidebar:
    st.header("⚙️ DB 연동 설정")
    
    # URL Input field
    input_url = st.text_input(
        "Google Apps Script URL",
        value=st.session_state["db_url"],
        placeholder="https://script.google.com/macros/s/.../exec",
        help="Google Apps Script 배포 후 생성된 웹 앱 URL을 입력하세요."
    )
    
    if input_url != st.session_state["db_url"]:
        st.session_state["db_url"] = input_url
    
    # Status Indicator
    if st.session_state["db_url"]:
        st.success("🟢 구글 시트 DB 연결됨")
        if st.button("🔄 구글 시트 데이터 불러오기", use_container_width=True):
            with st.spinner("구글 시트에서 최신 데이터를 가져오는 중..."):
                df_fetched, err = fetch_from_apps_script(st.session_state["db_url"])
                if err:
                    st.error(err)
                else:
                    st.session_state["budget_data"] = df_fetched
                    st.success("동기화 완료!")
                    st.rerun()
    else:
        st.info("🟡 로컬 데이터 모드 사용 중")
        st.caption("구글 시트 DB를 연동하려면 오른쪽 '⚙️ 구글 시트 DB 설정' 탭을 참고하세요.")

    st.markdown("---")
    st.markdown("### 📌 사용 도움말")
    st.caption("1. 구글 시트 연동 후 팀원이 동시에 데이터를 입력할 수 있습니다.")
    st.caption("2. Streamlit Cloud에 배포 시 인증키 없이 URL 등록으로 간단히 동작합니다.")

st.markdown('<div class="main-title">📊 팀 예산 관리 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Streamlit & Google Apps Script 기반 실시간 예산 취합 및 대시보드</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 예산 내역 입력 및 조회", "📈 부장님 보고용 대시보드", "⚙️ 구글 시트 DB 1분 연결 가이드"])

with tab1:
    col_input, col_table = st.columns([1, 2], gap="medium")
    
    with col_input:
        st.subheader("📝 신규 내역 등록")
        with st.form("budget_entry_form", clear_on_submit=True):
            selected_member = st.selectbox(
                "팀원 이름", 
                ["박용은", "홍성강", "이주영", "오길규", "이상태", "직접 입력"]
            )
            if selected_member == "직접 입력":
                selected_member = st.text_input("팀원 이름 직접 입력")

            current_month = datetime.datetime.now().strftime("%Y-%m")
            selected_month = st.text_input("해당 월 (YYYY-MM)", value=current_month)
            
            selected_category = st.selectbox(
                "예산 항목",
                ["수선유지비", "비품", "개량공사", "여비교통비", "복리후생비", "기타"]
            )
            
            amount_input = st.number_input("사용 금액 (원)", min_value=0, step=10000, value=100000)
            note_input = st.text_input("비고 / 사용 목적", placeholder="예: 사무실 집기 구매")
            
            submitted = st.form_submit_button("💾 내역 저장하기", use_container_width=True)
            
            if submitted:
                if not selected_member:
                    st.error("팀원 이름을 입력해주세요.")
                else:
                    new_id = int(datetime.datetime.now().timestamp() * 1000)
                    new_row = {
                        "id": new_id,
                        "month": selected_month,
                        "member": selected_member,
                        "category": selected_category,
                        "amount": int(amount_input),
                        "note": note_input
                    }
                    
                    # Add locally
                    st.session_state["budget_data"] = pd.concat(
                        [pd.DataFrame([new_row]), st.session_state["budget_data"]], 
                        ignore_index=True
                    )
                    
                    # Push to Apps Script if configured
                    if st.session_state["db_url"]:
                        payload = {"action": "add", **new_row}
                        ok, msg = send_to_apps_script(st.session_state["db_url"], payload)
                        if ok:
                            st.success("구글 시트에 기록되었습니다!")
                        else:
                            st.warning(f"로컬엔 저장되었으나 시트 전송 실패: {msg}")
                    else:
                        st.success("내역이 저장되었습니다. (로컬 모드)")
                    
                    st.rerun()

    with col_table:
        st.subheader("📂 등록된 예산 내역")
        df_current = st.session_state["budget_data"].copy()
        
        if not df_current.empty:
            # Filters
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                month_filter = st.multiselect("월별 필터", options=sorted(df_current["month"].unique().tolist()))
            with filter_col2:
                cat_filter = st.multiselect("항목 필터", options=sorted(df_current["category"].unique().tolist()))
            
            # Apply filters
            if month_filter:
                df_current = df_current[df_current["month"].isin(month_filter)]
            if cat_filter:
                df_current = df_current[df_current["category"].isin(cat_filter)]

            # Format amount column for display
            df_display = df_current.copy()
            if "amount" in df_display.columns:
                df_display["금액(원)"] = df_display["amount"].apply(lambda x: f"{int(x):,}원")
            
            # Show Table
            display_cols = [c for c in ["month", "member", "category", "금액(원)", "note"] if c in df_display.columns]
            st.dataframe(
                df_display[display_cols].rename(columns={
                    "month": "해당 월",
                    "member": "팀원",
                    "category": "항목",
                    "note": "비고"
                }),
                use_container_width=True,
                height=350
            )
            
            # Action buttons
            col_csv, col_clear = st.columns([2, 1])
            with col_csv:
                csv_data = df_current.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 CSV 데이터 다운로드",
                    data=csv_data,
                    file_name=f"team_budget_{datetime.date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_clear:
                if st.button("🗑️ 전체 데이터 초기화", type="secondary", use_container_width=True):
                    st.session_state["budget_data"] = pd.DataFrame()
                    if st.session_state["db_url"]:
                        send_to_apps_script(st.session_state["db_url"], {"action": "sync_all", "data": []})
                    st.rerun()
        else:
            st.info("등록된 데이터가 없습니다. 왼쪽 폼에서 내역을 추가해 주세요.")

with tab2:
    st.subheader("📈 예산 집행 현황 및 요약 대시보드")
    df_db = st.session_state["budget_data"].copy()
    
    if df_db.empty or "amount" not in df_db.columns:
        st.warning("분석할 예산 데이터가 존재하지 않습니다.")
    else:
        # Top KPI Metrics
        total_amount = df_db["amount"].sum()
        total_count = len(df_db)
        
        top_cat_series = df_db.groupby("category")["amount"].sum()
        top_category = top_cat_series.idxmax() if not top_cat_series.empty else "-"
        top_cat_amount = top_cat_series.max() if not top_cat_series.empty else 0
        
        avg_amount = total_amount / total_count if total_count > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 집행 예산", f"{total_amount:,} 원")
        m2.metric("총 집행 건수", f"{total_count} 건")
        m3.metric("최다 지출 항목", top_category, f"{top_cat_amount:,} 원")
        m4.metric("건당 평균 지출", f"{int(avg_amount):,} 원")
        
        st.markdown("---")
        
        # Plotly Visualizations
        ch_col1, ch_col2 = st.columns(2)
        
        with ch_col1:
            st.markdown("#### 🍩 항목별 예산 비중")
            cat_df = df_db.groupby("category", as_index=False)["amount"].sum()
            fig_pie = px.pie(
                cat_df, 
                values="amount", 
                names="category", 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
            st.plotly_chart(fig_pie, use_container_width=True)

        with ch_col2:
            st.markdown("#### 👤 팀원별 집행 금액")
            mem_df = df_db.groupby("member", as_index=False)["amount"].sum().sort_values(by="amount", ascending=True)
            fig_bar = px.bar(
                mem_df, 
                x="amount", 
                y="member", 
                orientation='h',
                text_auto=',d',
                color="amount",
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320, coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        
        # Monthly trend and Pivot table
        st.markdown("#### 📅 월별 / 항목별 요약 피벗 테이블")
        pivot_df = pd.pivot_table(
            df_db, 
            index="month", 
            columns="category", 
            values="amount", 
            aggfunc="sum", 
            fill_value=0
        )
        pivot_df["월별 합계"] = pivot_df.sum(axis=1)
        
        # Format currency for table display (Pandas 2.2+ compatibility fix)
        if hasattr(pivot_df, "map"):
            formatted_pivot = pivot_df.map(lambda x: f"{int(x):,}원")
        else:
            formatted_pivot = pivot_df.applymap(lambda x: f"{int(x):,}원")

        st.dataframe(formatted_pivot, use_container_width=True)

with tab3:
    st.subheader("🛠️ Google Apps Script 백엔드 연동 가이드 (1분 소요)")
    st.markdown("""
    Streamlit 앱을 GitHub 및 Streamlit Cloud에 배포할 때, 복잡한 GCP OAuth/인증서 없이 구글 시트를 DB로 바로 사용할 수 있습니다.
    """)
    
    st.markdown("### 1단계: 구글 시트 작성")
    st.write("새 구글 스프레드시트를 만들고 첫 번째 행에 다음 헤더를 채워넣으세요:")
    st.code("ID | 날짜 | 팀원 | 항목 | 금액 | 비고", language="text")

    st.markdown("### 2단계: Google Apps Script 코드 작성")
    st.write("메뉴 상단의 **[확장 프로그램] > [Apps Script]**를 클릭한 후, 아래 코드를 모두 붙여넣으세요:")

    apps_script_code = """function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var rows = sheet.getDataRange().getValues();
  if (rows.length <= 1) return responseJSON([]);
  var data = [];
  for (var i = 1; i < rows.length; i++) {
    data.push({
      id: rows[i][0],
      month: String(rows[i][1]),
      member: rows[i][2],
      category: rows[i][3],
      amount: Number(rows[i][4]),
      note: rows[i][5] || ""
    });
  }
  return responseJSON(data);
}

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var payload = JSON.parse(e.postData.contents);
  
  if (payload.action === "add") {
    sheet.appendRow([payload.id, payload.month, payload.member, payload.category, payload.amount, payload.note]);
    return responseJSON({ status: "success" });
  } else if (payload.action === "sync_all") {
    sheet.clear();
    sheet.appendRow(["ID", "날짜", "팀원", "항목", "금액", "비고"]);
    if (payload.data && payload.data.length > 0) {
      payload.data.forEach(function(item) {
        sheet.appendRow([item.id, item.month, item.member, item.category, item.amount, item.note || ""]);
      });
    }
    return responseJSON({ status: "success" });
  }
  return responseJSON({ status: "error", message: "Unknown action" });
}

function responseJSON(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}"""

    st.code(apps_script_code, language="javascript")

    st.markdown("### 3단계: 웹 앱 배포 설정 (중요 ⚠️)")
    st.markdown("""
    1. Apps Script 우측 상단의 **[배포] > [새 배포]** 버튼을 클릭합니다.
    2. 톱니바퀴 ⚙️ 아이콘을 누르고 **[웹 앱(Web app)]**을 선택합니다.
    3. 아래와 같이 설정 후 배포합니다:
       - **다음 사용자 권한으로 실행 (Execute as)**: `나 (Me)`
       - **액세스할 수 있는 사용자 (Who has access)**: `모든 사용자 (Anyone)` 👈 **필수 설정**
    4. 생성된 **웹 앱 URL (https://script.google.com/macros/s/.../exec)**을 복사하여 이 앱의 사이드바 DB URL 입력 칸에 넣으세요!
    """)
