import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import random
import yfinance as yf
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import re
import csv
from io import StringIO
from pathlib import Path
import unicodedata
import glob

# ==================== 환경 변수 로드 ====================
load_dotenv()

# ==================== OpenAI 클라이언트 초기화 ====================
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=openai_api_key) if openai_api_key else None
except Exception:
    client = None

# ==================== Streamlit 기본 설정 ====================
st.set_page_config(
    page_title="슬기로운 무역 마케팅 서비스",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 국가 옵션 (선택형) ====================
COUNTRY_OPTIONS = [
    "United States", "Canada", "Mexico",
    "Brazil", "Argentina", "Chile",
    "United Kingdom", "Germany", "France", "Italy", "Spain", "Netherlands",
    "Sweden", "Norway", "Denmark", "Poland",
    "Turkey", "Russia",
    "United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait",
    "South Africa", "Egypt", "Nigeria",
    "China", "Japan", "South Korea", "Taiwan", "Hong Kong",
    "Singapore", "Malaysia", "Thailand", "Vietnam", "Indonesia", "Philippines", "India",
    "Australia", "New Zealand"
]

COUNTRY_TO_ISO2 = {
    "United States": "US", "Canada": "CA", "Mexico": "MX",
    "Brazil": "BR", "Argentina": "AR", "Chile": "CL",
    "United Kingdom": "GB", "Germany": "DE", "France": "FR", "Italy": "IT", "Spain": "ES", "Netherlands": "NL",
    "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Poland": "PL",
    "Turkey": "TR", "Russia": "RU",
    "United Arab Emirates": "AE", "Saudi Arabia": "SA", "Qatar": "QA", "Kuwait": "KW",
    "South Africa": "ZA", "Egypt": "EG", "Nigeria": "NG",
    "China": "CN", "Japan": "JP", "South Korea": "KR", "Taiwan": "TW", "Hong Kong": "HK",
    "Singapore": "SG", "Malaysia": "MY", "Thailand": "TH", "Vietnam": "VN", "Indonesia": "ID", "Philippines": "PH", "India": "IN",
    "Australia": "AU", "New Zealand": "NZ",
}

# ==================== CSV 소스(파일명 기준) ====================
CSV_BUYER_FILES = {
    "KOTRA_해외바이어현황_20240829": "대한무역투자진흥공사_해외바이어 현황_20240829.csv",
    "조달청_해외조달_업체물품_20250821": "조달청_해외조달_업체물품_20250821.csv",
    "중진공_국가별해외바이어수_20250711": "중소벤처기업진흥공단_온라인수출플랫폼에 등록된 국가별 해외바이어 수_20250711.csv",
    "중진공_해외바이어구매오퍼_20241231": "중소벤처기업진흥공단_해외바이어 구매오퍼 정보_20241231.csv",
    "중진공_해외바이어인콰이어리_20241230": "중소벤처기업진흥공단_해외바이어 인콰이어리 신청_20241230.csv",
    "무보_화장품바이어_20200812": "한국무역보험공사_화장품 바이어 정보_20200812.csv",
}

# ==================== 산업 → 키워드(영문) 매핑 ====================
# 제품 카테고리 입력 없이 '산업'만으로 텍스트 매칭하기 위한 내부 룰
INDUSTRY_KEYWORDS = {
    "화장품/뷰티": [
        "cosmetics", "beauty", "skincare", "skin care", "makeup", "personal care",
        "lotion", "cream", "serum", "toner", "cleanser", "sunscreen", "mask", "fragrance"
    ],
    "전자제품": [
        "electronics", "electronic", "device", "gadget", "semiconductor", "chip",
        "display", "battery", "charger", "adapter", "smart", "iot", "sensor", "led"
    ],
    "식품": [
        "food", "beverage", "snack", "drink", "coffee", "tea", "sauce",
        "noodle", "ramen", "instant", "frozen", "seafood", "meat", "fruit"
    ],
    "섬유/의류": [
        "apparel", "clothing", "garment", "textile", "fabric", "fashion",
        "yarn", "cotton", "polyester", "knit", "denim", "outerwear", "sportswear"
    ],
    "자동차 부품": [
        "auto", "automotive", "car", "vehicle", "spare parts", "parts",
        "engine", "brake", "filter", "tire", "tyre", "transmission", "sensor"
    ],
    "기계/설비": [
        "machinery", "equipment", "industrial", "manufacturing", "factory",
        "pump", "valve", "compressor", "tool", "robot", "automation", "cnc"
    ],
    "의료기기": [
        "medical", "healthcare", "diagnostic", "surgical", "hospital",
        "clinic", "monitor", "disposable", "sterile"
    ],
    "기타": ["import", "export", "trade", "sourcing", "procurement"]
}

# ==================== CSS (원형 유지) ====================
st.markdown("""
<style>
.block-container{ padding: 2rem 8rem 5rem !important; }  
:root{
  --bg:#ffffff; --card:#ffffff; --line:#e5e7eb; --text:#0f172a; --muted:#64748b;
  --green:#16a34a; --green-weak:#dcfce7; --danger:#ef4444; --warn:#f59e0b;
}
.main,[data-testid="stAppViewContainer"]{ background: var(--bg); }
[data-testid="stSidebar"]{ background: var(--bg); border-right: 1px solid var(--line); }
h1,h2,h3{ color: var(--text); text-shadow:none !important; }
h1{ font-weight:800; font-size:2.2rem; margin-bottom:0.25rem; }
h2{ font-weight:700; font-size:1.4rem; }
h3{ font-weight:650; font-size:1.1rem; }
.small-muted{ color: var(--muted); font-size:0.92rem; }
.stButton>button{
  background: var(--green); color:#fff; border:1px solid var(--green);
  border-radius:12px; padding:10px 14px; font-weight:700; box-shadow:none !important;
}
[data-testid="stMetric"]{
  background: var(--card); border-radius:14px; padding:14px 16px; box-shadow:none !important;
}
.stProgress > div > div > div > div{ background: var(--green) !important; }
.ticker-wrapper{
  background: var(--card); border-radius:14px; height:70px; overflow:hidden;
  position:relative; padding:12px;
}
@keyframes scroll{ 0%{transform:translateY(0);} 100%{transform:translateY(-50%);} }
.ticker-content{ display:flex; flex-direction:column; animation: scroll 28s linear infinite; }
.item-row{
  background: var(--card); padding:10px 12px; margin-bottom:10px; border-radius:12px;
  display:flex; align-items:center; gap:10px;
}
.time-tag{
  color: var(--muted); font-size:0.75rem; font-family:monospace; font-weight:700; white-space:nowrap;
}
.item-text{ font-size:0.92rem; font-weight:650; flex:1; color: var(--text); padding-left:10px; }
.badge{
  display:inline-flex; align-items:center; padding:2px 10px; border-radius:999px;
  font-size:0.75rem; font-weight:750; background:#f8fafc; color: var(--muted);
}
.streamlit-expanderHeader{
  background: var(--card) !important; border:1px solid var(--line) !important; border-radius:12px !important;
}
.logo-box{ background: var(--card); border-radius:16px; padding:16px; text-align:center; }
.logo-text{ font-size:18px; font-weight:900; color: var(--text); }
.logo-dot{
  display:inline-block; width:8px; height:8px; border-radius:999px; background: var(--green); margin-right:8px;
}
.page-header{
  position:sticky; top:0; background: var(--bg); z-index:100; padding:1rem 0;
  margin-bottom:1rem; border-bottom:2px solid var(--line);
}
</style>
""", unsafe_allow_html=True)

# ==================== 세션 스테이트 ====================
if "page_mode" not in st.session_state:
    st.session_state.page_mode = "home"

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "안녕하세요! 무역 전문 AI 챗봇입니다. HS 코드, 관세, 통관 규정에 대해 무엇이든 물어보세요!"}
    ]

