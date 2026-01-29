import os
import requests
import pandas as pd
import time
import re
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()
exchange_key = os.getenv("EXCHANGE_RATE_KEY")

# 차단 방지를 위한 브라우저 헤더 설정
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.kita.net/board/totalTradeNews/totalTradeNewsList.do"
}

def get_exchange_rate():
    try:
        url = f"https://v6.exchangerate-api.com/v6/{exchange_key}/latest/USD"
        response = requests.get(url, timeout=5)
        return response.json()['conversion_rates']['KRW']
    except:
        return 1431.35 # 오류 시 이미지상의 기본값 표시

def get_full_trade_news(max_pages=5):
    data = []
    keywords = ["중국", "트럼프"] 
    session = requests.Session() # 세션 유지를 통해 상세 페이지 접근성 강화
    
    for page in range(1, max_pages + 1):
        list_url = f"https://www.kita.net/board/totalTradeNews/totalTradeNewsList.do?pageIndex={page}"
        try:
            response = session.get(list_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # [이미지 분석 결과] .board-list > li 구조 사용
            items = soup.select(".board-list > li")
            
            if not items:
                continue

            for item in items:
                title_tag = item.select_one(".subject a")
                if not title_tag: continue
                
                title = title_tag.text.strip()
                
                # 키워드 필터링
                if any(key in title for key in keywords):
                    # onclick 속성에서 no와 siteId 추출 (본문 수집의 핵심)
                    onclick = title_tag.attrs.get('onclick', '')
                    params = re.findall(r"'(.*?)'", onclick)
                    
                    if len(params) >= 2:
                        news_no, site_id = params[0], params[1]
                        link = f"https://www.kita.net/board/totalTradeNews/totalTradeNewsDetail.do?no={news_no}&siteId={site_id}"
                        
                        # 상세 페이지 본문 크롤링
                        detail_res = session.get(link, headers=headers, timeout=10)
                        detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                        
                        # [이미지 분석 결과] 본문 영역 추출
                        content_tag = detail_soup.select_one(".boardView_cont")
                        if not content_tag:
                            content_tag = detail_soup.select_one(".view_cont")
                            
                        content = content_tag.get_text(separator="\n").strip() if content_tag else "본문 내용을 불러올 수 없습니다."
                        
                        date_tag = item.select_one(".info")
                        date = date_tag.text.strip() if date_tag else "날짜없음"
                        
                        # KeyError 방지를 위해 딕셔너리 키 이름 통일
                        data.append({
                            "날짜": date, 
                            "제목": title, 
                            "본문": content, 
                            "link": link 
                        })
                        time.sleep(0.4)
        except Exception as e:
            print(f"오류 발생: {e}")
            continue
            
    return data

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="중국/트럼프 무역 모니터링", layout="wide")
st.title("🚢 핵심 무역 이슈 실시간 대시보드")

# 환율 표시
krw_rate = get_exchange_rate()
st.metric(label="현재 원/달러 환율 (USD/KRW)", value=f"{krw_rate:,.2f} 원")

st.divider()

# 검색 페이지 설정
target_pages = st.sidebar.number_input("검색할 페이지 수", 1, 10, 5)

if st.button("이슈 수집 및 본문 분석 시작"):
    with st.spinner('KITA 데이터를 분석 중입니다...'):
        news_results = get_full_trade_news(max_pages=target_pages)
        
        if news_results:
            st.success(f"✅ 총 {len(news_results)}건의 핵심 이슈를 발견했습니다!")
            
            # [핵심 기능] 제목 클릭 시 본문 내용 펼치기
            for news in news_results:
                with st.expander(f"[{news['날짜']}] {news['제목']}"):
                    st.write(f"**🔗 원문 링크:** [바로가기]({news['link']})")
                    st.markdown("---")
                    st.write(news['본문'])
            
            # 엑셀 저장 및 다운로드
            df = pd.DataFrame(news_results)
            try:
                df.to_excel("무역_핵심이슈_리포트.xlsx", index=False)
                st.info("📂 '무역_핵심이슈_리포트.xlsx' 파일로 저장되었습니다.")
            except PermissionError:
                st.error("⚠️ 엑셀 파일이 열려있습니다. 파일을 닫고 다시 실행해주세요.")
        else:
            st.warning("조건에 맞는 뉴스가 없습니다.")