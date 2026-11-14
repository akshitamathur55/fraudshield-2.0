import sys, os, json, shutil, zipfile, copy, re, subprocess
from lxml import etree
sys.path.insert(0, "/home/claude/report")
from lib_docx import *
import content1, content2, content3, content4
TITLE = "FraudShield 2.0: A Real-Time, Explainable, Multi-Class Fraud Detection and Decision Engine"
W = "{%s}" % WN
def txt(el): return "".join(t.text or "" for t in el.iter(W + "t")).strip()

def fld_par(label, page, lvl, first, last, instr, style=True):
    ppr = (f'<w:pStyle w:val="TOC{lvl}"/>' if style else "") + '<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8630"/></w:tabs><w:jc w:val="left"/>'
    body = ""
    if first: body += f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>'
    body += f'<w:r><w:t xml:space="preserve">{esc(label)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>{page}</w:t></w:r>'
    if last: body += '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    return X(f'<w:p><w:pPr>{ppr}</w:pPr>{body}</w:p>')

def build(pages=None, out="/home/claude/report/FraudShield_Report.docx"):
    pages = pages or {}
    work = "/tmp/build"; shutil.rmtree(work, ignore_errors=True); shutil.copytree("/tmp/tpl", work)
    tree = etree.parse(work + "/word/document.xml"); root = tree.getroot(); body = root.find("w:body", NS)
    kids = list(body); sect = kids[-1]
    R = json.load(open("/home/claude/report/results.json")); T = json.load(open("/home/claude/report/tests.json"))
    D = Doc(None); S = {}
    for m in (content1, content2, content3, content4): S.update(m.build(D, R, T))
    # cover title
    ts = list(kids[2].iter(W + "t")); ts[0].text = TITLE
    for t in ts[1:]: t.text = ""
    new = kids[:22]; heads = []; used = set()
    for el in kids[23:-1]:
        st = el.find("w:pPr/w:pStyle", NS); st = st.get(W + "val") if st is not None else None
        if st not in ("Heading1", "Heading2"): continue
        text = txt(el); h = copy.deepcopy(el)
        if st == "Heading1":
            ppr = h.find("w:pPr", NS); ps = ppr.find("w:pStyle", NS); ps.addnext(etree.SubElement(ppr, W + "pageBreakBefore")); 
        new.append(h); heads.append((int(st[-1]), text)); used.add(text)
        cont = S.get(text)
        if cont is None: print("!! no content for heading:", text); continue
        if cont in ("TOC", "LOF", "LOT"):
            continue  # filled after we know all headings
        new.extend(cont if isinstance(cont, list) else [cont])
    # TOC / LoF / LoT
    def fill(marker, entries, instr, lvlfn):
        i = next(k for k, e in enumerate(new) if e.tag == W + "p" and txt(e) == marker)
        paras = [fld_par(l, p, lv, k == 0, k == len(entries) - 1, instr, True) for k, (l, p, lv) in enumerate(entries)]
        for j, pr in enumerate(paras): new.insert(i + 1 + j, pr)
    fill("List of Tables", [(f"Table {n}: {t}", pages.get(("T", n), "0"), 1) for n, t in D.tbls], 'TOC \\h \\z \\c "Table"', None)
    fill("List of Figures", [(f"Figure {n}: {t}", pages.get(("F", n), "0"), 1) for n, t in D.figs], 'TOC \\h \\z \\c "Figure"', None)
    fill("Table of Contents", [(t, pages.get(("H", k), "0"), lv) for k, (lv, t) in enumerate(heads)], 'TOC \\o "1-2" \\h \\z \\u', None)
    for e in list(body): body.remove(e)
    for e in new: body.append(e)
    body.append(sect)
    # sectPr: footer + title page
    rel_footer = "rIdFooter1"
    fr = etree.Element(W + "footerReference"); fr.set(W + "type", "default"); fr.set("{%s}id" % NS["r"], rel_footer); sect.insert(0, fr)
    tp = etree.Element(W + "titlePg"); dg = sect.find("w:docGrid", NS)
    (dg.addprevious(tp) if dg is not None else sect.append(tp))
    tree.write(work + "/word/document.xml", xml_declaration=True, encoding="UTF-8", standalone=True)
    open(work + "/word/footer1.xml", "w", encoding="utf8").write(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="{WN}"><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
    # rels + media + content types
    rp = work + "/word/_rels/document.xml.rels"; rel = open(rp, encoding="utf8").read()
    add = f'<Relationship Id="{rel_footer}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
    os.makedirs(work + "/word/media", exist_ok=True)
    for rid, name, path in D.rels:
        shutil.copy(path, work + "/word/media/" + name); add += f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>'
    open(rp, "w", encoding="utf8").write(rel.replace("</Relationships>", add + "</Relationships>"))
    cp = work + "/[Content_Types].xml"; ct = open(cp, encoding="utf8").read()
    ct = ct.replace('<Default Extension="emf"', '<Default Extension="png" ContentType="image/png"/><Default Extension="emf"', 1)
    ct = ct.replace("</Types>", '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
    open(cp, "w", encoding="utf8").write(ct)
    # numbering
    npth = work + "/word/numbering.xml"; nt = etree.parse(npth); nr = nt.getroot()
    def abstract(aid, fmt, txt_, font):
        return X(f'<w:abstractNum w:abstractNumId="{aid}"><w:multiLevelType w:val="hybridMultilevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{txt_}"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>' + (f'<w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:hint="default"/></w:rPr>' if font else "") + "</w:lvl></w:abstractNum>")
    first_num = nr.find("w:num", NS); a1, a2 = abstract(9001, "bullet", "•", "Times New Roman"), abstract(9002, "decimal", "%1.", None)
    if first_num is not None: first_num.addprevious(a1); first_num.addprevious(a2)
    else: nr.append(a1); nr.append(a2)
    for i, kind in enumerate(D.nums, 1):
        aid = 9001 if kind == "bul" else 9002
        nr.append(X(f'<w:num w:numId="{900 + i}"><w:abstractNumId w:val="{aid}"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>'))
    nt.write(npth, xml_declaration=True, encoding="UTF-8", standalone=True)
    # zip (mimetype order: [Content_Types].xml first)
    if os.path.exists(out): os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(cp, "[Content_Types].xml")
        for dp, dn, fn in os.walk(work):
            for f in fn:
                full = os.path.join(dp, f); arc = os.path.relpath(full, work)
                if arc != "[Content_Types].xml": z.write(full, arc)
    return D, heads

def to_pdf(docx):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", os.path.dirname(docx), docx], capture_output=True, timeout=300)
    return docx.replace(".docx", ".pdf")

def find_pages(pdf, heads, D):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    pg = []
    for i in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True).stdout
        pg.append([l.strip() for l in t.splitlines() if l.strip()])
    pages = {}; cur = 0
    for k, (lv, text) in enumerate(heads):
        for i in range(cur, n):
            if text in pg[i]: pages[("H", k)] = str(i + 1); cur = i; break
    start = pages.get(("H", next(k for k, (l, t) in enumerate(heads) if t.startswith("Chapter 1"))), "1"); cur = int(start) - 1
    for kind, lst, key in (("Figure", D.figs, "F"), ("Table", D.tbls, "T")):
        c2 = cur
        for num, _ in lst:
            for i in range(c2, n):
                if any(l.startswith(f"{kind} {num}:") for l in pg[i]): pages[(key, num)] = str(i + 1); c2 = i; break
    return pages, n

if __name__ == "__main__":
    D, heads = build(); pdf = to_pdf("/home/claude/report/FraudShield_Report.docx"); pages, n = find_pages(pdf, heads, D)
    print("pass1 pages:", n, "headings found:", sum(1 for k in pages if k[0] == "H"), "/", len(heads), "figs", sum(1 for k in pages if k[0] == "F"), "/", len(D.figs), "tbls", sum(1 for k in pages if k[0] == "T"), "/", len(D.tbls))
    D, heads = build(pages); pdf = to_pdf("/home/claude/report/FraudShield_Report.docx"); pages2, n2 = find_pages(pdf, heads, D)
    print("pass2 pages:", n2, "stable:", pages2 == pages)
    if pages2 != pages:
        D, heads = build(pages2); pdf = to_pdf("/home/claude/report/FraudShield_Report.docx"); pages3, n3 = find_pages(pdf, heads, D); print("pass3 pages:", n3, "stable:", pages3 == pages2)
    json.dump({str(k): v for k, v in pages2.items()}, open("/home/claude/report/pages.json", "w"))
