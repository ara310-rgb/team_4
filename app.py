import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
PRIMARY_KEY = os.getenv("UN_API_KEY")
SECONDARY_KEY = os.getenv("UN_SECOND_API_KEY")

# 페이지 설정
st.set_page_config(page_title="K-Trade Accelerator", layout="wide")

# UN 국가 코드 -> 국가명 매핑 (주요 국가)
COUNTRY_CODE_MAP = {
    4: "아프가니스탄", 8: "알바니아", 12: "알제리", 20: "안도라", 24: "앙골라",
    28: "앤티가 바부다", 32: "아르헨티나", 36: "호주", 40: "오스트리아", 31: "아제르바이잔",
    44: "바하마", 48: "바레인", 50: "방글라데시", 52: "바베이도스", 56: "벨기에",
    60: "버뮤다", 64: "부탄", 68: "볼리비아", 70: "보스니아", 72: "보츠와나",
    76: "브라질", 96: "브루나이", 100: "불가리아", 104: "미얀마", 108: "부룬디",
    116: "캄보디아", 120: "카메룬", 124: "캐나다", 132: "카보베르데", 140: "중앙아프리카",
    144: "스리랑카", 148: "차드", 152: "칠레", 156: "중국", 158: "대만",
    170: "콜롬비아", 174: "코모로", 178: "콩고", 180: "콩고민주공화국", 188: "코스타리카",
    191: "크로아티아", 192: "쿠바", 196: "키프로스", 203: "체코", 204: "베냉",
    208: "덴마크", 212: "도미니카", 214: "도미니카공화국", 218: "에콰도르", 222: "엘살바도르",
    226: "적도기니", 231: "에티오피아", 232: "에리트레아", 233: "에스토니아", 234: "페로제도",
    238: "포클랜드제도", 242: "피지", 246: "핀란드", 250: "프랑스", 254: "프랑스령기아나",
    258: "프랑스령폴리네시아", 262: "지부티", 266: "가봉", 268: "조지아", 270: "감비아",
    275: "팔레스타인", 276: "독일", 288: "가나", 292: "지브롤터", 296: "키리바시",
    300: "그리스", 304: "그린란드", 308: "그레나다", 312: "과들루프", 316: "괌",
    320: "과테말라", 324: "기니", 328: "가이아나", 332: "아이티", 336: "바티칸",
    340: "온두라스", 344: "홍콩", 348: "헝가리", 352: "아이슬란드", 356: "인도",
    360: "인도네시아", 364: "이란", 368: "이라크", 372: "아일랜드", 376: "이스라엘",
    380: "이탈리아", 384: "코트디부아르", 388: "자메이카", 392: "일본", 398: "카자흐스탄",
    400: "요르단", 404: "케냐", 408: "북한", 410: "한국", 414: "쿠웨이트",
    417: "키르기스스탄", 418: "라오스", 422: "레바논", 426: "레소토", 428: "라트비아",
    430: "라이베리아", 434: "리비아", 438: "리히텐슈타인", 440: "리투아니아", 442: "룩셈부르크",
    446: "마카오", 450: "마다가스카르", 454: "말라위", 458: "말레이시아", 462: "몰디브",
    466: "말리", 470: "몰타", 474: "마르티니크", 478: "모리타니", 480: "모리셔스",
    484: "멕시코", 492: "모나코", 496: "몽골", 498: "몰도바", 499: "몬테네그로",
    500: "몬세라트", 504: "모로코", 508: "모잠비크", 512: "오만", 516: "나미비아",
    520: "나우루", 524: "네팔", 528: "네덜란드", 531: "퀴라소", 533: "아루바",
    534: "신트마르턴", 540: "뉴칼레도니아", 548: "바누아투", 554: "뉴질랜드", 558: "니카라과",
    562: "니제르", 566: "나이지리아", 570: "니우에", 574: "노퍽섬", 578: "노르웨이",
    580: "북마리아나제도", 581: "미국령군소제도", 583: "미크로네시아", 584: "마셜제도", 585: "팔라우",
    586: "파키스탄", 591: "파나마", 598: "파푸아뉴기니", 600: "파라과이", 604: "페루",
    608: "필리핀", 612: "핏케언제도", 616: "폴란드", 620: "포르투갈", 624: "기니비사우",
    626: "동티모르", 630: "푸에르토리코", 634: "카타르", 638: "레위니옹", 642: "루마니아",
    643: "러시아", 646: "르완다", 652: "생바르텔레미", 654: "세인트헬레나", 659: "세인트키츠네비스",
    660: "앵귈라", 662: "세인트루시아", 663: "생마르탱", 666: "생피에르미클롱", 670: "세인트빈센트그레나딘",
    674: "산마리노", 678: "상투메프린시페", 682: "사우디아라비아", 686: "세네갈", 688: "세르비아",
    690: "세이셸", 694: "시에라리온", 702: "싱가포르", 703: "슬로바키아", 704: "베트남",
    705: "슬로베니아", 706: "소말리아", 710: "남아프리카공화국", 716: "짐바브웨", 724: "스페인",
    728: "남수단", 729: "수단", 732: "서사하라", 740: "수리남", 744: "스발바르얀마옌",
    748: "에스와티니", 752: "스웨덴", 756: "스위스", 760: "시리아", 762: "타지키스탄",
    764: "태국", 768: "토고", 772: "토켈라우", 776: "통가", 780: "트리니다드토바고",
    784: "아랍에미리트", 788: "튀니지", 792: "터키", 795: "투르크메니스탄", 796: "터크스케이커스제도",
    798: "투발루", 800: "우간다", 804: "우크라이나", 807: "북마케도니아", 818: "이집트",
    826: "영국", 831: "건지", 832: "저지", 833: "맨섬", 834: "탄자니아",
    840: "미국령버진아일랜드", 842: "미국", 850: "미국령버진아일랜드", 854: "부르키나파소", 858: "우루과이",
    860: "우즈베키스탄", 862: "베네수엘라", 876: "왈리스푸투나", 882: "사모아", 887: "예멘",
    894: "잠비아", 0: "전세계", 899: "기타"
}

