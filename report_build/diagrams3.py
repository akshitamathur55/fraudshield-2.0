import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
from matplotlib.patches import FancyBboxPatch, Ellipse, Rectangle
IMG="/home/claude/report/img"; M,G,P,AM="#006A4E","#00D084","#E3F0EA","#FFF3D6"
class D:
    def __init__(s,w,h): s.fig,s.ax=plt.subplots(figsize=(w,h)); s.ax.set_xlim(0,w*10); s.ax.set_ylim(0,h*10); s.ax.axis("off"); s.n={}
    def band(s,x,y,w,h,label,fc="#F2F3F4"):
        s.ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.2,rounding_size=1.5",fc=fc,ec=M,lw=1)); s.ax.text(x+1.5,y+h-1.2,label,fontsize=8.5,weight="bold",color=M,va="top")
    def node(s,k,x,y,w,h,t,fc=P,shape="box",fs=8,ec=M,tc="#111"):
        s.n[k]=(x,y,w,h,shape)
        if shape=="ellipse": s.ax.add_patch(Ellipse((x,y),w,h,fc=fc,ec=ec,lw=1))
        elif shape=="cyl":
            s.ax.add_patch(Rectangle((x-w/2,y-h/2),w,h,fc=fc,ec=ec,lw=1)); s.ax.add_patch(Ellipse((x,y+h/2),w,h*.3,fc=fc,ec=ec,lw=1)); s.ax.add_patch(Ellipse((x,y-h/2),w,h*.3,fc=fc,ec=ec,lw=1)); s.ax.add_patch(Rectangle((x-w/2+.1,y-h/2),w-.2,h,fc=fc,ec="none"))
        else: s.ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle="round,pad=0.1,rounding_size=1",fc=fc,ec=ec,lw=1))
        s.ax.text(x,y,t,ha="center",va="center",fontsize=fs,color=tc)
    def _edge(s,k,tx,ty):
        x,y,w,h,sh=s.n[k]; dx,dy=tx-x,ty-y
        if dx==0 and dy==0: return x,y
        if sh=="ellipse": t=1/np.sqrt((dx/(w/2))**2+(dy/(h/2))**2)
        else: t=min((w/2)/abs(dx) if dx else 1e9,(h/2)/abs(dy) if dy else 1e9)
        return x+dx*t,y+dy*t
    def arrow(s,a,b,label="",ls="-",color="#2F4F46",off=(0,0),fs=7,both=False):
        xa,ya=s.n[a][:2]; xb,yb=s.n[b][:2]; p0=s._edge(a,xb,yb); p1=s._edge(b,xa,ya)
        s.ax.annotate("",xy=p1,xytext=p0,arrowprops=dict(arrowstyle="<->" if both else "->",color=color,lw=1.1,ls=ls,shrinkA=1,shrinkB=1))
        if label: s.ax.text((p0[0]+p1[0])/2+off[0],(p0[1]+p1[1])/2+off[1],label,fontsize=fs,ha="center",va="center",bbox=dict(fc="white",ec="none",pad=.6,alpha=.9))
    def save(s,name): s.fig.savefig(f"{IMG}/{name}.png",dpi=200,bbox_inches="tight",facecolor="white"); plt.close(s.fig)

# ---------- architecture ----------
d=D(7.2,7.9)
d.band(1,64,70,14,"Presentation layer  (Streamlit dashboard, app.py)")
for i,t in enumerate(["Start here\n(guide)","Check a\npayment","Live feed","Connections\nmap","Money saved\n(ROI)"]): d.node(f"t{i}",8.5+i*13.7,68,12,7,t,fs=7.5,fc="#FFFFFF" if i!=1 else "#C9F2E1")
d.band(1,30,70,31,"Decision engine  (core/model_wrapper.py  -  FraudShieldEngine.score)",fc="#E8F5EF")
for i,(k,t) in enumerate([("v","1  Schema\nvalidation"),("r","2  Business\nrules"),("g","3  Graph\nlookup"),("f","4  Feature\nlayer (13)")]): d.node(k,9.5+i*17,49,14.5,8,t,fs=8)
d.node("m",13.5,36,23,8,"5  ML classifier\n(5 classes)",fc=G,fs=8); d.node("x",36.5,36,19,8,"6  Explainability\n(local drivers)",fs=8); d.node("o",58,36,19,8,"7  Router: Allow /\nChallenge / Block",fs=8)
for a,b in (("v","r"),("r","g"),("g","f")): d.arrow(a,b)
d.arrow("f","m"); d.arrow("m","x"); d.arrow("x","o")
d.band(1,3,70,22,"Data and artefacts")
d.node("d1",11,11,17,8,"fraud_transactions.csv",shape="cyl",fs=7.5); d.node("d2",32,11,17,8,"fraud_detector.pkl",shape="cyl",fs=7.5); d.node("d3",56,11,17,8,"Audit log\n(session / CSV)",shape="cyl",fs=7.5)
for i in (1,2): d.arrow(f"t{i}","v",color="#6B7280")
d.arrow("d1","g",ls="--",label="graph",off=(-4,0)); d.arrow("d2","m",ls="--",label="load",off=(3,0)); d.arrow("o","d3",label="record",off=(4,0))
d.save("architecture")

