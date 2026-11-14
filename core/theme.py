"""theme.py - the colour palette (from your palette image) + light/dark CSS.
NOTE: hex codes were matched by eye/name from the image. If any look off, fix them in PALETTE below - nothing else needs to change."""

PALETTE = {  # primary
    "rich_black": "#04110F", "dark_green": "#06231F", "bangladesh": "#006A4E",
    "mountain_meadow": "#30BA8F", "caribbean": "#00D084", "anti_flash": "#F2F3F4",
    # secondary
    "pine": "#0B3B2E", "basil": "#0F4A3A", "forest": "#0F5A44", "frog": "#1E8F6B",
    "mint": "#2BB58B", "stone": "#5B7068", "pistachio": "#A5C9BA"}
P = PALETTE

THEMES = {
    "dark": dict(bg=P["rich_black"], surface=P["dark_green"], surface2=P["pine"], border=P["basil"], text=P["anti_flash"],
                 muted=P["pistachio"], accent=P["caribbean"], accent2=P["mountain_meadow"], on_accent=P["rich_black"], side="#051915", accent_soft="rgba(0,208,132,.14)"),
    "light": dict(bg=P["anti_flash"], surface="#FFFFFF", surface2="#E3F0EA", border=P["pistachio"], text=P["rich_black"],
                  muted="#4F655D", accent=P["bangladesh"], accent2=P["mountain_meadow"], on_accent="#FFFFFF", side="#FFFFFF", accent_soft="rgba(0,106,78,.12)"),
}
# meaning colours (a green-only palette can't express 'warning' or 'danger', so these two are added on purpose)
ROUTE = {"ALLOW": ("#00D084", "#04110F"), "CHALLENGE": ("#F59E0B", "#04110F"), "HARD BLOCK": ("#EF4444", "#FFFFFF")}

def plot_layout(mode, height=260, **kw):
    t = THEMES[mode]
    d = dict(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(color=t["text"], family="Inter, system-ui, sans-serif"), margin=dict(t=40, b=10, l=10, r=10))
    d.update(kw)          # caller's values (e.g. a custom margin) win
    return d

def _pill(key, on, align="flex-end"):
    """CSS that turns the st.button with key=`key` into a switch (track + knob). `on` = knob right/green."""
    return (f".st-key-{key}{{display:flex;justify-content:{align}}}"
            f".st-key-{key} button{{position:relative;width:auto!important;min-width:176px;padding:.5rem 1.1rem .5rem 3.6rem;border-radius:999px;"
            "background:var(--surface)!important;border:1.5px solid var(--accent)!important;color:var(--text)!important;justify-content:flex-start}"
            f".st-key-{key} button p{{margin:0;font-weight:600;color:var(--text)!important}}"
            f".st-key-{key} button::before{{content:'';position:absolute;left:10px;top:50%;width:38px;height:22px;margin-top:-11px;border-radius:999px;background:"
            + ("var(--accent)" if on else "#7C8F87") + "}"
            f".st-key-{key} button::after{{content:'';position:absolute;top:50%;width:16px;height:16px;margin-top:-8px;border-radius:50%;background:#FFFFFF;left:"
            + ("29px" if on else "13px") + "}")

def css(mode, stream_on=False, page="dashboard"):
    t = THEMES[mode]
    root = ":root{color-scheme:" + mode + ";" + "".join(f"--{k.replace('_','-')}:{v};" for k, v in t.items()) + "}"
    nav_active = f".st-key-nav_{page} button{{background:var(--accent-soft)!important;color:var(--accent)!important}}"
    pill = _pill("theme_btn", mode == "dark", "flex-start") + _pill("stream_btn", stream_on, "flex-start")
    return ("<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');"
            + root + STATIC + nav_active + pill + "</style>")

