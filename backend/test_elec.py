import requests
from lxml import html

url = "https://electronics.khu.ac.kr/electronics/notice/notice.do"

try:
    resp = requests.get(url, timeout=10)
    print(f"✅ 응답 코드: {resp.status_code}")
    
    tree = html.fromstring(resp.content)
    
    # 여러 선택자 시도
    rows1 = tree.xpath("//table[@class='board-list']//tbody/tr")
    rows2 = tree.xpath("//tbody/tr")
    rows3 = tree.xpath("//tr")
    
    print(f"📊 선택자 결과:")
    print(f"  board-list: {len(rows1)}개")
    print(f"  tbody/tr: {len(rows2)}개")
    print(f"  tr: {len(rows3)}개")
    
    if rows1:
        print(f"\n✅ 첫 번째 row HTML:")
        print(html.tostring(rows1[0], encoding='unicode')[:500])
    elif rows2:
        print(f"\n✅ tbody/tr 첫 번째:")
        print(html.tostring(rows2[0], encoding='unicode')[:500])
        
except Exception as e:
    print(f"❌ 에러: {e}")
    