"""Pure-Python design validation and energy estimates (NOT a professional safety assessment)."""
from __future__ import annotations
import copy, io, math
from PIL import Image, ImageDraw, ImageFont

FACILITIES = {
    'stage': ('무대', '#8b80c7', (8.0, 3.0)),
    'seat': ('관객석', '#7cb6d5', (5.0, 3.0)),
    'aisle': ('이동 통로', '#d6e3ef', (2.0, 6.0)),
    'exit': ('출입구', '#93c3a2', (2.0, 1.2)),
    'led': ('고효율 조명', '#f6d78f', (1.0, 1.0)),
    'kinetic': ('발전 체험', '#e4ab71', (3.0, 2.5)),
    'recycle': ('분리배출', '#9dd1b0', (2.0, 1.5)),
    'rest': ('휴게 공간', '#c7b0dc', (3.0, 2.5)),
    'ramp': ('경사로(모형)', '#b8dab2', (2.0, 2.0)),
    'solar': ('태양광 발전 패널', '#aedce7', (3.0, 1.8)),
    'reusable': ('다회용 컵 반납함', '#aedcb6', (1.8, 1.2)),
    'refill': ('물 리필 스테이션', '#a8d6ec', (1.8, 1.5)),
    'sign': ('기후행동 안내판', '#c5e5a9', (1.5, 0.8)),
    'reuse': ('친환경 물품 대여', '#d8e4b7', (2.0, 1.6)),
    'cooling': ('고효율 냉난방', '#b2dbe5', (2.5, 1.7)),
}
OBSTACLE_TYPES = {'stage','seat','kinetic','recycle','rest','ramp'}

def default_design():
    entries = [('stage', 6, 0.7, 8, 3)]
    return {'room_w':20.0,'room_h':15.0,'people':200,'hours':4.0,
            'baseline': {'light_count':30,'light_w':100,'sound_kw':1.5,'hvac_kw':5.0,'hvac_duty':0.6,'hours':4.0},
            'proposal': {'light_count':15,'light_w':50,'sound_kw':1.5,'hvac_kw':5.0,'hvac_duty':0.6,'hours':4.0},
            'emission_factor':0.45,
            'planned_seats':0, 'recycle_service_capacity':0,
            'items':[{'id':i+1,'kind':k,'x':float(x),'y':float(y),'w':float(w),'h':float(h)} for i,(k,x,y,w,h) in enumerate(entries)]}

def overlaps(a,b):
    return a['x'] < b['x']+b['w'] and a['x']+a['w'] > b['x'] and a['y'] < b['y']+b['h'] and a['y']+a['h'] > b['y']

def facility_spec(d,kind):
    return (d.get('custom_facilities') or {}).get(kind, FACILITIES.get(kind,('시설','#b4ded0',(1.,1.))))