# ---------- training pipeline ----------
d=D(7.2,3.6)
xs=[10,28,46,64]; 
for i,(k,t,s_) in enumerate([("a","data_gen.py\n12,179 synthetic\ntransactions","box"),("b","fraud_transactions\n.csv","cyl"),("c","Build entity graph\n(NetworkX)","box"),("d","Feature matrix\n13 x 12,179","box")]): d.node(k,xs[i]+3,28,15,10,t,shape=s_,fs=7.5)
for i,(k,t,s_,fc) in enumerate([("e","Stratified split\n80 % train /\n20 % test","box",P),("f","Balanced\nsample weights","box",P),("g","Gradient-boosted\ntrees (5 classes)","box","#00D084"),("h","Evaluate: macro-F1,\nconfusion matrix","box",P)]): d.node(k,[64,46,28,10][i]+3,9,15,10,t,fs=7.5,fc=fc)
for a,b in (("a","b"),("b","c"),("c","d"),("e","f"),("f","g"),("g","h")): d.arrow(a,b)
d.arrow("d","e"); d.ax.text(40,-4,"output: fraud_detector.pkl + training_metrics.json",fontsize=7.5,color=M,ha="center"); d.ax.text(0,38,"Row 1: data and features",fontsize=7,color="#6B7280"); d.ax.text(0,19,"Row 2: training and evaluation (right to left)",fontsize=7,color="#6B7280")
d.ax.set_xlim(0,80); d.ax.set_ylim(-6,40); d.save("trainpipe")

# ---------- DFD level 1 ----------
d=D(7.2,5.6)
d.node("src",9,52,14,6,"Payment source",fc=AM,ec="#F59E0B",fs=8)
pr=[("p1",9,36,"1.0\nValidate\npayload"),("p2",27,36,"2.0\nApply\nrules"),("p3",45,36,"3.0\nGraph\nlookup"),("p4",63,36,"4.0\nBuild\nfeatures"),("p5",63,17,"5.0\nPredict\nclass"),("p6",45,17,"6.0\nExplain"),("p7",27,17,"7.0\nRoute &\nrecord")]
for k,x,y,t in pr: d.node(k,x,y,13,11,t,shape="ellipse",fs=7.5,fc=G if k=="p5" else P)
d.node("usr",9,17,14,6,"Officer",fc="#FFFFFF",fs=8)
d.node("d1",45,52,15,5,"D1 History graph",shape="cyl",fs=7); d.node("d2",63,3,15,5,"D2 Model",shape="cyl",fs=7); d.node("d3",27,3,15,5,"D3 Audit log",shape="cyl",fs=7)
d.arrow("src","p1","payload",off=(-4,0)); d.arrow("p1","p2","clean payload",off=(0,2.2)); d.arrow("p2","p3","rule flags",off=(0,2.2)); d.arrow("p3","p4","device sharing",off=(0,2.2)); d.arrow("p4","p5","feature vector",off=(-7,0)); d.arrow("p5","p6","probabilities",off=(0,2.2)); d.arrow("p6","p7","drivers",off=(0,2.2))
d.arrow("d1","p3","links",off=(3,0)); d.arrow("d2","p5"); d.arrow("p7","d3","record",off=(5,0)); d.arrow("usr","p7","thresholds in /\ndecision out",both=True,off=(0,3.2)); d.arrow("p1","usr","validation errors",ls="--",off=(-8,0))
d.ax.set_xlim(0,76); d.ax.set_ylim(-2,58); d.save("dfd1")
print("ok")
