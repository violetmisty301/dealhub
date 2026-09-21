import json,re,time,statistics,urllib.request
from pathlib import Path
from html import unescape
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; OUT=DATA/'deals.json'; HIST=DATA/'history.json'
UA={'User-Agent':'Mozilla/5.0 DealHub-personal/2.0'}
def get(url):
 r=urllib.request.Request(url,headers=UA); return urllib.request.urlopen(r,timeout=20).read().decode('utf-8','ignore')
def clean(s): return re.sub(r'\s+',' ',unescape(re.sub('<[^>]+>',' ',s))).strip()
def norm(t):
 t=re.sub(r'^\[[^]]+\]\s*','',t.lower()); t=re.sub(r'[^0-9a-z가-힣]+',' ',t); return ' '.join(t.split())[:120]
def price_from(s):
 m=re.search(r'(?:₩|￦)?\s*([0-9][0-9,]{2,})\s*(?:원|krw)?',s,re.I)
 return int(m.group(1).replace(',','')) if m else None
def quasar():
 html=get('https://quasarzone.com/bbs/qb_saleinfo?device=pc&view=list')
 links=re.findall(r'href=["\']([^"\']*/bbs/qb_saleinfo/views/\d+[^"\']*)["\'][^>]*>(.*?)</a>',html,re.S|re.I)
 seen=set(); out=[]
 for href,txt in links:
  title=clean(txt)
  if not title or len(title)<4: continue
  url=href if href.startswith('http') else 'https://quasarzone.com'+href
  url=url.split('?')[0]
  if url in seen: continue
  seen.add(url)
  # list HTML often contains adjacent price/mall text; keep conservative parsing
  pos=html.find(href); ctx=clean(html[pos:pos+1800]) if pos>=0 else title
  p=price_from(ctx)
  mall=''
  m=re.match(r'\[([^]]+)\]',title); mall=m.group(1) if m else ''
  if p and p<100: p=None
  out.append({'source':'퀘이사존','title':title,'url':url,'price':p,'mall':mall,'category':'핫딜'})
  if len(out)>=50: break
 return out
# 뽐뿌는 페이지 구조/접근정책 변화에 대비해 실패 시 전체 작업을 중단하지 않음
def ppomppu():
 urls=['https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu','https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu4']
 out=[]
 for base in urls:
  try: html=get(base)
  except Exception: continue
  for href,txt in re.findall(r'href=["\']([^"\']*view\.php\?[^"\']+)["\'][^>]*>(.*?)</a>',html,re.S|re.I):
   title=clean(txt)
   if len(title)<5: continue
   url=href if href.startswith('http') else 'https://www.ppomppu.co.kr/zboard/'+href.lstrip('./')
   out.append({'source':'뽐뿌','title':title,'url':url,'price':price_from(title),'mall':'','category':'핫딜'})
   if len(out)>=40:return out
 return out
def main():
 DATA.mkdir(exist_ok=True); hist=json.loads(HIST.read_text('utf-8')) if HIST.exists() else {}
 deals=[]
 for fn in (quasar,ppomppu):
  try: deals+=fn()
  except Exception as e: print(fn.__name__,e)
 uniq={}
 for d in deals:
  k=d['source']+'|'+d['url']; uniq[k]=d
 deals=list(uniq.values())
 for d in deals:
  key=norm(d['title']); p=d.get('price'); arr=hist.get(key,[])
  if p:
   if not arr or arr[-1]!=p: arr=(arr+[p])[-100:]
   hist[key]=arr
  vals=arr or ([p] if p else [])
  d['history_count']=len(vals); d['low']=min(vals) if vals else None; d['avg']=round(statistics.mean(vals)) if vals else None
  if not p or len(vals)<=1:d['grade']='첫 관측'
  elif p<=min(vals):d['grade']='관측 역대가'
  elif p<=min(vals)*1.01:d['grade']='역대가 근접'
  elif p<=statistics.mean(vals)*.90:d['grade']='핫딜'
  else:d['grade']='보통'
 OUT.write_text(json.dumps({'updated_at':time.strftime('%Y-%m-%d %H:%M UTC',time.gmtime()),'deals':deals},ensure_ascii=False,indent=2),'utf-8'); HIST.write_text(json.dumps(hist,ensure_ascii=False,indent=2),'utf-8')
if __name__=='__main__': main()
