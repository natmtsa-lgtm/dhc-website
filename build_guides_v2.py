#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the 3 DHC stage-guide PDFs from the content .md files (WeasyPrint).

REPRODUCIBLE + PORTABLE rebuild of build_guides_final.py, with two fixes:
  1. Real brand fonts when available. Drop Fraunces + Inter TTFs into ./guide_fonts/
     (exact names below). If they're all present -> REAL build, writes the real finals.
     If not, it FALLS BACK to the Source Serif/Sans pip packages and writes *_LAYOUTTEST.pdf
     so it never clobbers a good real-font final by accident.
  2. Behaviour-spread pagination fix: content pages now flow continuously with a hairline
     separator instead of each being force-broken onto its own page. This removes the
     near-empty "orphan tail" pages (e.g. old Middle p.5) while keeping battles clearly
     delineated. Cover / how-to / divider / back still get their own pages.

  guide_fonts/ expected (REAL build):
    Fraunces-Regular.ttf Fraunces-SemiBold.ttf Fraunces-Bold.ttf
    Fraunces-Italic.ttf  Fraunces-SemiBoldItalic.ttf
    Inter-Regular.ttf Inter-SemiBold.ttf Inter-Bold.ttf Inter-Italic.ttf Inter-BoldItalic.ttf
  (Google Fonts / GitHub are proxy-blocked in the Claude sandbox, so fetch these in an
   environment with network access, or export them from the site's Google Fonts once.)
"""
import os, re, html, datetime
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = OUT = HERE
FONTS_DIR = os.path.join(HERE, "guide_fonts")
def furl(p): return "file://" + p

# ---- font resolution: REAL (guide_fonts) or FALLBACK (Source pip packages) ----
REAL_FACES = [  # (family, weight, style, filename in guide_fonts/)
    ("Fraunces", 400, "normal", "Fraunces-Regular.ttf"),
    ("Fraunces", 600, "normal", "Fraunces-SemiBold.ttf"),
    ("Fraunces", 700, "normal", "Fraunces-Bold.ttf"),
    ("Fraunces", 400, "italic", "Fraunces-Italic.ttf"),
    ("Fraunces", 600, "italic", "Fraunces-SemiBoldItalic.ttf"),
    ("Inter", 400, "normal", "Inter-Regular.ttf"),
    ("Inter", 600, "normal", "Inter-SemiBold.ttf"),
    ("Inter", 700, "normal", "Inter-Bold.ttf"),
    ("Inter", 400, "italic", "Inter-Italic.ttf"),
    ("Inter", 700, "italic", "Inter-BoldItalic.ttf"),
]

def real_fonts_present():
    return all(os.path.exists(os.path.join(FONTS_DIR, f)) for *_ , f in REAL_FACES)

def build_font_css():
    """Return (css, is_real). Prefer real fonts; else fall back to Source packages."""
    if real_fonts_present():
        css = "\n".join(
            "@font-face{font-family:'%s';src:url('%s');font-weight:%d;font-style:%s;}" %
            (fam, furl(os.path.join(FONTS_DIR, fn)), wt, st)
            for fam, wt, st, fn in REAL_FACES)
        return css, True
    # fallback: Adobe Source families mapped into the Fraunces/Inter slots
    import font_source_serif_pro, font_source_sans_pro
    SERIF = os.path.join(os.path.dirname(font_source_serif_pro.__file__), "files")
    SANS = os.path.join(os.path.dirname(font_source_sans_pro.__file__), "files")
    fb = [
        ("Fraunces", 400, "normal", SERIF, "SourceSerifPro-Regular.ttf"),
        ("Fraunces", 600, "normal", SERIF, "SourceSerifPro-Semibold.ttf"),
        ("Fraunces", 700, "normal", SERIF, "SourceSerifPro-Bold.ttf"),
        ("Fraunces", 400, "italic", SERIF, "SourceSerifPro-It.ttf"),
        ("Fraunces", 600, "italic", SERIF, "SourceSerifPro-SemiboldIt.ttf"),
        ("Inter", 400, "normal", SANS, "SourceSansPro-Regular.ttf"),
        ("Inter", 600, "normal", SANS, "SourceSansPro-Semibold.ttf"),
        ("Inter", 700, "normal", SANS, "SourceSansPro-Bold.ttf"),
        ("Inter", 400, "italic", SANS, "SourceSansPro-It.ttf"),
        ("Inter", 700, "italic", SANS, "SourceSansPro-BoldIt.ttf"),
    ]
    lines = []
    for fam, wt, st, d, fn in fb:
        p = os.path.join(d, fn)
        if os.path.exists(p):
            lines.append("@font-face{font-family:'%s';src:url('%s');font-weight:%d;font-style:%s;}" %
                         (fam, furl(p), wt, st))
    return "\n".join(lines), False

GUIDES = {
 "early": dict(src="DHC_EarlyStage_Guide_Content_v1.md", out="DHC_EarlyStage_Guide.pdf",
    title="The Early-Stage Guide", short="The Early-Stage Guide",
    sub="What to do after the diagnosis — while there’s still time to plan, together",
    start="## PAGE 1", ver="v1"),
 "middle": dict(src="DHC_Stage6_Guide_Content_v1.md", out="DHC_MiddleStage_Guide.pdf",
    title="The Middle-Stage Survival Guide", short="The Middle-Stage Survival Guide",
    sub="What to do when dementia gets hard — the daily battles, in plain language",
    start="## PAGE 3", ver="v1"),
 "late": dict(src="DHC_LateStage_Guide_Content_v1.md", out="DHC_LateStage_Guide.pdf",
    title="The Late-Stage Guide", short="The Late-Stage Guide",
    sub="Memory care, comfort, and the final months", start="## PAGE 1", ver="v1"),
}

LOGO = ('<svg width="46" height="46" viewBox="0 0 100 100" aria-hidden="true">'
 '<path d="M50 16 L84 45 M50 16 L16 45" fill="none" stroke="#3E6259" stroke-width="8" stroke-linecap="round"/>'
 '<path d="M24 44 L24 82 L76 82 L76 44" fill="none" stroke="#3E6259" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/>'
 '<path d="M50 72 C42 60 30 60 34 50 C37 43 46 45 50 52 C54 45 63 43 66 50 C70 60 58 60 50 72 Z" fill="#C0714F"/></svg>')

def inline(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\*\w])\*([^*]+?)\*(?!\*)', r'<em>\1</em>', t)
    return t

def clean_head(t):
    t = re.sub(r'\*\(.*?\)\*', '', t)
    t = t.replace('★','').replace('*','')
    return re.sub(r'\s+', ' ', t).strip()

def render_blocks(buf):
    out=[]; i=0; n=len(buf)
    def flush_para(p):
        p=p.strip()
        if not p: return
        m=re.match(r'^\*\*(.+?)\*\*(.*)$', p, re.S)
        if m:
            label=m.group(1).strip(); rest=m.group(2).strip(); low=label.lower()
            if low.startswith("when it's not just"):
                out.append('<div class="cbox medical"><div class="cbox-h">When it’s not just the dementia</div>'
                           '<p>%s</p></div>' % inline(re.sub(r'^when it’s not just the dementia[\.—\-\s]*','',label+ (' '+rest if rest else ''),flags=re.I)))
                return
            if low.startswith('borrow this sentence'):
                q=rest.lstrip(':').strip()
                out.append('<div class="cbox borrow"><div class="cbox-t">Borrow this sentence</div><p class="q">%s</p></div>'%inline(q))
                return
            if low.startswith('one line for the log'):
                q=rest.lstrip(':').strip()
                out.append('<div class="cbox log"><span class="logt">One line for the log</span> <span class="logb">%s</span></div>'%inline(q))
                return
            if low.startswith('a word on medication'):
                out.append('<div class="cbox med"><div class="cbox-h">A word on medication</div><p>%s</p></div>'%inline(rest.lstrip(':').strip()))
                return
            if rest=='':
                out.append('<p class="lblsolo">%s</p>'%inline(label))
                return
            out.append('<p><span class="lbl">%s</span> %s</p>'%(inline(label), inline(rest)))
            return
        out.append('<p>%s</p>'%inline(p))
    while i<n:
        ln=buf[i]; s=ln.strip()
        if s=='' or s=='---':
            i+=1; continue
        if s.startswith('### '):
            out.append('<h3>%s</h3>'%inline(clean_head(s[4:]))); i+=1; continue
        if s.startswith('> '):
            q=[]
            while i<n and buf[i].strip().startswith('>'):
                q.append(buf[i].strip().lstrip('>').strip()); i+=1
            text=' '.join(q).strip()
            aff = ('e.g.' in text and '**' in text) or 'affiliate' in text.lower() or 'footnotes, not prescriptions' in text.lower()
            cls='note aff' if aff else 'note'
            tag='<span class="afftag">Affiliate note</span>' if aff else ''
            out.append('<div class="%s">%s<p>%s</p></div>'%(cls,tag,inline(text)))
            continue
        if re.match(r'^\d+\.\s', s):
            items=[]
            while i<n and re.match(r'^\d+\.\s', buf[i].strip()):
                items.append(inline(re.sub(r'^\d+\.\s','',buf[i].strip()))); i+=1
            out.append('<ol>%s</ol>'%''.join('<li>%s</li>'%x for x in items)); continue
        if s.startswith('- '):
            items=[]
            while i<n and buf[i].strip().startswith('- '):
                items.append(inline(buf[i].strip()[2:])); i+=1
            out.append('<ul>%s</ul>'%''.join('<li>%s</li>'%x for x in items)); continue
        para=[s]; i+=1
        while i<n and buf[i].strip() and not re.match(r'^(>|-\s|\d+\.\s|###\s|---)', buf[i].strip()):
            para.append(buf[i].strip()); i+=1
        flush_para(' '.join(para))
    return '\n'.join(out)

def parse_pages(md, start_marker):
    lines=md.split('\n'); idx=0
    for k,l in enumerate(lines):
        if l.strip().startswith(start_marker): idx=k; break
    lines=lines[idx:]; pages=[]; cur=None; capturing=False
    def close():
        nonlocal cur
        if cur is not None:
            cur['html']=render_blocks(cur['buf']); pages.append(cur); cur=None
    for l in lines:
        s=l.strip()
        if re.match(r'^##\s+PAGE\b', s):
            close()
            eyebrow=clean_head(re.sub(r'^##\s+PAGE\s*\d*\s*[—\-]*\s*','',s))
            cur=dict(type='page',eyebrow=eyebrow,h1=None,buf=[]); capturing=True; continue
        if re.match(r'^##\s', s):
            close(); capturing=False; continue
        if re.match(r'^#\s', s):
            title=clean_head(s[2:])
            if capturing and cur is not None and cur['h1'] is None:
                cur['h1']=title; continue
            close(); pages.append(dict(type='divider',title=title)); capturing=False; continue
        if capturing and cur is not None:
            cur['buf'].append(l)
    close()
    return pages

def howto_html(g):
    if g['short'].startswith('The Middle'):
        extra=('<p>Every daily-battle page follows the same shape, so you can find what you need fast when '
        'it’s happening:</p><ul class="fmt">'
        '<li><b>What’s happening</b> — why, in about thirty seconds.</li>'
        '<li><b>In the moment</b> — what to try right now.</li>'
        '<li><b>What makes it worse</b> — what to stop doing.</li>'
        '<li><b>When it’s not just the dementia</b> — the sudden changes that mean you call, not manage.</li>'
        '<li><b>Borrow this sentence</b> — words that tend to work.</li>'
        '<li><b>One line for the log</b> — the one note that finds the pattern.</li></ul>')
    else:
        extra=('<p>This is a broad guide, meant to be read a page at a time. You do not need to read it '
        'front to back — start with whatever you’re facing now, and come back to the rest when you have room.</p>')
    return ('<section class="page howto">'
        '<div class="eyebrow">How to use this guide</div>'
        '<h1>Read only the page you need</h1>%s'
        '<div class="cbox med"><div class="cbox-h">The one rule that runs through everything</div>'
        '<p>A <b>sudden</b> change — new confusion, agitation, or sleepiness over hours or a day or two, '
        'often with a fever, pain, a change in urine, or after a new medication — is <b>medical until proven '
        'otherwise.</b> That is usually delirium, it is frequently reversible, and it needs a phone call, not a '
        'behaviour strategy. When something changes fast, think medical first.</p></div>'
        '<div class="note aff"><span class="afftag">A note on the footnotes</span>'
        '<p>A few pages point to products or services that genuinely help at this stage. Those are honest '
        'suggestions, not prescriptions — use only what helps, always with your person’s knowledge. '
        'Some are affiliate links, which means The Dementia House Call may earn a small commission at no extra '
        'cost to you; it never changes the guidance, and we never steer a medical decision toward a purchase.</p></div>'
        '</section>')%extra

def build(g, FONT_CSS, IS_REAL):
    md=open(os.path.join(SRC,g['src']),encoding='utf-8').read()
    pages=parse_pages(md,g['start'])
    body=[]
    body.append(
     '<section class="cover"><div class="cov-brand">%s<div class="wm-word">The Dementia House Call</div></div>'
     '<div class="cov-mid"><div class="cov-kick">A stage-by-stage guide for families</div>'
     '<h1 class="cov-title">%s</h1><div class="cov-sub">%s</div><div class="cov-rule"></div>'
     '<div class="cov-by">Plain, practical guidance from a doctor who makes dementia house calls</div></div>'
     '<div class="cov-foot">Educational information for caregivers — not medical advice.</div>'
     '</section>'%(LOGO,html.escape(g['title']),html.escape(g['sub'])))
    body.append(howto_html(g))
    first_content=True
    for p in pages:
        if p['type']=='divider':
            body.append('<section class="page divider"><div class="div-inner"><div class="div-line"></div>'
                        '<h2>%s</h2><div class="div-line"></div></div></section>'%inline(p['title']))
            first_content=True  # page after a divider starts fresh
            continue
        eb='<div class="eyebrow">%s</div>'%inline(p['eyebrow']) if p['eyebrow'] else ''
        h1='<h1>%s</h1>'%inline(p['h1']) if p['h1'] else ''
        cls='page firstpage' if first_content else 'page'
        body.append('<section class="%s">%s%s%s</section>'%(cls,eb,h1,p['html']))
        first_content=False
    body.append(
     '<section class="page back firstpage"><div class="cov-brand">%s<div class="wm-word">The Dementia House Call</div></div>'
     '<h1 class="back-h">You don’t have to figure this out alone</h1>'
     '<p class="back-p">The Dementia House Call sends free, plain-language letters for families — the same '
     'things a good house call would tell you. Join at <b>thedementiahousecall.com</b>, and look for the rest of '
     'the stage-by-stage series and the Care Binder.</p>'
     '<div class="back-series"><b>The series:</b> The Early-Stage Guide · The Middle-Stage Survival Guide '
     '· The Late-Stage Guide · and the Care Binder, the filing cabinet they all point back to.</div>'
     '<p class="disc">This guide is general education for families and is not medical advice; it does not create a '
     'doctor–patient relationship and does not replace your own physician. Anything that looks like a sudden '
     'change, an infection, or an injury needs assessing, not managing — if you’re unsure, assume it does '
     'and make the call. Some links in this guide are affiliate links; The Dementia House Call may earn a small '
     'commission at no cost to you, and it never changes the guidance. © %s The Dementia House Call.</p>'
     '</section>'%(LOGO,datetime.date.today().year))
    doc=TEMPLATE.replace('__FONTCSS__',FONT_CSS).replace('__TITLE__',html.escape(g['title'])).replace('__SHORT__',g['short']).replace('__BODY__','\n'.join(body))
    out_name = g['out'] if IS_REAL else g['out'].replace('.pdf','_LAYOUTTEST.pdf')
    outp=os.path.join(OUT,out_name)
    HTML(string=doc, base_url=OUT).write_pdf(outp)
    print("built", out_name, os.path.getsize(outp)//1024,"KB | pages parsed:", sum(1 for p in pages if p['type']=='page'))
    return outp

TEMPLATE = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
__FONTCSS__
:root{--cream:#FDFBF7;--cream2:#F5EFE4;--sand:#E4D9C6;--pine:#3E6259;--pine2:#2F4B44;
--clay:#C0714F;--clay2:#A05A3C;--claysoft:#E7C7B6;--ink:#2E3532;--muted:#6E6657;--line:#B9AF9F;}
@page{size:letter;margin:0.78in 0.72in 0.68in;
  @bottom-left{content:"__SHORT__";font-family:'Inter';font-size:7.6pt;color:#8F877A;}
  @bottom-center{content:"The Dementia House Call";font-family:'Inter';font-size:7.6pt;color:#8F877A;letter-spacing:.03em;}
  @bottom-right{content:"Page " counter(page);font-family:'Inter';font-size:7.6pt;color:#8F877A;}}
@page cover{margin:0;@bottom-left{content:none;}@bottom-center{content:none;}@bottom-right{content:none;}}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{background:var(--cream);color:var(--ink);font-family:'Inter',system-ui,sans-serif;font-size:11.2pt;line-height:1.5;}
.page,.cover,.back{position:relative;z-index:1;}
/* PAGINATION FIX: content pages flow continuously; only special pages force a break. */
.page{break-before:auto;}
.firstpage,.howto,.divider,.back{break-before:page;}
.page + .page{border-top:1px solid var(--line);margin-top:16pt;padding-top:15pt;}
.firstpage + .page{border-top:none;margin-top:0;padding-top:0;} /* no rule right after a forced-break page start */
p{margin:0 0 9pt;}
h1{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:24pt;line-height:1.12;color:var(--pine2);margin:0 0 12pt;break-after:avoid;}
h3{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:14.5pt;color:var(--pine);margin:14pt 0 6pt;break-after:avoid;}
.eyebrow{font-family:'Inter';font-weight:700;font-size:9pt;letter-spacing:.10em;text-transform:uppercase;color:var(--clay);margin:0 0 3pt;break-after:avoid;}
strong,b{font-weight:700;color:var(--pine2);}
em,i{font-style:italic;}
ul,ol{margin:0 0 10pt;padding-left:19pt;}
li{margin:0 0 4.5pt;}
.lblsolo{font-family:'Inter';font-weight:700;font-size:10.4pt;letter-spacing:.05em;text-transform:uppercase;color:var(--pine);margin:12pt 0 5pt;break-after:avoid;}
.lbl{font-weight:700;color:var(--pine2);}
.cbox{border-radius:9px;padding:11pt 14pt;margin:11pt 0;break-inside:avoid;}
.cbox-h{font-family:'Inter';font-weight:700;font-size:10pt;letter-spacing:.04em;text-transform:uppercase;margin:0 0 5pt;}
.cbox p{margin:0;}
.medical{background:#FBF3EE;border-left:4px solid var(--clay);}
.medical .cbox-h{color:var(--clay2);}
.med{background:var(--cream2);border-left:4px solid var(--pine);}
.med .cbox-h{color:var(--pine);}
.borrow{background:#EAF0ED;border:1px solid #CBDAD3;}
.borrow .cbox-t{font-family:'Inter';font-weight:700;font-size:8.6pt;letter-spacing:.09em;text-transform:uppercase;color:var(--pine);margin-bottom:3pt;}
.borrow .q{font-family:'Fraunces',Georgia,serif;font-style:italic;font-size:13pt;line-height:1.4;color:var(--pine2);}
.log{background:var(--sand);border-radius:7px;padding:8pt 12pt;font-size:10pt;break-inside:avoid;}
.log .logt{font-family:'Inter';font-weight:700;font-size:8.4pt;letter-spacing:.08em;text-transform:uppercase;color:var(--clay2);}
.log .logb{color:var(--ink);}
.note{background:var(--cream2);border-left:3px solid var(--line);border-radius:7px;padding:9pt 13pt;margin:11pt 0;font-size:10.4pt;color:#4c524d;break-inside:avoid;}
.note p{margin:0;}
.note.aff{border-left-color:var(--clay);}
.afftag{display:inline-block;font-family:'Inter';font-weight:700;font-size:7.6pt;letter-spacing:.08em;text-transform:uppercase;color:#fff;background:var(--clay);border-radius:20px;padding:2pt 8pt;margin-bottom:5pt;}
ul,ol{break-inside:avoid;}
.cover{page:cover;height:100vh;background:var(--cream2);padding:0.9in 0.8in;display:flex;flex-direction:column;}
.cov-brand{display:flex;align-items:center;gap:11px;}
.wm-word{font-family:'Inter';font-weight:700;font-size:11pt;letter-spacing:.14em;text-transform:uppercase;color:var(--pine);}
.cov-mid{flex:1;display:flex;flex-direction:column;justify-content:center;}
.cov-kick{font-family:'Inter';font-weight:700;font-size:11pt;letter-spacing:.10em;text-transform:uppercase;color:var(--clay);margin-bottom:12pt;}
.cov-title{font-family:'Fraunces',Georgia,serif;font-weight:700;font-size:44pt;line-height:1.04;color:var(--pine2);margin:0;}
.cov-sub{font-family:'Fraunces',Georgia,serif;font-style:italic;font-size:18pt;line-height:1.3;color:var(--clay2);margin:14pt 0 0;}
.cov-rule{width:80pt;height:3px;background:var(--clay);margin:22pt 0;}
.cov-by{font-size:12pt;color:var(--muted);max-width:80%;}
.cov-foot{font-size:9.5pt;color:var(--muted);text-align:center;}
.divider{display:flex;align-items:center;justify-content:center;height:9in;}
.div-inner{text-align:center;width:100%;}
.div-inner h2{font-family:'Fraunces',Georgia,serif;font-weight:700;font-size:30pt;color:var(--pine2);margin:16pt 0;letter-spacing:.01em;}
.div-line{height:2px;background:var(--line);width:38%;margin:0 auto;}
.back{page:cover;background:var(--cream2);min-height:100vh;padding:0.9in 0.8in;}
.back .cov-brand{margin-bottom:26pt;}
.back-h{font-size:26pt;color:var(--pine2);}
.back-p{font-size:12pt;max-width:92%;}
.back-series{background:var(--cream2);border-radius:9px;padding:12pt 15pt;margin:16pt 0 22pt;font-size:10.6pt;}
.disc{font-size:8.6pt;line-height:1.5;color:var(--muted);border-top:1px solid var(--line);padding-top:10pt;margin-top:20pt;}
.howto .fmt li{margin-bottom:5pt;}
.back.firstpage{border-top:none;margin-top:0;padding-top:0.9in;}
</style></head><body>
__BODY__
</body></html>"""

if __name__=="__main__":
    FONT_CSS, IS_REAL = build_font_css()
    print("FONTS:", "REAL Fraunces/Inter (guide_fonts/)" if IS_REAL
          else "FALLBACK Source Serif/Sans -> writing *_LAYOUTTEST.pdf (drop real TTFs in guide_fonts/ for finals)")
    for key in ("early","middle","late"):
        build(GUIDES[key], FONT_CSS, IS_REAL)
