#!/usr/bin/env python3
"""Build a CV .docx in YOUR OWN format.

Clones an existing .docx (fonts, colours, page setup, numbering, styles) and writes
fresh content into it, so the output matches your real CV **by construction** rather
than by imitation. This is the whole trick: it never designs anything.

Point CV_TEMPLATE at any .docx whose look you want to keep — your current CV works
best. Colours and type sizes below are read from that file's conventions; adjust the
constants if yours differ.

Usage:
    CV_TEMPLATE=~/Documents/my-cv.docx python3 build_cv.py content.json out.docx

Content JSON schema:
{
  "name": "YOUR NAME",
  "contact": ["City, Country", "+44 ...", "email", "linkedin", "site"],
  "sections": [
    {"heading": "PROFILE", "body": "one paragraph"},
    {"heading": "EXPERIENCE", "entries": [
       {"org": "Company", "role": "Job Title",
        "dates": "May 2025 – Aug 2025",
        "meta": ["One-line company descriptor", "City, Country"],
        "bullets": ["Accomplished X, measured by Y, by doing Z.", "..."]}
    ]},
    {"heading": "SKILLS", "skills": [["Category", "A • B • C"]]}
  ]
}
"""
import json, re, shutil, sys, zipfile, os
from xml.sax.saxutils import escape

TEMPLATE = os.path.expanduser(
    os.environ.get("CV_TEMPLATE", "~/Documents/my-cv.docx")
)
if not os.path.exists(TEMPLATE):
    sys.exit(
        f"CV template not found: {TEMPLATE}\n"
        "Set CV_TEMPLATE to an existing .docx whose formatting you want to reuse:\n"
        "  CV_TEMPLATE=~/Documents/my-cv.docx python3 build_cv.py content.json out.docx"
    )

NAVY, SLATE, BODY = "1A1A2E", "4A4A6A", "2D2D2D"
TAB = 9026  # right-aligned tab stop: dates flush to right margin

def rpr(sz, bold=False, italic=False, color=BODY):
    p = f'<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>'
    if bold: p += '<w:b/>'
    if italic: p += '<w:i/>'
    p += f'<w:color w:val="{color}"/><w:sz w:val="{int(sz*2)}"/><w:szCs w:val="{int(sz*2)}"/></w:rPr>'
    return p

def run(text, sz, bold=False, italic=False, color=BODY):
    return f'<w:r>{rpr(sz,bold,italic,color)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'

def para(runs, before=0, after=0, jc=None, border=False, tabs=False):
    p = '<w:p><w:pPr>'
    if border:
        p += f'<w:pBdr><w:bottom w:val="single" w:color="{NAVY}" w:sz="5" w:space="3"/></w:pBdr>'
    if tabs:
        p += f'<w:tabs><w:tab w:val="right" w:pos="{TAB}"/></w:tabs>'
    sp = (f' w:before="{before}"' if before else '') + (f' w:after="{after}"' if after else '')
    p += f'<w:spacing{sp}/>'
    if jc: p += f'<w:jc w:val="{jc}"/>'
    p += '</w:pPr>' + ''.join(runs) + '</w:p>'
    return p

def bullet(text, numid):
    """Bullet paragraph. Supports **bold** inline."""
    runs, i = [], 0
    for m in re.finditer(r'\*\*(.+?)\*\*', text):
        if m.start() > i: runs.append(run(text[i:m.start()], 9))
        runs.append(run(m.group(1), 9, bold=True))
        i = m.end()
    if i < len(text): runs.append(run(text[i:], 9))
    if not runs: runs = [run(text, 9)]
    return ('<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
            f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{numid}"/></w:numPr>'
            '<w:spacing w:before="16" w:after="16"/></w:pPr>' + ''.join(runs) + '</w:p>')

def inline_runs(text, sz=9, color=BODY):
    """Body text with **bold** support."""
    runs, i = [], 0
    for m in re.finditer(r'\*\*(.+?)\*\*', text):
        if m.start() > i: runs.append(run(text[i:m.start()], sz, color=color))
        runs.append(run(m.group(1), sz, bold=True, color=NAVY))
        i = m.end()
    if i < len(text): runs.append(run(text[i:], sz, color=color))
    return runs or [run(text, sz, color=color)]

