#!/usr/bin/env python3
"""Rebuild content.js from bundled source/*.md or a supplied ZIP path."""
from pathlib import Path
from zipfile import ZipFile
import json, re, shutil, html, collections, sys
SRC = Path(__file__).resolve().parents[1]
ZIP = Path(sys.argv[1]) if len(sys.argv)>1 else SRC/'Step02_All_Tracks_60.zip'

def segment(md, start, end=None):
    a=re.search(start,md,re.M)
    if not a:return ''
    s=md[a.end():]
    if end:
        z=re.search(end,s,re.M)
        if z:s=s[:z.start()]
    return s.strip()

def rows(body):
    res=[]
    for line in body.splitlines():
        if not line.startswith('|'):continue
        cells=[i.strip() for i in line.strip().strip('|').split('|')]
        if not cells or all(re.match(r'^:?-{2,}:?$',c) for c in cells):continue
        res.append(cells)
    return res

def parse_lesson(fn,md):
    m=re.match(r'^(U?\d\d)_',fn)
    id=m.group(1)
    title=next((x.split('.',1)[1].strip() for x in md.splitlines() if x.startswith('# ') and '.' in x),fn)
    subtitle=next((x[4:].strip() for x in md.splitlines() if x.startswith('### ')),'')
    head=segment(md,r'^# .*$' ,r'^---$')
    meta={r[0]:r[1] for r in rows(head) if len(r)==2 and r[0] not in ['항목']}
    original=segment(md,r'^## 0\. 원문.*$',r'^---$')
    original_paragraphs=[re.sub(r'^>\s?', '',x).strip() for x in original.splitlines() if x.startswith('> ') and len(x.strip())>2]
    # Some long-form essays contain blockquotes prefaced by >, plus occasional data tables in other sections.
    chunk_seg=segment(md,r'^## 1회차.*$',r'^---$')
    chunks=[]
    pindex=0
    for line in chunk_seg.splitlines():
        if re.match(r'^### 문단 \d+',line):
            pindex=int(re.search(r'\d+',line).group());chunks.append({'paragraph':pindex,'rows':[]})
        elif line.startswith('|'):
            cells=[i.strip() for i in line.strip().strip('|').split('|')]
            if len(cells)>=3 and cells[0] not in ['영어 청크','---','-'] and not re.match(r'^:?-{2,}:?$',cells[0]):
                if not chunks:chunks.append({'paragraph':1,'rows':[]})
                chunks[-1]['rows'].append({'en':cells[0], 'ko':cells[1], 'note':cells[2]})
    sentence_seg=segment(md,r'^## 2회차.*$',r'^---$')
    sentences=[];para=0
    lines=sentence_seg.splitlines()
    for i,line in enumerate(lines):
        p=re.match(r'^### 문단 (\d+)',line)
        if p:para=int(p.group(1))
        match=re.match(r'^\*\*([①-㊿])\s*(.*?)\*\*\s*$',line)
        if match:
            following=[x.strip() for x in lines[i+1:i+4] if x.strip() and not x.startswith('**') and not x.startswith('#') and not x.startswith('---')]
            ko=next((x for x in following if not x.startswith('어휘:')), '')
            note=next((x.replace('어휘:','',1).strip() for x in following if x.startswith('어휘:')), '')
            sentences.append({'en':match.group(2), 'ko':ko, 'note':note,'paragraph':para})
    if len(sentences)<15: raise ValueError(f'Failed parsing sentences: {fn}: {len(sentences)}')
    lex=segment(md,r'^## 핵심 어휘 정리.*$',r'^---$')
    vocabulary=[]
    for row in rows(lex):
        if len(row)<4 or row[0] in ('어휘','---'):continue
        for a,b in [(row[0],row[1]),(row[2],row[3])]:
            if a and b and not re.match('^-+$',a):vocabulary.append({'en':a,'ko':b})
    if not vocabulary: raise ValueError(f'No vocab {fn}')
    return {'id':id,'number':int(id[-2:]),'track':'university' if id.startswith('U') else 'core',
            'title':title,'subtitle':subtitle,'meta':meta,'original':original_paragraphs,
            'chunks':chunks,'sentences':sentences,'vocabulary':vocabulary,'source':md,
            'wordCount':len(re.findall(r"[a-zA-Z]+(?:['’-][a-zA-Z]+)*",' '.join(original_paragraphs))),
            'sourceFilename':fn}

def main():
    data=[];indexes={}
    if ZIP.is_file():
        with ZipFile(ZIP) as z:
            documents={f:z.read(f).decode('utf-8-sig') for f in z.namelist() if f.endswith('.md')}
    else:
        documents={f.name:f.read_text(encoding='utf-8-sig') for f in (SRC/'source').glob('*.md')}
    for f,md in documents.items():
        if f in ('00_Series_Index.md','00U_University_Track_Index.md'):
            indexes[f]=md
        if not re.match(r'^(?:[0-9]{2}|U[0-9]{2})_',f) or f.startswith('00'):continue
        data.append(parse_lesson(f,md))
        (SRC/'source'/f).write_text(md,encoding='utf-8')
    data.sort(key=lambda x:(x['track']!='core',x['number']))
    assert len(data)==60, len(data)
    assert sum(len(l['sentences']) for l in data)==1759
    for f,v in indexes.items():(SRC/'source'/f).write_text(v,encoding='utf-8')
    blob={'lessons':data,'indexes':indexes,'stats':{
        'lessons':len(data),'sentences':sum(len(x['sentences']) for x in data),
        'chunks':sum(sum(len(p['rows']) for p in x['chunks']) for x in data),
        'words':sum(x['wordCount'] for x in data),
        'vocabEntries':sum(len(x['vocabulary']) for x in data),
        'references':sum('## 참고 문헌' in x['source'] for x in data)
    }}
    (SRC/'content.js').write_text('/* Generated from the original 60 Markdown lessons; all originals are kept in source/. */\nwindow.STUDIO_DATA = '+json.dumps(blob,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    print('STATS',blob['stats']);print('size',round((SRC/'content.js').stat().st_size/1024/1024,2),'MiB')
    print('lesson check:',[(x['id'],len(x['original']),len(x['chunks']),len(x['sentences']),len(x['vocabulary'])) for x in data[:3]])
if __name__=='__main__': main()