if "matched_buyers" not in st.session_state:
    st.session_state.matched_buyers = []

# ==================== CSV 로더 유틸 (한글파일명/인코딩/구분자/경로 커버) ====================
def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)

def _find_local_csv_by_name(filename: str) -> str | None:
    target = _nfc(filename)
    candidates = [
        Path.cwd() / filename,
        Path.cwd() / "data" / filename,
        Path.cwd() / "datasets" / filename,
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    for p in glob.glob("**/*.csv", recursive=True):
        base = _nfc(Path(p).name)
        if base == target:
            return str(Path(p))
    return None

def _read_csv_bytes_flexible(raw: bytes) -> tuple[pd.DataFrame, str, str]:
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]
    text = None
    used_enc = None

    for enc in encodings:
        try:
            text = raw.decode(enc)
            used_enc = enc
            break
        except Exception:
            continue

    if text is None:
        text = raw.decode("cp949", errors="replace")
        used_enc = "cp949(errors=replace)"

    sample = text[:5000]
    delim_candidates = [",", ";", "\t", "|"]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=delim_candidates)
        sep = dialect.delimiter
    except Exception:
        sep = ","

    df = pd.read_csv(StringIO(text), sep=sep, engine="python", on_bad_lines="skip")

    # 컬럼이 1개면 구분자 오탐 가능 → 재시도
    if df.shape[1] == 1:
        for alt in delim_candidates:
            if alt == sep:
                continue
            df2 = pd.read_csv(StringIO(text), sep=alt, engine="python", on_bad_lines="skip")
            if df2.shape[1] > 1:
                df = df2
                sep = alt
                break

    return df, used_enc, sep

