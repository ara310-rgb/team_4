import streamlit as st
import os
import time
import random
from dotenv import load_dotenv
from openai import OpenAI
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Global Market Insight AI", 
    page_icon="🌏",
    layout="wide"
)

# --- 스타일 커스텀 ---
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stButton>button {
        width: 100%;
        background-color: #FF9900;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
    }
    .stButton>button:hover { background-color: #e68a00; color: white; }
    /* 탭 폰트 사이즈 키우기 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 설정 및 초기화 ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPEN_API_KEY")

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ Market Insight AI")
    st.markdown("---")
    if OPENAI_API_KEY:
        st.success("✅ 시스템 연결 정상")
    else:
        st.error("❌ API Key 확인 필요 (.env)")
        st.stop()

# --- 헤더 섹션 ---
st.title("🌏 글로벌 SEO & 아마존 리스팅 생성기")
st.markdown("구글 트렌드 데이터를 **3단계 심층 분석(1년/3개월/1개월)**하여 데이터를 반드시 찾아냅니다.")
st.divider()

# --- 입력 폼 ---
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        input_type = st.radio("입력 방식", ["제품 키워드", "HS Code"])
    with col2:
        user_input = st.text_input("제품 정보 입력", placeholder="예: Wireless Keyboard, 8518")
    with col3:
        target_country = st.text_input("타겟 국가 (코드)", placeholder="US, GB, JP").upper()

    # 영국 코드 보정
    if target_country == "UK":
        target_country = "GB"

    analyze_btn = st.button("🚀 시장 분석 및 마케팅 문구 생성")

# --- 유틸리티 함수: 국가 코드 -> 언어 변환 ---
def get_language_name(country_code):
    lang_map = {
        'US': 'English', 'GB': 'English', 'CA': 'English', 'AU': 'English',
        'JP': 'Japanese', 'CN': 'Chinese', 'VN': 'Vietnamese',
        'FR': 'French', 'DE': 'German', 'ES': 'Spanish', 'KR': 'Korean'
    }
    return lang_map.get(country_code, f"the official language of {country_code}")

# --- 핵심 로직 함수들 ---

def get_seed_keyword(client, user_input, input_type, target_country_code):
    """1차 시드 키워드 생성"""
    lang_name = get_language_name(target_country_code)
    prompt = f"""
    Task: Identify the product from '{user_input}' (Type: {input_type}).
    Target: {target_country_code} (Language: {lang_name}).
    
    Action:
    1. Translate/Localize the product name into the ONE most common search term in **{lang_name}**.
    2. Provide the English translation.
    
    Output: NativeKeyword, EnglishKeyword
    Example: Smartphone, 스마트폰
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        clean = content.replace('*', '').replace('"', '').replace("'", "")
        if "," in clean:
            return [x.strip() for x in clean.split(',', 1)]
        return clean.strip(), clean.strip()
    except:
        return None, None

def get_alternative_keywords(client, original_keyword, target_country_code):
    """데이터가 없을 때 대체 키워드 추천 (Smart Fallback)"""
    lang_name = get_language_name(target_country_code)
    prompt = f"""
    The keyword '{original_keyword}' has NO search volume in Google Trends for {target_country_code}.
    
    Task: Provide 3 alternative, highly popular search terms for this same product in **{lang_name}**.
    Think of synonyms, broader categories, or related specific terms people actually type.
    
    Output format: Keyword1, Keyword2, Keyword3
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        return [k.strip() for k in content.split(',')]
    except:
        return []

def get_trends_data_with_retry(seed_keyword, geo_code):
    """
    [핵심 수정] PyTrends 요청 - 3단 기어 전략 (12개월 -> 3개월 -> 1개월)
    """
    pytrends = TrendReq(hl='en-US', tz=360) 
    
    # 3가지 기간 전략: 1년(넓게), 3개월(중간), 1개월(좁게/민감하게)
    timeframes = ['today 12-m', 'today 3-m', 'today 1-m']
    
    for tf in timeframes:
        try:
            # st.write(f"DEBUG: '{seed_keyword}' 검색 시도 (기간: {tf})") # 디버깅용 (필요시 주석 해제)
            
            # gprop='' 제거, cat 제거하여 검색 범위 최대화
            pytrends.build_payload([seed_keyword], timeframe=tf, geo=geo_code)
            
            related = pytrends.related_queries()
            
            # 데이터 유효성 검사
            if related and seed_keyword in related:
                top_df = related[seed_keyword]['top']
                if top_df is not None and not top_df.empty:
                    # 데이터가 있으면 즉시 반환
                    return top_df.head(20)['query'].tolist()
                    
            # 데이터가 없으면 잠시 대기 후 다음 기간(timeframe)으로 넘어감
            time.sleep(1) 
            
        except Exception as e:
            # 429(Too Many Requests)일 경우 조금 더 길게 대기
            if "429" in str(e):
                time.sleep(3)
            continue
            
    return [] # 모든 기간을 다 돌았는데도 없으면 빈 리스트 반환

def filter_seo_keywords(client, raw_keywords, product_name, country):
    if not raw_keywords: return "데이터 없음"
    prompt = f"""
    Role: Cross-Border SEO Expert.
    Product: {product_name}, Target: {country}.
    Raw Keywords: {raw_keywords}
    
    Task: Select top 5 high-intent keywords for online sales.
    Exclude: "Near me", "Location", "Store", generic Brand names.
    
    Output: Keyword1, Keyword2, Keyword3, Keyword4, Keyword5
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except:
        return ""

def generate_amazon_bullets(client, product_name, keywords, country):
    lang_name = get_language_name(country)
    
    prompt = f"""
    Role: Amazon Copywriter for the **{country}** market.
    Product: {product_name}
    Keywords: {keywords}
    
    CRITICAL INSTRUCTION:
    Write 5 persuasive Amazon Bullet Points in **{lang_name}**.
    (If Target is GB/US -> English. If JP -> Japanese. If KR -> Korean).
    
    Structure:
    - [Benefit Header] Description using keywords.
    
    Output Example (if English):
    - 📌 ULTIMATE WIRELESS FREEDOM - Experience...
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "문구 생성 실패"

# --- 메인 실행 로직 ---
if analyze_btn:
    if not user_input or not target_country:
        st.warning("⚠️ 제품명과 국가 코드를 모두 입력해주세요.")
    else:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 스피너 메시지 단순화
        with st.spinner("🤖 AI가 구글 트렌드 빅데이터를 분석 중입니다..."):
            
            # 1. 초기 키워드 선정
            native_kw, english_kw = get_seed_keyword(client, user_input, input_type, target_country)
            
            # 영국 타겟인데 한글이 나오면 강제 수정 (혹시 모를 오류 방지)
            if target_country == "GB" and "키보드" in native_kw: 
                native_kw = english_kw # 강제로 영어 사용
            
            final_search_kw = native_kw
            raw_keywords = []
            
            if native_kw:
                # 2. 첫 번째 검색 시도 (3단 기어 전략 적용)
                raw_keywords = get_trends_data_with_retry(native_kw, target_country)
                
                # 🚨 여전히 데이터 없음 -> 대체 키워드 로직 가동
                if not raw_keywords:
                    st.toast(f"⚠️ '{native_kw}' 데이터 부족. 심층 탐색 모드로 전환합니다.", icon="🔄")
                    
                    alternatives = get_alternative_keywords(client, native_kw, target_country)
                    
                    for alt_kw in alternatives:
                        # st.caption(f"🔄 대체 키워드 시도 중: {alt_kw}...") # UI를 깔끔하게 하기 위해 숨김
                        temp_data = get_trends_data_with_retry(alt_kw, target_country)
                        if temp_data:
                            raw_keywords = temp_data
                            final_search_kw = alt_kw 
                            st.success(f"✅ '{final_search_kw}' 키워드로 데이터 확보 성공!")
                            break
                    
                    if not raw_keywords:
                        st.error("❌ 구글 트렌드 API가 일시적으로 요청을 차단했거나, 검색량이 매우 적습니다. 잠시 후 다시 시도해주세요.")
                        st.stop()

                # 3. SEO 및 카피라이팅
                selected_keywords = filter_seo_keywords(client, raw_keywords, english_kw, target_country)
                amazon_copy = generate_amazon_bullets(client, english_kw, selected_keywords, target_country)
                
                # --- 결과 출력 ---
                st.markdown("<br>", unsafe_allow_html=True)
                
                tab1, tab2, tab3 = st.tabs(["📊 SEO 핵심 키워드", "📝 아마존 리스팅 (현지어)", "🔍 원본 데이터"])
                
                with tab1:
                    st.markdown(f"### 🎯 [{target_country}] TOP 5 키워드")
                    st.success(f"분석 기준 키워드: **{final_search_kw}**")
                    st.info(selected_keywords)
                    st.markdown(f"> **Tip:** 위 키워드들을 아마존 Backend Keywords(Search Terms) 란에 입력하세요.")
                    
                with tab2:
                    st.markdown(f"### 🛒 아마존 블랙보드 ({get_language_name(target_country)})")
                    st.markdown(amazon_copy)
                    
                with tab3:
                    st.markdown("### 📈 구글 트렌드 연관 검색어")
                    st.dataframe({"Rank": range(1, len(raw_keywords)+1), "Keyword": raw_keywords}, use_container_width=True)

            else:
                st.error("제품명을 식별할 수 없습니다.")