def get_country_name(code):
    """국가 코드를 국가명으로 변환"""
    if pd.isna(code):
        return "알 수 없음"
    try:
        code = int(code)
        return COUNTRY_CODE_MAP.get(code, f"국가코드 {code}")
    except:
        return "알 수 없음"

def get_comtrade_data_with_params(hs_code, year, reporter_code):
    """UN Comtrade API 호출 함수"""
    url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
    
    params = {
        'reporterCode': reporter_code,
        'period': year,
        'cmdCode': hs_code,
        'flowCode': 'M',  # Import (수입)
        'typeCode': 'C'
    }

    api_keys = [PRIMARY_KEY]
    if SECONDARY_KEY:
        api_keys.append(SECONDARY_KEY)
    
    for idx, api_key in enumerate(api_keys):
        if not api_key:
            continue
            
        headers = {'Ocp-Apim-Subscription-Key': api_key}
        
        try:
            key_type = "Primary" if idx == 0 else "Secondary"
            st.write(f"📡 데이터 요청 중 ({key_type} Key)...")
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            st.write(f"📥 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                with st.expander("🔍 API 응답 미리보기", expanded=False):
                    st.write("**응답 키:**", list(data.keys()))
                    if 'data' in data and data['data']:
                        st.write(f"**데이터 건수:** {len(data['data'])}")
                        st.json(data['data'][0])
                
                if 'data' in data and data['data']:
                    df = pd.DataFrame(data['data'])
                    
                    # 국가명 추가 (reporterCode 또는 partnerCode 기준)
                    if 'partnerCode' in df.columns:
                        df['countryName'] = df['partnerCode'].apply(get_country_name)
                    elif 'reporterCode' in df.columns:
                        df['countryName'] = df['reporterCode'].apply(get_country_name)
                    else:
                        st.error("국가 코드 컬럼을 찾을 수 없습니다.")
                        return None
                    
                    st.success(f"✅ 데이터 로드 성공! ({len(df)}건)")
                    return df
                else:
                    st.warning("⚠️ API 응답은 성공했지만 해당 조건의 데이터가 없습니다.")
                    st.info("""
                    **시도해볼 사항:**
                    1. 다른 연도 선택 (2021, 2020)
                    2. '전세계'가 아닌 특정 국가 선택
                    3. flowCode를 'X'(수출)로 변경
                    """)
                    return None
            
            elif response.status_code in [401, 429]:
                if idx == 0 and SECONDARY_KEY:
                    st.warning(f"⚠️ {key_type} Key 문제. 보조 키로 전환...")
                    continue
                else:
                    st.error(f"❌ API 인증 실패: {response.status_code}")
                    st.code(response.text[:500])
                    return None
            else:
                st.error(f"❌ API 오류: {response.status_code}")
                with st.expander("에러 내용"):
                    st.code(response.text[:500])
                return None
                
        except Exception as e:
            st.error(f"❌ 오류: {e}")
            import traceback
            with st.expander("상세 오류"):
                st.code(traceback.format_exc())
            return None
    
    return None

def main():
    # 헤더
    st.title("🌐 K-Trade Accelerator: 시장조사")
    st.markdown("---")

    # 사이드바
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        if PRIMARY_KEY:
            st.success(f"Primary Key 로드됨: {PRIMARY_KEY[:5]}***")
        else:
            st.error("Primary Key 없음")
        
        if SECONDARY_KEY:
            st.success(f"Secondary Key 로드됨: {SECONDARY_KEY[:5]}***")
        
        st.info("제조사 해외사업부 전용 관제탑")
        
        st.markdown("---")
        st.markdown("### 📖 사용 안내")
        st.markdown("""
        1. HS Code 입력
        2. 조회 연도 선택
        3. Flow 타입 선택 (수입/수출)
        4. 분석 실행
        """)
        
        st.markdown("---")
        st.markdown("### 💡 HS Code 예시")
        st.markdown("""
        - **330499**: 화장품
        - **382499**: 화학제품
        - **851762**: 스마트폰
        - **870323**: 승용차
        """)

    # 메인 UI
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("🔍 품목 분석")
        hs_input = st.text_input(
            "HS Code 입력",
            value="382499",
            help="6자리 HS Code"
        )
        
        year = st.selectbox(
            "조회 연도",
            options=['2022', '2021', '2020', '2019'],
            help="최신 데이터는 2022년까지 안정적"
        )
        
        # Flow 타입 선택
        flow_options = {
            '수입 (Import)': 'M',
            '수출 (Export)': 'X',
            '재수출 (Re-Export)': 'RX',
            '재수입 (Re-Import)': 'RM'
        }
        flow_name = st.selectbox(
            "거래 유형",
            options=list(flow_options.keys()),
            help="수입: 해당 국가로 들어오는 물품 / 수출: 해당 국가에서 나가는 물품"
        )
        
        reporter_options = {
            '미국': '842',
            '중국': '156',
            '독일': '276',
            '일본': '392',
            '한국': '410',
            '영국': '826',
            '프랑스': '250',
            '이탈리아': '380',
            '인도': '356',
            '브라질': '76'
        }
        reporter_name = st.selectbox(
            "분석 대상 국가",
            options=list(reporter_options.keys()),
            help="이 국가의 무역 데이터를 분석합니다"
        )
        
        run_btn = st.button("🚀 글로벌 수요 분석 실행", type="primary")

    with col2:
        if run_btn:
            if not hs_input or len(hs_input) < 2:
                st.warning("⚠️ 유효한 HS Code를 입력해주세요.")
            else:
                reporter_code = reporter_options[reporter_name]
                flow_code = flow_options[flow_name]
                
                st.info(f"📋 **분석 조건**: HS Code {hs_input} | {year}년 | {reporter_name} {flow_name}")
                
                # API 호출 (임시로 flow를 하드코딩하지 않고 동적으로 처리)
                # 기존 함수 수정 필요
                df = get_comtrade_data_modified(hs_input, year, reporter_code, flow_code)
                
                if df is not None and len(df) > 0:
                    # World 제외
                    df_filtered = df[df['countryName'] != '전세계'].copy()
                    
                    if len(df_filtered) == 0:
                        st.warning("필터링 후 데이터가 없습니다.")
                    else:
                        # primaryValue 기준 정렬
                        value_col = 'primaryValue'
                        if value_col not in df_filtered.columns:
                            value_col = 'fobvalue' if 'fobvalue' in df_filtered.columns else 'cifvalue'
                        
                        top_10 = df_filtered.sort_values(by=value_col, ascending=False).head(10)

                        # 그래프
                        fig = px.bar(
                            top_10,
                            x='countryName',
                            y=value_col,
                            title=f"HS {hs_input} {reporter_name} {flow_name} 상위 10개국 ({year})",
                            labels={'countryName': '국가', value_col: '거래액 ($)'},
                            color=value_col,
                            color_continuous_scale='Blues',
                            text=value_col
                        )
                        fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                        fig.update_layout(
                            xaxis_tickangle=-45,
                            height=550,
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # 요약 통계
                        st.markdown("### 📊 요약 통계")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("총 거래 상대국", len(df_filtered))
                        with col_b:
                            st.metric("Top 1 국가", top_10.iloc[0]['countryName'])
                        with col_c:
                            total_value = df_filtered[value_col].sum()
                            st.metric("총 거래액", f"${total_value:,.0f}")

                        # 상세 테이블
                        with st.expander("📋 상세 데이터 보기"):
                            display_df = df_filtered[['countryName', value_col, 'period']].copy()
                            display_df.columns = ['국가', '거래액 ($)', '연도']
                            display_df = display_df.sort_values(by='거래액 ($)', ascending=False).reset_index(drop=True)
                            display_df['거래액 ($)'] = display_df['거래액 ($)'].apply(lambda x: f"${x:,.0f}")
                            st.dataframe(display_df, use_container_width=True, height=400)

def get_comtrade_data_modified(hs_code, year, reporter_code, flow_code):
    """Flow 파라미터를 받는 수정된 함수"""
    url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
    
    params = {
        'reporterCode': reporter_code,
        'period': year,
        'cmdCode': hs_code,
        'flowCode': flow_code,  # 동적으로 받음
        'typeCode': 'C'
    }

    api_keys = [PRIMARY_KEY]
    if SECONDARY_KEY:
        api_keys.append(SECONDARY_KEY)
    
    for idx, api_key in enumerate(api_keys):
        if not api_key:
            continue
            
        headers = {'Ocp-Apim-Subscription-Key': api_key}
        
        try:
            key_type = "Primary" if idx == 0 else "Secondary"
            st.write(f"📡 데이터 요청 중 ({key_type} Key)...")
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            st.write(f"📥 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                with st.expander("🔍 API 응답 미리보기", expanded=False):
                    st.write("**응답 키:**", list(data.keys()))
                    if 'data' in data and data['data']:
                        st.write(f"**데이터 건수:** {len(data['data'])}")
                        st.json(data['data'][0])
                
                if 'data' in data and data['data']:
                    df = pd.DataFrame(data['data'])
                    
                    # 국가명 매핑
                    if 'partnerCode' in df.columns:
                        df['countryName'] = df['partnerCode'].apply(get_country_name)
                    elif 'reporterCode' in df.columns:
                        df['countryName'] = df['reporterCode'].apply(get_country_name)
                    
                    st.success(f"✅ 데이터 로드 성공! ({len(df)}건)")
                    return df
                else:
                    st.warning("데이터가 없습니다. 다른 조건을 시도하세요.")
                    return None
            
            elif response.status_code in [401, 429]:
                if idx == 0 and SECONDARY_KEY:
                    st.warning(f"⚠️ {key_type} Key 문제. 보조 키로 전환...")
                    continue
                else:
                    st.error(f"❌ API 인증 실패: {response.status_code}")
                    return None
            else:
                st.error(f"❌ API 오류: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"❌ 오류: {e}")
            return None
    
    return None

if __name__ == "__main__":
    main()