def _read_csv_flexible_from_path(path: str) -> tuple[pd.DataFrame, str, str]:
    raw = Path(path).read_bytes()
    return _read_csv_bytes_flexible(raw)

def _norm_col(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", "", s)
    s = s.replace("-", "").replace("_", "")
    return s

def _infer_col(cols, keywords):
    normed = {c: _norm_col(c) for c in cols}
    for c, nc in normed.items():
        for kw in keywords:
            if kw in nc:
                return c
    return None

def _safe_get(row, col):
    if not col:
        return ""
    v = row.get(col)
    if pd.isna(v):
        return ""
    return str(v).strip()

def _parse_date_any(x: str):
    if not x:
        return None
    x = str(x).strip()
    for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m", "%Y.%m", "%Y/%m"]:
        try:
            return datetime.strptime(x, fmt)
        except Exception:
            continue
    return None

@st.cache_data(ttl=60 * 60)
def load_and_standardize_buyer_csv(resolved_paths: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    meta = []

    for source_name, path in resolved_paths.items():
        if not path:
            meta.append({"source": source_name, "status": "missing", "detail": "path not resolved"})
            continue

        try:
            df, enc, sep = _read_csv_flexible_from_path(path)
        except Exception as e:
            meta.append({"source": source_name, "status": "fail", "detail": str(e)})
            continue

        cols = list(df.columns)

        col_company = _infer_col(cols, ["회사", "기업", "업체", "바이어", "buyer", "company", "corporation", "상호", "기관명", "조직"])
        col_country = _infer_col(cols, ["국가", "country", "nation", "소재국", "거주국", "지역", "state"])
        col_city = _infer_col(cols, ["도시", "city", "소재지", "소재도시", "지역"])
        col_product = _infer_col(cols, ["품목", "제품", "item", "product", "오퍼", "inquiry", "관심", "수요", "구매", "구매품목"])
        col_hs = _infer_col(cols, ["hs", "hscode", "hs코드", "품목코드", "세번"])
        col_name = _infer_col(cols, ["담당자", "contact", "name", "성명", "대표자", "buyername"])
        col_email = _infer_col(cols, ["이메일", "email", "e-mail", "메일"])
        col_phone = _infer_col(cols, ["전화", "phone", "tel", "연락처", "mobile", "핸드폰"])
        col_web = _infer_col(cols, ["웹", "홈페이지", "website", "url", "domain", "사이트"])
        col_date = _infer_col(cols, ["일자", "날짜", "등록", "신청", "date", "created", "updated", "연도", "year"])

        for _, r in df.iterrows():
            company = _safe_get(r, col_company) or "Unknown Company"
            country = _safe_get(r, col_country)
            city = _safe_get(r, col_city)
            product = _safe_get(r, col_product)
            hs = _safe_get(r, col_hs)
            contact = _safe_get(r, col_name)
            email = _safe_get(r, col_email)
            phone = _safe_get(r, col_phone)
            website = _safe_get(r, col_web)
            date_raw = _safe_get(r, col_date)
            dt = _parse_date_any(date_raw)

            rows.append({
                "company_name": company,
                "country": country,
                "city": city,
                "product_text": product,
                "hs_code": hs,
                "contact_person": contact,
                "email": email,
                "phone": phone,
                "website": website,
                "date": dt,
                "date_raw": date_raw,
                "source": source_name,
            })

        meta.append({
            "source": source_name,
            "status": "ok",
            "rows": len(df),
            "cols": len(cols),
            "encoding": enc,
            "sep": sep,
            "path": path,
        })

    df_all = pd.DataFrame(rows)
    df_meta = pd.DataFrame(meta)

    if not df_all.empty:
        for c in ["company_name", "country", "city", "product_text", "hs_code", "contact_person",
                  "email", "phone", "website", "date_raw", "source"]:
            df_all[c] = df_all[c].fillna("").astype(str).str.strip()

    return df_all, df_meta

def score_buyer_record(row: dict,
                       industry: str,
                       hs_code: str,
                       countries_selected: list[str],
                       require_email: bool,
                       source_weight: dict):
    """
    ✅ 판별 기준: 산업(키워드) + HS 코드
    - industry: product_text/company_name에 키워드가 있으면 가점
    - hs_code: row의 hs_code에 포함되면 가점
    - 국가/연락처/웹/폰 등 가점 유지
    """
    score = 0
    prod = (row.get("product_text", "") or "").lower()
    comp = (row.get("company_name", "") or "").lower()
    hs = (row.get("hs_code", "") or "").replace(" ", "")
    country_val = (row.get("country", "") or "").lower()

    # 산업 키워드 매칭
    kws = INDUSTRY_KEYWORDS.get(industry, []) or []
    if kws:
        if any(kw.lower() in prod for kw in kws):
            score += 30
        if any(kw.lower() in comp for kw in kws):
            score += 10

    # HS 매칭
    if hs_code:
        hk = hs_code.replace(" ", "")
        if hk and hk in hs:
            score += 45

    # 국가 필터
    if countries_selected:
        hit = any((c.lower() in country_val) for c in countries_selected if c)
        if hit:
            score += 20
        else:
            score -= 15

    # 연락처 가점
    if row.get("email"):
        score += 20
    if row.get("contact_person"):
        score += 8
    if row.get("phone"):
        score += 6
    if row.get("website"):
        score += 6

    # 이메일 필수 옵션
    if require_email and not row.get("email"):
        score -= 999

    # 내부 최신성 가점(표시에는 안 씀)
    dt = row.get("date")
    if isinstance(dt, datetime):
        days_ago = (datetime.now() - dt).days
        if days_ago <= 90:
            score += 10
        elif days_ago <= 365:
            score += 5

    # 내부 소스 가중치(표시에는 안 씀)
    score += int(source_weight.get(row.get("source", ""), 0))
    return max(-999, min(100, score))

def dedupe_buyer_candidates(records: list[dict]) -> list[dict]:
    if not records:
        return records
    df = pd.DataFrame(records)
    if df.empty:
        return records

    df["email_key"] = df["email"].fillna("").astype(str).str.lower().str.strip()
    df["cc_key"] = (
        df["company_name"].fillna("").astype(str).str.lower().str.strip()
        + "|" +
        df["country_targets"].apply(lambda x: ",".join(x) if isinstance(x, list) else str(x)).str.lower().str.strip()
    )

    with_email = df[df["email_key"] != ""].sort_values("match_score", ascending=False).drop_duplicates("email_key")
    no_email = df[df["email_key"] == ""].sort_values("match_score", ascending=False).drop_duplicates("cc_key")
    out = pd.concat([with_email, no_email], axis=0).sort_values("match_score", ascending=False)
    return out.drop(columns=["email_key", "cc_key"]).to_dict(orient="records")

# ==================== OpenAI API (원형 유지) ====================
def get_openai_response(prompt, system_message="당신은 무역 전문가입니다."):
    if not client:
        return "⚠️ OpenAI API가 설정되지 않았습니다."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=900
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ API 오류: {str(e)}"

def generate_buyer_email(buyer_name, country, industry, purchase_history, contact_person=None, email=None):
    prompt = f"""
다음 바이어에게 보낼 비즈니스 이메일을 한국어로 작성해주세요.

- 회사명: {buyer_name}
- 국가: {country}
- 산업: {industry}
- 관심 제품/범주: {', '.join(purchase_history)}
- 담당자(알려진 경우): {contact_person or '미확인'}
- 이메일(알려진 경우): {email or '미확인'}

한국 제품 수출 업체로서 파트너십을 제안하는 전문적이고 간결한 이메일을 작성해주세요.
제목과 본문을 포함해주세요.
"""
    return get_openai_response(prompt, "당신은 국제 비즈니스 커뮤니케이션 전문가입니다.")

def translate_email(email_content, target_language):
    prompt = f"""
다음 이메일을 {target_language}로 번역해주세요.
비즈니스 이메일 톤을 유지하세요.

{email_content}
"""
    return get_openai_response(prompt, "당신은 전문 비즈니스 번역가입니다.")

# ==================== HOME 데이터(원형 유지) ====================
def generate_news_data():
    news = [
        {"시간": "09:15", "내용": "🇺🇸 미 서안 항만 적체 해소 가속화", "중요도": "높음"},
        {"시간": "10:30", "내용": "🇨🇳 한-아세안 FTA 활용률 역대 최고치 경신", "중요도": "보통"},
        {"시간": "11:45", "내용": "🇪🇺 EU 탄소국경조정제도 본격 시행 임박", "중요도": "보통"},
        {"시간": "13:20", "내용": "🇰🇷 K-뷰티, 중동 시장 점유율 15% 돌파", "중요도": "높음"},
        {"시간": "14:50", "내용": "🇯🇵 2026 홍콩 글로벌 소싱 페어 개막", "중요도": "낮음"},
        {"시간": "15:30", "내용": "🇻🇳 베트남 섬유 산업 수출 30% 증가", "중요도": "보통"},
        {"시간": "16:10", "내용": "🇮🇳 인도 IT 서비스 수출 급증세", "중요도": "높음"},
    ]
    return news * 4

def generate_exchange_data():
    currencies = ["USD", "EUR", "JPY", "CNY", "GBP"]
    base_rate = {"USD": 1320, "EUR": 1450, "JPY": 900, "CNY": 182, "GBP": 1680}
    out = []
    for currency in currencies:
        change = random.uniform(-3, 3)
        out.append({
            "통화": currency,
            "현재가": f"{base_rate[currency] + change:.2f}",
            "변동": f"{change:+.2f}",
            "변동률": f"{(change / base_rate[currency] * 100):+.2f}%"
        })
    return out * 4

def generate_search_trend():
    keywords = ["LED 조명", "화장품", "자동차 부품", "반도체", "의류"]
    counts = [random.randint(500, 2000) for _ in range(5)]
    return pd.DataFrame({"키워드": keywords, "검색량": counts})

@st.cache_data(ttl=60 * 60)
def generate_exchange_chart_data(days: int = 120):
    end = datetime.now()
    start = end - timedelta(days=days)
    symbols = {"USD/KRW": "KRW=X", "EUR/KRW": "EURKRW=X"}
    series_list = []
    for name, symbol in symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end)
            if not df.empty and "Close" in df.columns:
                series_list.append(df["Close"].rename(name))
        except Exception:
            continue

    if not series_list:
        dates = pd.date_range(start=start, end=end, freq="D")
        data = {
            "USD/KRW": [1320 + random.uniform(-10, 10) for _ in range(len(dates))],
            "EUR/KRW": [1450 + random.uniform(-15, 15) for _ in range(len(dates))],
        }
        return pd.DataFrame(data, index=dates).reset_index().rename(columns={"index": "Timestamp"})

    result_df = pd.concat(series_list, axis=1).reset_index()
    if "Date" in result_df.columns:
        result_df = result_df.rename(columns={"Date": "Timestamp"})
    elif "index" in result_df.columns:
        result_df = result_df.rename(columns={"index": "Timestamp"})
    result_df["Timestamp"] = pd.to_datetime(result_df["Timestamp"])
    return result_df.sort_values("Timestamp")

# ==================== 사이드바 ====================
with st.sidebar:
    st.markdown("""
        <div class="logo-box">
            <div class="logo-text"><span class="logo-dot"></span>슬기로운 서비스</div>
            <div class="small-muted" style="margin-top:6px;">Trade Marketing Suite</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 🔧 빠른 도구")
    b1, b2 = st.columns(2)
    with b1:
        st.button("환율 계산", use_container_width=True, key="calc_btn")
    with b2:
        if st.button("AI 챗봇", use_container_width=True, key="chat_btn"):
            st.session_state.page_mode = "chatbot"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📂 주요 서비스")

    nav_items = [
        {"icon": "🌏", "title": "국가별 수출입 데이터"},
        {"icon": "📄", "title": "서류 자동 완성"},
        {"icon": "💱", "title": "실시간 환율"},
        {"icon": "🎯", "title": "SEO 서비스"},
        {"icon": "🤝", "title": "AI 바이어 매칭 엔진"},
    ]

    for item in nav_items:
        with st.expander(f"{item['icon']} {item['title']}"):
            st.markdown(f"**{item['title']} 서비스**")
            if item["title"] == "AI 바이어 매칭 엔진":
                if st.button("바로가기 →", key=f"nav_{item['title']}", use_container_width=True):
                    st.session_state.page_mode = "buyer_matching"
                    st.rerun()
            else:
                st.button("바로가기 →", key=f"nav_{item['title']}", use_container_width=True, disabled=True)

# ==================== 라우팅 ====================
# HOME
if st.session_state.page_mode == "home":
    st.title("슬기로운 무역 마케팅 서비스")
    st.markdown('<div class="small-muted">🚀 우리 회사의 마케팅 정보를 원스톱으로 경험해보세요</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    option_menu(
        menu_title=None,
        options=["Home", "Task", "Theme", "Settings"],
        icons=["house-fill", "list-task", "palette-fill", "gear-fill"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background": "#ffffff", "border-radius": "16px"},
            "icon": {"color": "#16a34a", "font-size": "20px"},
            "nav-link": {
                "font-size": "15px", "text-align": "center", "margin": "6px",
                "padding": "10px 16px", "border-radius": "12px",
                "color": "#0f172a", "font-weight": "650",
                "background": "#ffffff", "border": "1px solid #e5e7eb",
            },
            "nav-link-selected": {
                "background": "#dcfce7", "color": "#166534", "font-weight": "850",
                "border": "1px solid #16a34a",
            },
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        news_list = generate_news_data()
        news_html = ""
        for item in news_list:
            tone = {"높음": "danger", "보통": "warn", "낮음": "ok"}[item["중요도"]]
            border_color = {"danger": "var(--danger)", "warn": "var(--warn)", "ok": "var(--green)"}[tone]
            news_html += f'<div class="item-row"><span class="time-tag">[{item["시간"]}]</span><span class="item-text" style="border-left: 3px solid {border_color};">{item["내용"]}</span><span class="badge" style="border-color:{border_color}; color:{border_color};">{item["중요도"]}</span></div>'
        st.markdown(f'<div class="ticker-wrapper"><div class="ticker-content">{news_html}</div></div>', unsafe_allow_html=True)

    with col2:
        exchange_list = generate_exchange_data()
        exchange_html = ""
        for item in exchange_list:
            is_positive = float(item["변동"]) >= 0
            color = "var(--green)" if is_positive else "var(--danger)"
            arrow = "▲" if is_positive else "▼"
            exchange_html += f'<div class="item-row"><div style="flex:1;"><div class="exchange-head" style="border-left: 3px solid {color};"><span class="currency-name">{item["통화"]}/KRW</span><span class="change-rate" style="color:{color};">{arrow} {item["변동률"]}</span></div><div class="exchange-value"><span class="rate-value">{item["현재가"]}</span><span class="change-value" style="color:{color};">({item["변동"]})</span></div></div></div>'
        st.markdown(f'<div class="ticker-wrapper"><div class="ticker-content">{exchange_html}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("#### 📝 수출 서류 준비")
        st.progress(0.75)
        st.metric("진행률", "75%", delta="↑ 15%")

    with c2:
        st.markdown("#### 🚢 물류 처리")
        st.progress(0.45)
        st.metric("진행률", "45%", delta="↓ 5%")

    with c3:
        st.markdown("#### 💼 바이어 매칭")
        st.progress(0.90)
        st.metric("진행률", "90%", delta="↑ 20%")

    with c4:
        search_df = generate_search_trend().sort_values("검색량", ascending=False).reset_index(drop=True)
        st.dataframe(search_df, use_container_width=True, hide_index=True)

    left, right = st.columns([1, 2])
    chart_data = generate_exchange_chart_data()

    with left:
        if not chart_data.empty and len(chart_data) > 1:
            latest = chart_data.iloc[-1]
            prev = chart_data.iloc[-2]
            for col_name in ["USD/KRW", "EUR/KRW"]:
                if col_name in chart_data.columns:
                    cur = float(latest[col_name])
                    prv = float(prev[col_name])
                    diff = cur - prv
                    pct = (diff / prv * 100) if prv != 0 else 0
                    st.metric(col_name, f"{cur:,.2f} 원", f"{diff:+.2f} ({pct:+.2f}%)")

    with right:
        if not chart_data.empty and "Timestamp" in chart_data.columns:
            st.line_chart(chart_data.set_index("Timestamp"))

# CHATBOT
elif st.session_state.page_mode == "chatbot":
    st.markdown('<div class="page-header">', unsafe_allow_html=True)
    col_back, col_title = st.columns([1, 9])
    with col_back:
        if st.button("⬅️ 홈으로", key="back_home_chat", use_container_width=True):
            st.session_state.page_mode = "home"
            st.rerun()
    with col_title:
        st.markdown("## 💬 AI 무역 챗봇")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("HS 코드, 관세, 통관 규정에 대해 무엇이든 물어보세요!")
    st.markdown("---")

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if prompt := st.chat_input("질문을 입력하세요..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.spinner("AI가 답변을 생성 중입니다..."):
            response = get_openai_response(
                prompt,
                "당신은 국제 무역과 관세 전문가입니다. HS 코드, 통관 규정, 필요 서류, 관세율에 대해 정확하고 상세한 답변을 한국어로 제공합니다."
            )
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, _ = st.columns([1, 5])
    with col_btn1:
        if st.button("🗑️ 대화 초기화", key="reset_chat", use_container_width=True):
            st.session_state.chat_messages = [{"role": "assistant", "content": "안녕하세요! 무역 전문 AI 챗봇입니다. HS 코드, 관세, 통관 규정에 대해 무엇이든 물어보세요!"}]
            st.rerun()

# BUYER MATCHING (CSV 기반) — ✅ 산업+HS만 사용
elif st.session_state.page_mode == "buyer_matching":
    st.markdown('<div class="page-header">', unsafe_allow_html=True)
    col_back, col_title = st.columns([1, 9])
    with col_back:
        if st.button("⬅️ 홈으로", key="back_home_buyer", use_container_width=True):
            st.session_state.page_mode = "home"
            st.session_state.matched_buyers = []
            keys_to_delete = [k for k in st.session_state.keys()
                              if str(k).startswith("email_content_")
                              or str(k).startswith("trans_")
                              or str(k).startswith("generate_email_")]
            for k in keys_to_delete:
                del st.session_state[k]
            st.rerun()
    with col_title:
        st.markdown("## 🤝 AI 바이어 매칭 엔진")
    st.markdown("</div>", unsafe_allow_html=True)

    st.success("✅ 로딩 완료.")
    st.markdown("---")

    # (1) 로컬 파일 경로 resolve
    resolved_paths = {k: _find_local_csv_by_name(v) for k, v in CSV_BUYER_FILES.items()}

    # (2) 데이터 로드/정규화 (UI 없이)
    with st.spinner("📦 CSV 로딩/정규화 중..."):
        df_all, df_meta = load_and_standardize_buyer_csv(resolved_paths)

    # (3) 입력 UI: 제품 카테고리 없음 (산업 + HS만)
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### ✍️ 제품 정보 입력")
        industry = st.selectbox("산업 분야", [
            "화장품/뷰티", "전자제품", "식품", "섬유/의류",
            "자동차 부품", "기계/설비", "의료기기", "기타"
        ])
        hs_code = st.text_input("HS 코드 (선택)", placeholder="예: 3304, 8517")
        max_results = st.slider("최대 후보 수", 10, 300, 60, 10)

    with right:
        st.markdown("### 🌍 타겟 국가 선택")
        select_all = st.checkbox("✅ 전체 선택", value=False, key="country_select_all_csv")
        default_countries = COUNTRY_OPTIONS if select_all else ["United States"]
        selected_countries = st.multiselect(
            "타겟 국가 (복수 선택 가능)",
            options=COUNTRY_OPTIONS,
            default=default_countries,
            key="country_multiselect_csv"
        )
        require_email = st.checkbox("📧 이메일 있는 후보만", value=False)

    st.markdown("<br>", unsafe_allow_html=True)

    # (4) 검색 버튼
    source_weight = {
        "중진공_해외바이어구매오퍼_20241231": 6,
        "중진공_해외바이어인콰이어리_20241230": 6,
        "KOTRA_해외바이어현황_20240829": 4,
        "조달청_해외조달_업체물품_20250821": 3,
        "무보_화장품바이어_20200812": 2,
        "중진공_국가별해외바이어수_20250711": 0,
    }

    if st.button("🔍 (바이어 후보 발굴", use_container_width=True, type="primary"):
        if df_all.empty:
            st.error("⚠️ 데이터가 비어있습니다. 배포 환경에서는 로컬에 파일이 없을 수 있습니다. 프로젝트 폴더(또는 data/)에 포함시켜 주세요.")
        else:
            countries_selected = selected_countries[:]

            df = df_all.copy()
            df["match_score"] = df.apply(
                lambda r: score_buyer_record(
                    r.to_dict(),
                    industry=industry,
                    hs_code=hs_code.strip(),
                    countries_selected=countries_selected,
                    require_email=require_email,
                    source_weight=source_weight,
                ),
                axis=1
            )

            # HS가 있으면 더 엄격, 없으면 완화
            if hs_code.strip():
                df = df[df["match_score"] >= 35]
            else:
                df = df[df["match_score"] >= 20]

            df = df.sort_values("match_score", ascending=False)

            buyers = []
            for _, row in df.iterrows():
                website = row.get("website", "")
                email = row.get("email", "")
                domain_guess = ""

                if website:
                    d = str(website).strip().lower()
                    d = d.replace("https://", "").replace("http://", "").split("/")[0]
                    domain_guess = d
                elif email and "@" in str(email):
                    domain_guess = str(email).split("@")[-1].strip().lower()

                buyers.append({
                    "company_name": row.get("company_name", "Unknown Company"),
                    "domain": domain_guess,
                    "website": website if website else (f"https://{domain_guess}" if domain_guess else ""),
                    "industry": industry,
                    "country_targets": selected_countries,
                    "email": email if email else (f"info@{domain_guess}" if domain_guess else ""),
                    "contact_person": row.get("contact_person", "") or "미추출",

                    # 내부 정렬용(출력에서는 숨김)
                    "match_score": int(row.get("match_score", 0)),
                    "source": row.get("source", "CSV"),

                    # 원천 정보 표시(요청한 것만 유지)
                    "_raw_country": row.get("country", ""),
                    "_raw_city": row.get("city", ""),
                    "_raw_product_text": row.get("product_text", ""),
                    "_raw_hs": row.get("hs_code", ""),
                    "_raw_phone": row.get("phone", ""),
                })

            buyers = dedupe_buyer_candidates(buyers)
            buyers = buyers[:max_results]
            st.session_state.matched_buyers = buyers

            if buyers:
                st.success(f"🎉 {len(buyers)}개의 바이어 후보를 찾았습니다! (산업+HS 기반)")
            else:
                st.warning("검색 결과가 없습니다. HS 코드를 입력하거나, 산업 분야를 바꿔보세요.")

    # (5) 결과 표시: 날짜/매칭점수/소스 출력은 삭제 유지
    if st.session_state.matched_buyers:
        st.markdown("---")
        st.markdown("### 🎯 검색된 바이어 후보 목록")
        st.caption("✅ 이메일/담당자가 존재할 경우 표시됩니다.")

        for idx, buyer in enumerate(st.session_state.matched_buyers):
            key = f"{buyer.get('domain','') or buyer.get('company_name','') }|{idx}"
            has_real_email = bool(buyer.get("email")) and ("@" in buyer.get("email", ""))
            badge = "✅ 연락처 확보" if has_real_email or buyer.get("contact_person") not in ["", "미추출"] else "🔍 미확인"

            with st.expander(
                f"**{idx+1}. {buyer['company_name']}** ({buyer.get('domain','') or 'no-domain'}) - {badge}",
                expanded=(idx == 0)
            ):
                col_info, col_action = st.columns([2, 1])

                with col_info:
                    st.markdown(f"""
**🌐 웹사이트:** {buyer.get('website','N/A') or 'N/A'}  
**🏭 산업:** {buyer.get('industry','N/A')}  
**🌍 타겟 국가:** {", ".join(buyer.get("country_targets", []))}  
**🌍 (원천국가/도시):** {buyer.get("_raw_country","")} {buyer.get("_raw_city","")}  
**📦 (원천 품목/오퍼):** {buyer.get("_raw_product_text","") or 'N/A'}  
**🧾 (원천 HS):** {buyer.get("_raw_hs","") or 'N/A'}  
**👤 담당자:** {buyer.get("contact_person","N/A")}  
**📧 이메일:** {buyer.get("email","N/A")}  
**☎️ 전화:** {buyer.get("_raw_phone","") or 'N/A'}  
""")

                with col_action:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.info("CSV 기반\n연락처가 있으면\n바로 표시됩니다.")
                    st.markdown("<br>", unsafe_allow_html=True)

                    if st.button("✉️ 제안 이메일", key=f"email_btn_{key}", use_container_width=True):
                        st.session_state[f"generate_email_{key}"] = True
                        st.rerun()

                if st.session_state.get(f"generate_email_{key}", False):
                    st.markdown("---")
                    st.markdown("#### 📧 AI 생성 제안 이메일")

                    contact_person = buyer.get("contact_person")
                    email_addr = buyer.get("email")

                    # 관심 제품/범주: 산업 + HS
                    interest = [buyer.get("industry", "")]
                    if hs_code.strip():
                        interest.append(f"HS {hs_code.strip()}")

                    if f"email_content_{key}" not in st.session_state:
                        with st.spinner("AI가 맞춤 이메일을 작성 중입니다..."):
                            email_content = generate_buyer_email(
                                buyer_name=buyer.get("company_name", ""),
                                country=", ".join(buyer.get("country_targets", [])) or buyer.get("_raw_country", ""),
                                industry=buyer.get("industry", ""),
                                purchase_history=[x for x in interest if x],
                                contact_person=None if contact_person == "미추출" else contact_person,
                                email=email_addr
                            )
                            st.session_state[f"email_content_{key}"] = email_content

                    st.text_area("🇰🇷 한국어 이메일", st.session_state[f"email_content_{key}"], height=280, key=f"email_kr_{key}")

                    st.markdown("#### 🌐 자동 번역")
                    col_t1, col_t2 = st.columns(2)

                    with col_t1:
                        if st.button("🇺🇸 영어로 번역", key=f"trans_en_{key}", use_container_width=True):
                            with st.spinner("영어로 번역 중..."):
                                st.session_state[f"trans_en_{key}"] = translate_email(
                                    st.session_state[f"email_content_{key}"], "영어"
                                )
                                st.rerun()

                    with col_t2:
                        if st.button("🇨🇳 중국어로 번역", key=f"trans_cn_{key}", use_container_width=True):
                            with st.spinner("중국어로 번역 중..."):
                                st.session_state[f"trans_cn_{key}"] = translate_email(
                                    st.session_state[f"email_content_{key}"], "중국어"
                                )
                                st.rerun()

                    if f"trans_en_{key}" in st.session_state:
                        st.text_area("🇺🇸 영어 번역", st.session_state[f"trans_en_{key}"], height=280, key=f"email_en_{key}")

                    if f"trans_cn_{key}" in st.session_state:
                        st.text_area("🇨🇳 중국어 번역", st.session_state[f"trans_cn_{key}"], height=280, key=f"email_cn_{key}")