def rectangle_overlap(a,b):
    """Axis-aligned approximate overlap (metres squared); rotation not included."""
    dx=max(0.,min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x']))
    dy=max(0.,min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y']))
    return dx,dy,dx*dy

def meaningful_overlap(a,b,tolerance=0.25):
    dx,dy,area=rectangle_overlap(a,b)
    minimum=max(.001,min(a['w']*a['h'],b['w']*b['h']))
    return dx>tolerance and dy>tolerance and area>max(.25,minimum*.10)

def evaluate_design(d, has_survey_pdf=False, survey_facts=None):
    """Transparent teaching rubric; advisory, not certified safety or engineering review.

    Score 100 - documented deductions. The facility drawing is approximate;
    no deduction for small 0.25m overlaps or stage lighting overlays.
    """
    items=d.get('items',[])
    env={'led','kinetic','recycle','solar','reusable','refill','sign','reuse','cooling'}
    env_items=[x for x in items if x['kind'] in env or x['kind'].startswith('custom_')]
    deductions=[]
    def minus(category,points,reason,ids=None):
        deductions.append({'category':category,'points':points,'reason':reason,'ids':ids or []})
    types={x['kind'] for x in env_items}
    # Environment 40 points
    if not env_items:
        minus('환경성',20,'친환경 시설이나 환경 개선 방안이 배치도에 확인되지 않습니다.')
    if not types.intersection({'led','solar','cooling','kinetic'}):
        minus('환경성',8,'에너지 사용을 줄이거나 친환경 에너지를 활용하는 방안이 명확하지 않습니다.')
    if not types.intersection({'recycle','reusable','refill','reuse'}):
        minus('환경성',5,'일회용품·폐기물 감축 또는 자원 순환 실천 방안을 확인하기 어렵습니다.')
    # Feasibility 30 points
    # A floor plan cannot prove operating data, generation yield or survey availability.
    # Those are separate follow-up checks, never point deductions.
    checks=[]
    if not has_survey_pdf:
        checks.append('강당 조사 PDF가 등록되지 않았습니다. 실제 강당 조건과 비교하려면 자료를 등록해 보세요. (감점 없음)')
    if 'kinetic' in types:
        checks.append('발전 체험 장치의 예상 발전량과 운영 방식은 평면 설계도만으로 판단할 수 없습니다. 체험 효과와 전력 공급 효과를 구분해 확인하세요. (감점 없음)')
    if 'solar' in types:
        checks.append('태양광 패널의 설치 면적·방향·일조량 등은 도면 외 추가 자료를 통해 확인해야 합니다. (감점 없음)')
    if 'led' in types:
        checks.append('고효율 조명의 실제 전력 절감 효과와 조도는 별도 측정 자료로 확인해야 합니다. (감점 없음)')
    # environmental facility placement: don't penalize stage light overlap or light/light overlap
    overlap_seen=set()
    for a in env_items:
        if max(0.,-a['x'],-a['y'],a['x']+a['w']-d['room_w'],a['y']+a['h']-d['room_h'])>0.25:
            minus('실현 가능성',5,f'{facility_spec(d,a["kind"])[0]} #{a["id"]}이 강당 영역을 0.25m 넘게 벗어납니다.',[a['id']])
            break
    for i,a in enumerate(items):
        for b in items[i+1:]:
            if not meaningful_overlap(a,b):continue
            kinds={a['kind'],b['kind']}
            # Existing physical stage and LED lighting may overlap, valid by design.
            if 'led' in kinds and ('stage' in kinds or kinds=={'led'}):continue
            if kinds=={'seat','led'}:
                key='seat_led'; pts=12; cat='위험성'
                reason='조명이 관객석 영역과 상당히 겹칩니다. 관객 구역의 직접 설치·눈부심·전선 노출 가능성을 확인하고, 무대 위 조명 배치를 검토하세요.'
            elif a['kind'] in env and b['kind'] in env:
                key='env_overlap';pts=5;cat='실현 가능성'
                reason='서로 다른 친환경 시설이 크게 겹쳐 실제 배치에 어려움이 있을 수 있습니다.'
            else:continue
            if key not in overlap_seen:
                minus(cat,pts,reason,[a['id'],b['id']]);overlap_seen.add(key)
    # Compare survey audience with explicitly declared, verifiable proposal capacities.
    # Never assume seat block capacity or recycling-bin throughput from a diagram.
    facts=survey_facts if isinstance(survey_facts,dict) else {}
    survey_audience=facts.get('관객 수')
    if isinstance(survey_audience,int) and survey_audience>0:
        declared_seats=int(d.get('planned_seats') or 0)
        if declared_seats>0 and any(x['kind']=='seat' for x in items) and declared_seats<survey_audience:
            minus('실현 가능성',7,f'강당 조사 PDF에 관객 {survey_audience}명이 기록되어 있지만, 학생이 입력한 계획 좌석은 {declared_seats}석으로 {survey_audience-declared_seats}석 부족합니다.')
        elif declared_seats>0 and not any(x['kind']=='seat' for x in items):
            minus('실현 가능성',7,f'강당 조사 PDF의 관객 {survey_audience}명과 계획 좌석 {declared_seats}석이 입력되었으나 도면에 관객석 구역이 없습니다.')
        elif declared_seats==0:
            checks.append(f'강당 조사 PDF의 관객 수는 {survey_audience}명입니다. 도면의 관객석 블록은 좌석 수를 의미하지 않으므로, 실제 계획 좌석 수를 입력해 비교하세요. (감점 없음)')
        per_bin=int(d.get('recycle_service_capacity') or 0)
        recycle_count=sum(1 for x in items if x['kind']=='recycle')
        if per_bin>0 and recycle_count*per_bin<survey_audience:
            minus('실현 가능성',5,f'강당 조사 PDF의 관객 {survey_audience}명에 비해 분리배출 시설 {recycle_count}개 × 계획 이용 인원 {per_bin}명 = {recycle_count*per_bin}명으로 부족합니다. 이 계획값은 학생이 설정한 가정입니다.')
        elif per_bin==0:
            checks.append(f'관객 {survey_audience}명 대비 분리배출 시설 {recycle_count}개의 충분성은 1개당 계획 이용 인원이 없어서 판단할 수 없습니다. (감점 없음)')
    elif has_survey_pdf:
        checks.append('강당 조사 PDF에 명확한 관객 수 표기가 없거나 해당 수치를 추출하지 못했습니다. 인원 대비 시설 수는 감점하지 않습니다.')
    # caps per domain prevent negative scores, preserve explicit deduction trail
    caps={'환경성':40,'실현 가능성':30,'위험성':30}
    subtotals={k:v for k,v in caps.items()}
    applied=[]
    for dct in deductions:
        available=subtotals[dct['category']]
        take=min(dct['points'],available)
        if take:
            entry=dict(dct);entry['points']=take;applied.append(entry)
            subtotals[dct['category']]-=take
    score=sum(subtotals.values())
    good=[]
    if 'led' in types:good.append('고효율 조명을 설계에 반영했습니다.')
    if 'recycle' in types or 'reusable' in types:good.append('분리배출 또는 다회용품을 활용한 폐기물 감축 요소가 있습니다.')
    if 'solar' in types:good.append('태양광 발전을 검토할 수 있도록 배치했습니다. 발전 효과는 별도 검증이 필요합니다.')
    if 'kinetic' in types:good.append('관객 참여형 기후행동 체험 요소가 있습니다.')
    if not good:good.append('설계도를 바탕으로 친환경 개선 방향을 구체화할 수 있습니다.')
    return {'score':score,'categories':subtotals,'deductions':applied,'strengths':good,
            'checks':checks,'limitations':'교육용 잠정 평가입니다. 회전 시설의 정밀 충돌, 조도, 실제 발전량, 법정 안전기준을 검증하지 않습니다.'}

def validate(d):
    result=evaluate_design(d,False)
    issues=[{'level':'확인 필요','text':f'-{x["points"]}점: {x["reason"]}','ids':x['ids']} for x in result['deductions']]
    issues.append({'level':'안내','text':'배치도는 개략 설계입니다. 0.25m 이내 작은 배치 오차 및 무대와 조명의 겹침은 감점하지 않습니다.','ids':[]})
    return issues

def energy(c):
    hours=max(0.,float(c['hours']))
    light=max(0,int(c['light_count']))*max(0.,float(c['light_w']))/1000*hours
    sound=max(0.,float(c['sound_kw']))*hours
    hvac=max(0.,float(c['hvac_kw']))*min(1,max(0,float(c['hvac_duty'])))*hours
    return {'lighting':round(light,3),'sound':round(sound,3),'hvac':round(hvac,3),'total':round(light+sound+hvac,3)}

def simulate(d):
    before=energy(d['baseline']); after=energy(d['proposal']); f=float(d['emission_factor'])
    return {'before':before,'after':after,'kg_before':round(before['total']*f,3),
            'kg_after':round(after['total']*f,3),
            'delta_kwh':round(before['total']-after['total'],3),
            'reduction_pct':round((before['total']-after['total'])/before['total']*100,1) if before['total']>0 else None,
            'issues':validate(d)}

def rules_feedback(d):
    """Environmental-only offline guidance. No energy recalculation."""
    types={x['kind'] for x in d['items']}
    out=['[친환경 설계 검토] 배치도는 개념도이며, 작은 좌표 오차는 허용합니다.']
    if 'led' in types:out.append('고효율 LED 조명의 소비전력, 필요한 조명 수와 운영 시간의 근거를 확인하세요.')
    if 'kinetic' in types:out.append('관객 참여형 발전의 실제 생산 전력은 확인되지 않았습니다. 교육·체험 효과와 전력 대체 효과를 구분하세요.')
    if 'recycle' in types:out.append('분리배출 시설은 배치뿐 아니라 수거·운영 계획이 있어야 폐기물 감축에 기여할 수 있습니다.')
    if 'solar' in types:out.append('태양광 패널은 강당의 설치 가능 위치, 면적, 일조 조건을 확인해야 발전 효과를 추정할 수 있습니다.')
    if 'reusable' in types or 'refill' in types:out.append('다회용 컵·물 리필 시설은 일회용품 감축에 도움을 줄 수 있으나 실제 운영·세척·회수 계획이 필요합니다.')
    if False:out.append('스마트 절전 장치의 감축 효과는 기존 운전 방식, 센서 조건, 실제 사용 시간을 비교해 검토해야 합니다.')
    if not types.intersection({'led','kinetic','recycle','solar','smart','reusable','refill','upcycle','cooling'}):out.append('설계에 친환경 기술을 한 가지 이상 배치하고 그 적용 이유를 설명해 보세요.')
    out.extend(x['text'] for x in validate(d) if x['level'] in ('확인 필요','추가 검증 필요'))
    return '\n\n'.join(out)

FONT_PATHS = ['/usr/share/fonts/truetype/nanum/NanumGothic.ttf','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','C:/Windows/Fonts/malgun.ttf']
def font(sz):
    for p in FONT_PATHS:
        try: return ImageFont.truetype(p,sz)
        except OSError: pass
    return ImageFont.load_default()

def draw_pictogram(draw, kind, bounds, rotation=0):
    """Small dependency-free illustrative pictograms in PNG exports."""
    x1,y1,x2,y2=bounds
    cx=(x1+x2)/2; cy=(y1+y2)/2
    size=min((x2-x1)*.58,(y2-y1)*.58,52)
    if size < 10:return
    # Draw the glyph in a transparent square, rotate it with the facility.
    n=112; tile=Image.new('RGBA',(n,n),(0,0,0,0)); p=ImageDraw.Draw(tile)
    ink='#2b6570'; light='#ffffff'; green='#27865d'
    if kind=='stage':
        p.rectangle((16,30,96,75),fill='#7563ac',outline='#514080',width=4)
        p.line((20,25,92,25),fill=ink,width=6)
        for xx in (28,56,84):p.line((xx,25,xx,80),fill=light,width=2)
    elif kind=='seat':
        p.rounded_rectangle((26,19,86,65),radius=12,fill='#459bc8',outline=ink,width=4)
        p.rounded_rectangle((18,59,94,88),radius=9,fill='#93cae6',outline=ink,width=4)
        for xx in (31,81):p.line((xx,88,xx,100),fill=ink,width=5)
    elif kind=='led':
        p.ellipse((25,12,87,77),fill='#ffdf78',outline='#a8791d',width=4)
        p.rectangle((43,76,69,89),fill='#a8791d')
        p.line((43,93,69,93),fill='#a8791d',width=5)
        for a,b in [((56,3),(56,12)),((14,21),(21,28)),((98,21),(91,28)),((9,65),(20,65)),((103,65),(92,65))]:p.line((a,b),fill='#a8791d',width=4)
    elif kind=='kinetic':
        p.polygon([(19,74),(88,74),(98,93),(14,93)],fill='#a76e3e')
        p.polygon([(22,68),(36,41),(58,53),(71,68)],fill='#e5ae7a',outline=ink)
        p.polygon([(67,10),(49,54),(65,54),(51,82),(91,42),(72,42),(86,10)],fill='#f4cc53',outline='#b48215')
    elif kind=='recycle':
        p.arc((17,17,95,96),20,135,fill=green,width=7)
        p.arc((17,17,95,96),140,250,fill=green,width=7)
        p.arc((17,17,95,96),260,378,fill=green,width=7)
        p.polygon([(17,45),(16,66),(35,53)],fill=green)
        p.polygon([(77,17),(55,16),(70,35)],fill=green)
        p.polygon([(87,82),(94,60),(73,72)],fill=green)
    elif kind=='aisle':
        p.line((56,18,56,98),fill=ink,width=7)
        p.polygon([(56,8),(37,31),(75,31)],fill=ink);p.polygon([(56,104),(37,81),(75,81)],fill=ink)
    elif kind=='exit':
        p.rectangle((27,15,85,98),outline=green,width=7)
        p.line((39,58,76,58),fill=green,width=6)
        p.polygon([(89,58),(66,41),(66,75)],fill=green)
    elif kind=='rest':
        p.rounded_rectangle((23,30,90,81),radius=12,fill='#a891c8',outline='#654d9d',width=5)
        p.line((25,81,25,99),fill='#654d9d',width=5);p.line((88,81,88,99),fill='#654d9d',width=5)
    elif kind=='ramp':
        p.polygon([(18,90),(93,90),(93,24)],fill='#92c98a',outline=green)
        p.line((18,90,93,24),fill=light,width=5)
    elif kind.startswith('custom_'):
        p.ellipse((22,22,90,90),fill='#b7e4c8',outline=green,width=4)
        p.line((28,86,84,28),fill=green,width=5)
    else:
        p.ellipse((22,22,90,90),outline=ink,width=6)
    if rotation:tile=tile.rotate(-rotation,expand=False,resample=Image.Resampling.BICUBIC)
    tile=tile.resize((round(size),round(size)),Image.Resampling.LANCZOS)
    return tile,(round(cx-size/2),round(cy-size/2))

def draw_plan(d, image_width=1350):
    rw=max(1.,float(d['room_w']));rh=max(1.,float(d['room_h']))
    chart_w=image_width-110;chart_h=max(210,min(int(chart_w*rh/rw),1200))
    im=Image.new('RGB',(image_width,chart_h+120),'#f8fafc');dr=ImageDraw.Draw(im)
    left,top=55,65;sx=chart_w/rw;sy=chart_h/rh
    dr.rectangle((left,top,left+chart_w,top+chart_h),fill='#fff',outline='#7a98ab',width=4)
    for i in range(1,math.ceil(rw)):
        x=left+i*sx
        if x<left+chart_w:dr.line((x,top,x,top+chart_h),fill='#edf2f6',width=1)
    for j in range(1,math.ceil(rh)):
        y=top+j*sy
        if y<top+chart_h:dr.line((left,y,left+chart_w,y),fill='#edf2f6',width=1)
    dr.text((left,15),f'친환경 콘서트장 개념 설계도  {rw:g}m × {rh:g}m',fill='#192d45',font=font(25))
    for o in d['items']:
        name,color,_=facility_spec(d,o['kind'])
        cx=left+(o['x']+o['w']/2)*sx; cy=top+(o['y']+o['h']/2)*sy
        px_w=max(2,round(o['w']*sx));px_h=max(2,round(o['h']*sy))
        angle=float(o.get('rotation',0))%360
        layer=Image.new('RGBA',(px_w+16,px_h+16),(0,0,0,0));ld=ImageDraw.Draw(layer)
        ld.rounded_rectangle((8,8,8+px_w,8+px_h),radius=5,fill=color,outline='#50677e',width=2)
        glyph=draw_pictogram(ld,o['kind'],(8,8,8+px_w,8+px_h),0)
        if glyph:layer.alpha_composite(glyph[0],glyph[1])
        if px_w>60 and px_h>38:
            label=f'{name} #{o["id"]}'
            bb=ld.textbbox((0,0),label,font=font(14));tx=8+max(2,(px_w-(bb[2]-bb[0]))/2)
            ld.text((tx,8+px_h-21),label,fill='#26374c',font=font(14),stroke_width=1,stroke_fill='white')
        rotated=layer.rotate(-angle,expand=True,resample=Image.Resampling.BICUBIC)
        pos=(round(cx-rotated.width/2),round(cy-rotated.height/2))
        im.paste(rotated,pos,rotated)
    dr=ImageDraw.Draw(im)
    dr.text((left,top+chart_h+20),f'강당 가로 {rw:g}m / 세로 {rh:g}m',fill='#314a5e',font=font(20))
    dr.text((left,top+chart_h+20),'환경 2차시 | 친환경 설계 개념도 · 작은 위치 오차 허용 · 건축 안전성 검토 아님',fill='#516577',font=font(18))
    return im

def plan_bytes(d):
    buf=io.BytesIO();draw_plan(d).save(buf,format='PNG');return buf.getvalue()
