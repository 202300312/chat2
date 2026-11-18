"""Per-team lesson PDF extraction and drawing export. No OCR."""
from __future__ import annotations
import io, sqlite3, json, hashlib, math, re
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from core import database as db
from core.engine import plan_bytes

MAX_BYTES=8*1024*1024

def init():
    with db.connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS survey_pdf (
            team_id INTEGER PRIMARY KEY, filename TEXT NOT NULL,
            extracted TEXT NOT NULL, chars INTEGER NOT NULL
        )""")

def save_document(team_id:int,filename:str,raw:bytes):
    if not raw.startswith(b'%PDF-') or not filename.lower().endswith('.pdf'):
        raise ValueError('PDF 파일만 업로드할 수 있습니다.')
    if len(raw)>MAX_BYTES:raise ValueError('PDF 용량은 8MB 이하로 제한됩니다.')
    try:
        r=PdfReader(io.BytesIO(raw),strict=False)
        if r.is_encrypted:raise ValueError('비밀번호가 걸린 PDF는 지원하지 않습니다.')
        if len(r.pages)>40:raise ValueError('PDF는 40페이지 이하여야 합니다.')
        sections=[]
        for i,page in enumerate(r.pages):
            sections.append(f'[페이지 {i+1}]\n'+(page.extract_text() or ''))
        content='\n'.join(sections).strip()[:24000]
    except ValueError:raise
    except Exception:raise ValueError('PDF 텍스트를 읽지 못했습니다. 파일 형식을 확인하세요.')
    if not content:raise ValueError('문서에서 텍스트가 추출되지 않았습니다. 스캔 이미지 PDF는 지원하지 않습니다.')
    init()
    with db.connect() as c:
        c.execute("""INSERT INTO survey_pdf(team_id,filename,extracted,chars) VALUES(?,?,?,?)
            ON CONFLICT(team_id) DO UPDATE SET filename=excluded.filename,
            extracted=excluded.extracted,chars=excluded.chars""",
            (team_id,filename[:150],content,len(content)))
    return {'filename':filename,'chars':len(content)}

def get_document(team_id):
    init()
    with db.connect() as c:
        row=c.execute('SELECT filename,chars FROM survey_pdf WHERE team_id=?',(team_id,)).fetchone()
        return dict(row) if row else None

def delete_document(team_id):
    init()
    with db.connect() as c:
        c.execute('DELETE FROM survey_pdf WHERE team_id=?',(team_id,))

def get_combined_context(team_id):
    init()
    with db.connect() as c:
        row=c.execute('SELECT filename,extracted FROM survey_pdf WHERE team_id=?',(team_id,)).fetchone()
    if not row:return ''
    # Short reference window for small local LLM; visible in UI as a limitation.
    return f'강당 조사 PDF ({row["filename"]})\n{row["extracted"][:2400]}'

def design_to_pdf(d,title='콘서트장 설계도'):
    """PDF file with image diagram and page title. Canvas dimensions follow drawing aspect ratio."""
    from PIL import Image
    png=plan_bytes(d)
    im=Image.open(io.BytesIO(png))
    width,height=im.size
    page_w,page_h=595.28,841.89
    bio=io.BytesIO();c=canvas.Canvas(bio,pagesize=(page_w,page_h))
    fonts=[('Malgun','C:/Windows/Fonts/malgun.ttf'),('Nanum','/usr/share/fonts/truetype/nanum/NanumGothic.ttf'),('Nanum2','/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf')]
    font_name='Helvetica'
    for name,path in fonts:
        try:pdfmetrics.registerFont(TTFont(name,path));font_name=name;break
        except Exception:pass
    c.setFont(font_name,15);c.setFillColorRGB(.16,.36,.20)
    c.drawString(38,page_h-48,'Eco Concert Design' if font_name=='Helvetica' else str(title)[:40])
    usable_w=page_w-70; usable_h=page_h-115
    scale=min(usable_w/width,usable_h/height)
    dw,dh=width*scale,height*scale
    c.drawImage(ImageReader(io.BytesIO(png)),(page_w-dw)/2,page_h-75-dh,width=dw,height=dh,preserveAspectRatio=True,mask='auto')
    c.setFont(font_name,9)
    c.setFillColorRGB(.3,.4,.34)
    foot='Concept floor plan - not a construction drawing' if font_name=='Helvetica' else '환경 수업용 개념 설계도 · 실제 건축 도면 아님'
    c.drawString(38,30,foot)
    # Embed machine-readable design snapshot. PDF is still viewable as an ordinary document.
    from core.engine import default_design
    safe={k:d[k] for k in ('room_w','room_h','people','planned_seats','recycle_service_capacity','items') if k in d}
    safe['custom_facilities']=d.get('custom_facilities',{})
    encoded=json.dumps(safe,ensure_ascii=False,separators=(',',':'))
    digest=hashlib.sha256(encoded.encode('utf-8')).hexdigest()
    c.setAuthor('Eco Concert Designer v12')
    c.setSubject('School concert hall educational design')
    c.setKeywords('eco-design')
    c.save()
    from pypdf import PdfWriter
    writer=PdfWriter();writer.append(io.BytesIO(bio.getvalue()))
    writer.add_metadata({'/EcoDesignFormat':'v12','/EcoDesignJSON':encoded,'/EcoDesignSHA256':digest})
    output=io.BytesIO();writer.write(output);return output.getvalue()


def design_from_pdf(raw:bytes):
    """Recover only an exported design PDF; do not hallucinate geometry from screenshots."""
    from core.engine import FACILITIES
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES or not raw.startswith(b'%PDF-'):
        raise ValueError('8MB 이하의 정상적인 PDF를 선택해 주세요.')
    try:
        reader=PdfReader(io.BytesIO(raw),strict=False)
        md=reader.metadata or {}
        if md.get('/EcoDesignFormat')!='v12':
            raise ValueError('다른 PDF 형식입니다. 「설계도 PDF 내려받기」로 저장한 PDF를 업로드해 주세요. 이미지 형태의 도면은 자동으로 치수를 읽지 않습니다.')
        raw_json=str(md.get('/EcoDesignJSON') or '')
        sig=str(md.get('/EcoDesignSHA256') or '')
        if len(raw_json)>180000 or hashlib.sha256(raw_json.encode('utf-8')).hexdigest()!=sig:
            raise ValueError('설계도 데이터 확인에 실패했습니다. PDF를 다시 저장해 주세요.')
        d=json.loads(raw_json)
        if not isinstance(d,dict) or not 5<=float(d['room_w'])<=60 or not 5<=float(d['room_h'])<=50:
            raise ValueError('강당 치수 정보가 올바르지 않습니다.')
        items=d.get('items')
        if not isinstance(items,list) or len(items)>500:raise ValueError('시설 수가 허용 범위를 벗어났습니다.')
        for i in items:
            if not isinstance(i,dict) or not isinstance(i.get('kind'),str):raise ValueError('시설 정보가 올바르지 않습니다.')
            vals=[float(i[k]) for k in ('x','y','w','h')]
            if not all(math.isfinite(v) for v in vals) or not .20<=vals[2]<=60 or not .20<=vals[3]<=50:raise ValueError('시설 좌표나 크기를 확인해 주세요.')
        custom=d.get('custom_facilities',{})
        if not isinstance(custom,dict) or len(custom)>100:raise ValueError('사용자 시설 정보가 올바르지 않습니다.')
        d['people']=int(d.get('people',0))
        for k in ('planned_seats','recycle_service_capacity'):
            d[k]=min(5000,max(0,int(d.get(k,0) or 0)))
        return d
    except ValueError:raise
    except Exception as exc:raise ValueError('설계도 PDF 정보를 읽을 수 없습니다. 웹앱에서 PDF를 다시 내려받아 주세요.') from exc


def extract_survey_facts(text:str):
    """Only explicitly labelled audience counts, not unsourced inferences."""
    t=(text or '').replace(',', '').replace('：', ':')
    # The PDF may contain other numbers (stage widths, electricity, attendance
    # statistics from past years). We require a nearby exact audience label.
    matches=[]
    for regex in (
        r'(?:예상\s*)?관객\s*수\s*[:：=]?\s*(\d{1,5})\s*명',
        r'관객\s*[:：=]\s*(\d{1,5})\s*명',
        r'(?:예상\s*)?참여\s*인원\s*[:：=]?\s*(\d{1,5})\s*명',
    ):
        matches.extend(int(m.group(1)) for m in re.finditer(regex,t))
        if matches:break
    if len(set(matches))==1 and 1<=matches[0]<=5000:
        return {'관객 수':matches[0]}
    return {}


def get_survey_facts(team_id):
    init()
    with db.connect() as c:
        row=c.execute('SELECT extracted FROM survey_pdf WHERE team_id=?',(team_id,)).fetchone()
    return extract_survey_facts(row['extracted']) if row else {}