STATIC = """
html,body,.stApp,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stMainBlockContainer"],[data-testid="stBottom"],section.main,.main{background:var(--bg)!important;color:var(--text);font-family:Inter,system-ui,sans-serif}
[data-testid="stHeader"],[data-testid="stToolbar"]{background:transparent!important;pointer-events:none}[data-testid="stHeader"] *{pointer-events:auto}
.block-container{padding:2.6rem 2rem 3rem!important;max-width:1500px}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp p,.stApp li,.stApp label,.stApp summary{color:var(--text)}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--muted)!important}
[data-testid="stWidgetLabel"] *,[data-testid="stCheckbox"] *,[data-testid="stMarkdownContainer"] p,[data-testid="stSliderThumbValue"],[data-testid="stTickBarMin"],[data-testid="stTickBarMax"]{color:var(--text)!important}
/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:var(--side)!important;border-right:1px solid var(--border)}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding:1.2rem .9rem}
.brand{font-size:1.45rem;font-weight:800;letter-spacing:-.01em;margin:0}.brand-sub{color:var(--muted);font-size:.78rem;margin:.1rem 0 1rem}
.navlabel{color:var(--muted);font-size:.7rem;font-weight:700;letter-spacing:.12em;margin:1rem 0 .3rem .4rem}
[class*="st-key-nav_"] button{width:100%;justify-content:flex-start!important;background:transparent!important;border:0!important;color:var(--muted)!important;font-weight:600;padding:.55rem .85rem;border-radius:12px}
[class*="st-key-nav_"] button:hover{background:var(--surface2)!important;color:var(--text)!important}
[class*="st-key-nav_"] button p{margin:0;color:inherit!important;font-size:.97rem}
.sidecard{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:12px 14px;margin-top:1rem;font-size:.82rem;color:var(--text)}
.sidecard b{color:var(--accent)}
/* ---------- page header ---------- */
.pt{font-size:2.1rem;font-weight:800;letter-spacing:-.02em;margin:0;color:var(--text)}.ps{color:var(--muted);margin:.15rem 0 1.1rem;font-size:.98rem}
/* ---------- cards ---------- */
[class*="st-key-card"]{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:20px 22px}
.ct{font-size:1.12rem;font-weight:700;margin:0 0 .7rem 0;color:var(--text)}.cs{color:var(--muted);font-size:.85rem;margin:-.4rem 0 .8rem 0}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}
@media(max-width:1000px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:16px 18px}
.kpi .l{color:var(--muted);font-weight:600;font-size:.92rem}.kpi .v{font-size:2.2rem;font-weight:800;line-height:1.1;margin-top:.45rem;color:var(--text)}.kpi .s{font-size:.8rem;margin-top:.2rem;color:var(--muted)}
.up{color:var(--accent)!important}.down{color:#EF4444!important}
.banner{border-radius:16px;padding:18px 22px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center}
.banner .k{font-size:.88rem;font-weight:600;opacity:.9}.banner .t{font-size:1.75rem;font-weight:800;line-height:1.15}
.bar{height:12px;background:var(--surface2);border-radius:99px;overflow:hidden;margin:.5rem 0 .6rem}.bar>div{height:100%;border-radius:99px}
.big{text-align:center;font-size:1.6rem;font-weight:800;color:var(--text)}
.mi{display:grid;grid-template-columns:1fr 1fr;gap:14px 18px}.mi .l{color:var(--muted);font-size:.8rem}.mi .v{font-weight:700;font-size:1.05rem;color:var(--text)}
.ex{border-left:4px solid var(--accent2);background:var(--surface2);border-radius:10px;padding:10px 14px;margin:8px 0;font-size:.92rem;color:var(--text)}
.step{border-left:4px solid var(--accent2);background:var(--surface2);padding:9px 14px;margin:7px 0;border-radius:0 12px 12px 0;color:var(--text)}.step.flag{border-left-color:#EF4444}
.muted{color:var(--muted)}
.grid{display:flex;flex-wrap:wrap;gap:12px}.grid>.tile{flex:1 1 190px}
.tile{background:var(--surface2);border:1px solid var(--border);border-radius:16px;padding:14px 16px;color:var(--text)}
.num{display:inline-block;background:var(--accent);color:var(--on-accent);border-radius:50%;width:26px;height:26px;text-align:center;line-height:26px;font-weight:700;margin-right:8px}
.hero{background:linear-gradient(135deg,#006A4E,#06231F);color:#F2F3F4;border-radius:20px;padding:24px 28px;margin-bottom:14px}.hero h2,.hero p{color:#F2F3F4!important;margin:0 0 6px 0}
/* ---------- live feed ---------- */
.feedwrap{max-height:660px;overflow-y:auto;padding-right:6px}
.fc{background:var(--surface2);border:1px solid var(--border);border-left:5px solid var(--accent);border-radius:14px;padding:12px 14px;margin:10px 0}
.fc .h{display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:.93rem;color:var(--text)}
.fc .g{display:grid;grid-template-columns:repeat(3,1fr);gap:8px 10px;margin-top:9px}.fc .g .l{display:block;font-size:.66rem;letter-spacing:.07em;color:var(--muted);text-transform:uppercase}.fc .g .v{font-size:.86rem;font-weight:600;color:var(--text)}
.pill{display:inline-block;padding:3px 11px;border-radius:999px;font-weight:700;font-size:.78rem;white-space:nowrap}
.blink{animation:blink 1s infinite}@keyframes blink{50%{opacity:.4}}
.live{display:inline-block;padding:3px 12px;border-radius:999px;font-weight:700;font-size:.8rem;margin-right:8px}
.feed{width:100%;border-collapse:collapse;font-size:.84rem;color:var(--text)}.feed th{color:var(--muted);text-align:left;padding:7px 8px;border-bottom:1px solid var(--border);font-weight:600}.feed td{padding:7px 8px;border-bottom:1px solid var(--border)}
.sig{display:flex;gap:12px;padding:9px 0;border-bottom:1px solid var(--border)}.sig i{width:4px;border-radius:4px;flex:none}.sig b{display:block;font-size:.9rem;color:var(--text)}.sig span{font-size:.8rem;color:var(--muted)}
.ar{padding:9px 0;border-bottom:1px solid var(--border)}.ar b{display:block;font-size:.93rem;color:var(--text)}.ar span{font-size:.8rem;color:var(--muted)}.ar em{font-style:normal;font-size:.72rem;color:var(--muted)}
.cat{display:flex;justify-content:space-between;padding:7px 0;font-size:.92rem;color:var(--text)}
/* ---------- native widgets ---------- */
[data-testid="stMetric"]{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:10px 14px}
[data-testid="stMetricLabel"] *{color:var(--muted)!important}[data-testid="stMetricValue"] *{color:var(--text)!important}
div[data-baseweb="input"],div[data-baseweb="base-input"],div[data-baseweb="select"]>div{background:var(--surface2)!important;border-color:var(--border)!important;color:var(--text)!important;border-radius:12px!important}
input,textarea{color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;background:transparent!important}
input::placeholder{color:var(--muted)!important;-webkit-text-fill-color:var(--muted)!important}
[data-testid="stNumberInput"] button{background:var(--surface2)!important;color:var(--text)!important}
div[data-baseweb="select"] *{color:var(--text)!important}
div[data-baseweb="popover"] div,div[data-baseweb="popover"] ul,div[data-baseweb="menu"],li[role="option"]{background:var(--surface)!important;color:var(--text)!important}
li[role="option"]:hover{background:var(--surface2)!important}
.stButton>button,.stDownloadButton>button{width:100%;border-radius:12px;font-weight:600;background:var(--surface2);color:var(--text);border:1px solid var(--border)}
.stButton>button p,.stDownloadButton>button p{color:inherit!important}
.stButton>button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:linear-gradient(90deg,var(--accent),var(--accent2))!important;color:var(--on-accent)!important;border:0!important;font-weight:700;padding:.65rem 1rem}
.st-key-simfraud button{background:#EF4444!important;color:#fff!important;border:0!important}.st-key-simfraud button p{color:#fff!important}
[data-testid="stExpander"]{background:var(--surface);border:1px solid var(--border);border-radius:14px}
[data-testid="stExpander"] summary *{color:var(--text)!important}
[data-testid="stExpander"] svg,div[data-baseweb="select"] svg{fill:var(--muted)!important;color:var(--muted)!important}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--border);background:transparent!important}
.stTabs [data-baseweb="tab"]{color:var(--muted);font-weight:600}.stTabs [aria-selected="true"]{color:var(--accent)!important}
.stTabs [data-baseweb="tab-highlight"]{background:var(--accent)!important}[data-baseweb="tab-border"]{background:var(--border)!important}
[data-testid="stSlider"] [role="slider"]{background:var(--accent)!important;border:2px solid var(--surface)!important}
[data-testid="stTooltipContent"]{background:var(--surface2)!important;border:1px solid var(--border)}[data-testid="stTooltipContent"] *{color:var(--text)!important}
[data-testid="stAlert"]{border-radius:12px;border:1px solid var(--border)}[data-testid="stAlert"] *{color:var(--text)!important}
[data-testid="stRadio"] [role="radiogroup"]{gap:.4rem}
"""
