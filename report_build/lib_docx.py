"""Small helper library that writes WordprocessingML into the template package."""
import re, os, shutil, copy
from lxml import etree
from PIL import Image
WN = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WN, "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing", "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture"}
DECL = " ".join(f'xmlns:{k}="{v}"' for k, v in NS.items())
GREEN, DARK, LIGHT, ALT = "006A4E", "04110F", "E3F0EA", "F4F8F6"

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def X(xml):
    return etree.fromstring(f"<root {DECL}>{xml}</root>")[0]
def XS(xml):
    return list(etree.fromstring(f"<root {DECL}>{xml}</root>"))

TOK = re.compile(r"(\*\*.+?\*\*|~~.+?~~|`.+?`)")
def runs(text, size=None, color=None, bold=False, italic=False, font=None):
    out = []
    for part in TOK.split(text):
        if not part: continue
        b, i, code = bold, italic, False
        if part.startswith("**") and part.endswith("**"): part, b = part[2:-2], True
        elif part.startswith("~~") and part.endswith("~~"): part, i = part[2:-2], True
        elif part.startswith("`") and part.endswith("`"): part, code = part[1:-1], True
        rp = ""
        if code: rp += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
        elif font: rp += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'
        if b: rp += "<w:b/><w:bCs/>"
        if i: rp += "<w:i/><w:iCs/>"
        if color: rp += f'<w:color w:val="{color}"/>'
        sz = size if size else (20 if code else None)
        if sz: rp += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
        out.append(f'<w:r>{"<w:rPr>"+rp+"</w:rPr>" if rp else ""}<w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return "".join(out)

def P(text="", style=None, jc="both", keep=False, before=None, after=None, left=None, hanging=None, num=None, shd=None, size=None,
      bold=False, italic=False, color=None, tabs=None, pbb=False, line=None, font=None, border=None, raw=None, keeplines=False):
    pp = ""
    if style: pp += f'<w:pStyle w:val="{style}"/>'
    if keep: pp += "<w:keepNext/>"
    if keeplines: pp += "<w:keepLines/>"
    if pbb: pp += "<w:pageBreakBefore/>"
    if num: pp += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>'
    if border: pp += f'<w:pBdr><w:left w:val="single" w:sz="24" w:space="8" w:color="{border}"/></w:pBdr>'
    if shd: pp += f'<w:shd w:val="clear" w:color="auto" w:fill="{shd}"/>'
    if tabs: pp += "<w:tabs>" + "".join(f'<w:tab w:val="{v}" w:leader="{l}" w:pos="{p}"/>' for v, l, p in tabs) + "</w:tabs>"
    sp = ""
    if before is not None: sp += f' w:before="{before}"'
    if after is not None: sp += f' w:after="{after}"'
    if line is not None: sp += f' w:line="{line}" w:lineRule="auto"'
    if sp: pp += f"<w:spacing{sp}/>"
    if left is not None or hanging is not None:
        pp += f'<w:ind w:left="{left or 0}"' + (f' w:hanging="{hanging}"' if hanging else "") + "/>"
    if jc: pp += f'<w:jc w:val="{jc}"/>'
    body = raw if raw is not None else runs(text, size, color, bold, italic, font)
    return X(f'<w:p>{"<w:pPr>"+pp+"</w:pPr>" if pp else ""}{body}</w:p>')

class Doc:
    """Holds counters / registries used while building."""
    def __init__(self, pkg):
        self.pkg = pkg; self.fig = 0; self.tbl = 0; self.img = 0; self.rels = []; self.nums = []; self.figs = []; self.tbls = []; self.numbering_next = None
        self.rid_base = 5000; self.docpr = 100
    # ---------- lists ----------
    def bullets(self, items, ordered=False, after=60):
        numid = self.new_num(ordered); out = []
        for k, t in enumerate(items):
            out.append(P(t, style="ListParagraph", jc="both", num=numid, after=after if k < len(items) - 1 else 160, left=720, hanging=360))
        return out
    def new_num(self, ordered):
        self.nums.append(("dec" if ordered else "bul")); return 900 + len(self.nums)
    # ---------- captions ----------
    def caption(self, kind, text, jc="center", keep=False):
        if kind == "Figure": self.fig += 1; n = self.fig; self.figs.append((n, text))
        else: self.tbl += 1; n = self.tbl; self.tbls.append((n, text))
        raw = (f'<w:r><w:t xml:space="preserve">{kind} </w:t></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> SEQ {kind} \\* ARABIC </w:instrText></w:r>'
               f'<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>{n}</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r><w:r><w:t xml:space="preserve">: {esc(text)}</w:t></w:r>')
        return P(style="Caption", jc=jc, raw=raw, keep=keep, before=60 if kind == "Figure" else 160, after=200 if kind == "Figure" else 80)
    # ---------- figures ----------
    def figure(self, path, caption, width=6.0, max_h=7.6):
        im = Image.open(path); w, h = im.size; wi = width; hi = wi * h / w
        if hi > max_h: hi = max_h; wi = hi * w / h
        cx, cy = int(wi * 914400), int(hi * 914400)
        self.img += 1; rid = f"rIdImg{self.img}"; name = f"img_{self.img}.png"; self.rels.append((rid, name, path)); self.docpr += 1
        draw = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{self.docpr}" name="Figure {self.img}" descr="{esc(caption)}"/>'
                f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{self.docpr}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
        return [P(style=None, jc="center", keep=True, before=120, after=0, raw=draw), self.caption("Figure", caption)]
    # ---------- tables ----------
    def table(self, headers, rows, widths, caption=None, size=18, align=None, bold_first=False, total=8640, hl_rows=()):
        if caption: cap = self.caption("Table", caption, keep=True)
        s = sum(widths); widths = [int(w * total / s) for w in widths]
        align = align or ["left"] * len(headers)
        def cell(t, w, fill=None, hdr=False, al="left", b=False):
            tc = f'<w:tcW w:w="{w}" w:type="dxa"/>' + (f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else "") + '<w:vAlign w:val="center"/>'
            paras = "".join(f'<w:p><w:pPr><w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/><w:jc w:val="{ "center" if hdr else al}"/></w:pPr>{runs(line, size, "FFFFFF" if hdr else None, bold=hdr or b)}</w:p>' for line in str(t).split("\n"))
            return f"<w:tc><w:tcPr>{tc}</w:tcPr>{paras}</w:tc>"
        bd = "".join(f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="A5C9BA"/>' for e in ("top", "left", "bottom", "right", "insideH", "insideV"))
        x = f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{bd}</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr>'
        x += "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
        x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(cell(h, w, GREEN, True) for h, w in zip(headers, widths)) + "</w:tr>"
        for k, r in enumerate(rows):
            fill = "FFF3D6" if k in hl_rows else (ALT if k % 2 else None)
            x += "<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(cell(c, w, fill, False, al, b=(bold_first and j == 0)) for j, (c, w, al) in enumerate(zip(r, widths, align))) + "</w:tr>"
        x += "</w:tbl>"
        out = ([cap] if caption else []) + [X(x), P("", after=120, jc=None)]
        return out
    # ---------- boxes ----------
    def box(self, title, lines, height=None, dashed=True, fill="F7F7F7", color="808080"):
        """Single-cell bordered box used for placeholders the student fills in."""
        st = "dashed" if dashed else "single"
        bd = "".join(f'<w:{e} w:val="{st}" w:sz="8" w:space="0" w:color="{color}"/>' for e in ("top", "left", "bottom", "right"))
        content = P(title, jc="center", bold=True, color="595959", after=60, before=60, size=22).xpath("self::*")[0]
        ps = [etree.tostring(content).decode()] + [etree.tostring(P(l, jc="center", italic=True, color="7F7F7F", after=40, size=20)).decode() for l in lines]
        ps = [re.sub(r' xmlns:\w+="[^"]+"', "", p) for p in ps]
        trh = f'<w:trPr><w:cantSplit/>' + (f'<w:trHeight w:val="{height}" w:hRule="atLeast"/>' if height else "") + "</w:trPr>"
        x = (f'<w:tbl><w:tblPr><w:tblW w:w="8640" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{bd}</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid><w:gridCol w:w="8640"/></w:tblGrid>'
             f'<w:tr>{trh}<w:tc><w:tcPr><w:tcW w:w="8640" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="{fill}"/><w:vAlign w:val="center"/></w:tcPr>{"".join(ps)}</w:tc></w:tr></w:tbl>')
        return [X(x), P("", after=120, jc=None)]
    def callout(self, text, label="Note", color=GREEN, fill=LIGHT):
        bd = f'<w:top w:val="nil"/><w:left w:val="single" w:sz="36" w:space="0" w:color="{color}"/><w:bottom w:val="nil"/><w:right w:val="nil"/>'
        p = etree.tostring(P(f"**{label}.** " + text, jc="both", after=40, before=40, size=21)).decode(); p = re.sub(r' xmlns:\w+="[^"]+"', "", p)
        x = (f'<w:tbl><w:tblPr><w:tblW w:w="8640" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{bd}</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="140" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tblCellMar></w:tblPr>'
             f'<w:tblGrid><w:gridCol w:w="8640"/></w:tblGrid><w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr><w:tcW w:w="8640" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="{fill}"/></w:tcPr>{p}</w:tc></w:tr></w:tbl>')
        return [X(x), P("", after=100, jc=None)]
    def code(self, text):
        """Shaded monospace block for short commands (not source-code listings)."""
        out = []
        for l in text.split("\n"):
            out.append(P(raw=runs(f"`{l}`" if l.strip() else " ", size=19), jc="left", shd="F2F3F4", after=0, before=0, left=200, line=240))
        out.append(P("", after=120, jc=None)); return out

def H(el_template, text=None):
    return copy.deepcopy(el_template)