def cell(text, w, header=False):
    runs = inline_runs(text, 8.5, NAVY if header else BODY)
    if header:
        runs = [run(text, 8.5, bold=True, color=NAVY)]
    shd = '<w:shd w:val="clear" w:fill="F2F2F5"/>' if header else ''
    return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>'
            '<w:tcBorders>'
            + ''.join(f'<w:{s} w:val="single" w:sz="4" w:color="C8C8D2"/>'
                      for s in ('top', 'left', 'bottom', 'right')) + '</w:tcBorders>'
            + shd + '</w:tcPr>'
            '<w:p><w:pPr><w:spacing w:before="20" w:after="20"/></w:pPr>'
            + ''.join(runs) + '</w:p></w:tc>')

def table(cols, rows, total=9026):
    w = [total // len(cols)] * len(cols)
    x = ['<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr>' % total]
    x.append('<w:tr>' + ''.join(cell(c, w[i], header=True) for i, c in enumerate(cols)) + '</w:tr>')
    for r in rows:
        x.append('<w:tr>' + ''.join(cell(str(v), w[i]) for i, v in enumerate(r)) + '</w:tr>')
    x.append('</w:tbl><w:p><w:pPr><w:spacing w:after="60"/></w:pPr></w:p>')
    return ''.join(x)

def build(c, template=TEMPLATE):
    with zipfile.ZipFile(template) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    # reuse the template's own bullet list id so numbering.xml stays valid
    numid = (re.search(r'<w:numId w:val="(\d+)"/>', doc) or [None, '1'])[1]
    sect = re.search(r'<w:sectPr\b.*?</w:sectPr>', doc, re.S).group(0)

    body = [para([run(c['name'], 19, bold=True, color=NAVY)], after=32, jc='center'),
            para([run('  •  '.join(c['contact']), 8.5, color=SLATE)], after=90, jc='center')]
    if c.get('subtitle'):
        body.append(para([run(c['subtitle'], 9.5, bold=True, color=NAVY)], after=60, jc='center'))

    for s in c['sections']:
        if s.get('heading'):
            body.append(para([run(s['heading'], 9, bold=True, color=NAVY)],
                             before=120, after=35, border=True))
        if 'body' in s:
            body.append(para([run(s['body'], 9, color=BODY)], before=45, after=32))
        for p in s.get('paras', []):
            body.append(para(inline_runs(p), before=30, after=30))
        if s.get('table'):
            body.append(table(s['table']['cols'], s['table']['rows']))
        for b in s.get('bullets', []):
            body.append(bullet(b, numid))
        for e in s.get('entries', []):
            body.append(para(
                [run(f"{e['org']}  —  {e['role']}", 9.5, bold=True, color=NAVY),
                 '<w:r><w:tab/></w:r>',
                 run(e.get('dates', ''), 9.5, bold=True, color=NAVY)],
                before=90, after=14, tabs=True))
            if e.get('meta'):
                body.append(para([run('  •  '.join(e['meta']), 8.5, italic=True, color=SLATE)], after=20))
            for b in e.get('bullets', []):
                body.append(bullet(b, numid))
        for i, (label, items) in enumerate(s.get('skills', [])):
            body.append(para([run(f'{label}:  ', 9, bold=True, color=NAVY),
                              run(items, 9, color=BODY)],
                             before=18 if i == 0 else 14, after=14))

    new = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           '<w:body>' + ''.join(body) + sect + '</w:body></w:document>')

    out = sys.argv[2]
    shutil.copy(template, out)
    # rewrite document.xml inside the copied package
    tmp = out + '.tmp'
    with zipfile.ZipFile(template) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                data = new.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, out)
    return out

if __name__ == '__main__':
    c = json.load(open(sys.argv[1]))
    print('wrote', build(c))
