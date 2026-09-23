# -*- coding: utf-8 -*-
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

F="/usr/share/fonts/truetype/"
pdfmetrics.registerFont(TTFont("S",  F+"liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("SB", F+"liberation/LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("R",  F+"liberation/LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("RB", F+"liberation/LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("M",  F+"dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("MB", F+"dejavu/DejaVuSansMono-Bold.ttf"))

PW,PH=612,792
ML=MR=48; TW=PW-ML-MR

BG   = HexColor("#050505")
SURF = HexColor("#0a0a0a")
SUR2 = HexColor("#18181b")
CY   = HexColor("#22d3ee")
EM   = HexColor("#10b981")
AM   = HexColor("#f59e0b")
RD   = HexColor("#f43f5e")
TXT  = HexColor("#fafafa")
MUT  = HexColor("#b0b0b8")
DIM  = HexColor("#6b6b73")
LINE = HexColor("#26262b")

c=canvas.Canvas("out/Amplifier_Regulatory_Approach.pdf",pagesize=(PW,PH))

def page_bg(grid=True):
    c.setFillColor(BG); c.rect(0,0,PW,PH,stroke=0,fill=1)
    if grid:
        c.setStrokeColor(Color(1,1,1,alpha=0.035)); c.setLineWidth(0.4)
        x=0
        while x<=PW:
            c.line(x,0,x,PH); x+=34
        y=0
        while y<=PH:
            c.line(0,y,PW,y); y+=34

def T(x,y,s,f,sz,col,right=False):
    c.setFont(f,sz); c.setFillColor(col)
    (c.drawRightString if right else c.drawString)(x,y,s)

def rule(y,col=LINE,w=0.6,x0=ML,x1=PW-MR):
    c.setStrokeColor(col); c.setLineWidth(w); c.line(x0,y,x1,y)

def box(x,y,w,h,fill=SURF,stroke=LINE,r=5,lw=0.7):
    if fill is not None:
        c.setFillColor(fill)
    c.setStrokeColor(stroke or LINE); c.setLineWidth(lw)
    c.roundRect(x,y,w,h,r,stroke=1 if stroke else 0,fill=1 if fill else 0)

def wrap(s,f,sz,maxw):
    out=[];line=""
    for wd in s.split():
        t=(line+" "+wd).strip()
        if c.stringWidth(t,f,sz)<=maxw: line=t
        else:
            if line: out.append(line)
            line=wd
    if line: out.append(line)
    return out

def para(x,y,s,f,sz,col,maxw,lead):
    for ln in wrap(s,f,sz,maxw):
        T(x,y,ln,f,sz,col); y-=lead
    return y

def chip(x,y,label,col,pad=6,sz=6.6):
    w=c.stringWidth(label,"MB",sz)+pad*2
    c.setFillColor(col); c.roundRect(x,y-2,w,12,3,stroke=0,fill=1)
    T(x+pad,y+1.4,label,"MB",sz,HexColor("#050505"))
    return w

def eyebrow(y,txt,col=CY):
    T(ML,y,txt,"MB",7.2,col)
    return y-26

def h1(y,txt,sz=27):
    T(ML,y,txt,"RB",sz,TXT); return y-sz*0.62

def h2(y,txt,sz=15.5):
    T(ML,y,txt,"SB",sz,TXT); return y-sz*0.75

def topbar():
    T(ML,PH-44,"AMPLIFIER HEALTH","SB",10.5,TXT)
    T(PW-MR,PH-43,"CONFIDENTIAL  ·  INTERNAL","MB",6.6,DIM,right=True)
    rule(PH-54)

def footer(n,label):
    rule(46)
    T(ML,33,label,"MB",6.6,DIM)
    T(PW-MR,33,"%02d"%n,"MB",7.6,CY,right=True)

# ---------------------------------------------------------------- PAGE 1
page_bg()
c.setFillColor(SURF); c.rect(0,PH-262,PW,262,stroke=0,fill=1)
c.setStrokeColor(Color(0.13,0.83,0.93,alpha=0.30)); c.setLineWidth(0.5)
for i in range(22):
    c.line(PW-250+i*12, PH-262, PW-170+i*12, PH)
c.setFillColor(CY); c.rect(0,PH-266,PW,3,stroke=0,fill=1)

T(ML,PH-52,"AMPLIFIER HEALTH","SB",11,TXT)
T(PW-MR,PH-51,"CONFIDENTIAL  ·  INTERNAL","MB",6.6,DIM,right=True)

y=PH-108
T(ML,y,"REGULATORY STRATEGY  ·  SEPTEMBER 2026","MB",7.4,CY); y-=34
T(ML,y,"Regulatory Approach","RB",40,TXT); y-=42
T(ML,y,"FDA pathway and the two phase strategy","RB",20,CY); y-=30
y=para(ML,y,"Built from the CDRH town hall on the Clinical Decision Support Software Final Guidance, March 11 2026, the Amplifier Financial Model v6, and LP diligence of September 22 2026.","S",9.3,MUT,TW-150,13)

y=PH-300
box(ML,y-96,TW,96,SUR2,LINE)
c.setFillColor(RD); c.rect(ML,y-96,3.5,96,stroke=0,fill=1)
T(ML+18,y-24,"THE FINDING","MB",7.2,RD)
yy=y-42
yy=para(ML+18,yy,"Voice analysis that interprets clinical state fails Criterion 1 of the Cures Act CDS exclusion. The CDS carve out is not the lane it was assumed to be.","RB",14.5,TXT,TW-36,17)
T(ML+18,yy-4,"The non device position rests on general wellness and non patient care uses. Everything with a disease claim is a device.","S",9.2,MUT)

y=y-124
stats=[("3","REGULATORY LANES","Wellness · Non care · Device"),
       ("4","CURES CRITERIA","All four must be met"),
       ("1","INDICATION FIRST","You clear a use, not a model"),
       ("$3.5M","VALIDATION BUDGET","Allocated in Series A")]
cw=TW/4
for i,(n,l,s) in enumerate(stats):
    x=ML+i*cw
    box(x,y-74,cw-7,74,SURF,LINE)
    c.setFillColor(CY); c.rect(x,y-1.5,cw-7,2.5,stroke=0,fill=1)
    T(x+11,y-36,n,"RB",23,TXT)
    T(x+11,y-51,l,"MB",6.2,CY)
    for j,ln in enumerate(wrap(s,"S",6.8,cw-26)):
        T(x+11,y-62-j*8,ln,"S",6.8,DIM)

y=y-104
rule(y); y-=20
cols=[("01","The guidance","Four criteria, the 2026 changes, enforcement discretion"),
      ("02","Where we sit","Criterion by criterion, and the Criterion 1 problem"),
      ("03","Three lanes","Wellness, non patient care, device, with partners mapped"),
      ("04","Two phases","Why clearance is sequenced second"),
      ("05","Controls","Claim language, and what phase one must hold"),
      ("06","Open items","Owners and the Pre Submission")]
for i,(n,t,d) in enumerate(cols):
    cx=ML+(i%3)*(TW/3); cy=y-(i//3)*46
    T(cx,cy,n,"MB",7,CY)
    T(cx+22,cy,t,"SB",9.6,TXT)
    for j,ln in enumerate(wrap(d,"S",7.2,TW/3-34)):
        T(cx+22,cy-11-j*8.6,ln,"S",7.2,DIM)

footer(1,"AMPLIFIER HEALTH  ·  REGULATORY APPROACH")
c.showPage()

# ---------------------------------------------------------------- PAGE 2
page_bg(); topbar()
y=PH-84
y=eyebrow(y,"SECTION 01  ·  THE FINAL GUIDANCE")
y=h1(y,"What the guidance says"); y-=10
y=para(ML,y,"The 21st Century Cures Act amended the device definition in December 2016, excluding five categories of software function under 520(o). Two matter to us: general wellness under 520(o)(1)(B), and clinical decision support under 520(o)(1)(E).","S",9.4,MUT,TW,13.5)
y-=14

# timeline
tl=[("DEC 2016","Cures Act"),("DEC 2017","Draft"),("SEP 2019","Revised draft"),("SEP 2022","Final"),("JAN 2026","Final, operative")]
ty=y-6
c.setStrokeColor(LINE); c.setLineWidth(1); c.line(ML+8,ty,PW-MR-8,ty)
seg=TW/(len(tl)-1)
for i,(d,l) in enumerate(tl):
    x=ML+8+i*(TW-16)/(len(tl)-1)
    last=(i==len(tl)-1); first=(i==0)
    c.setFillColor(CY if last else DIM)
    c.circle(x,ty,4.5 if last else 3,stroke=0,fill=1)
    dcol=CY if last else DIM; lcol=TXT if last else MUT
    c.setFont("MB",6.4); c.setFillColor(dcol)
    if first: c.drawString(x-4,ty+12,d)
    elif last: c.drawRightString(x+4,ty+12,d)
    else: c.drawCentredString(x,ty+12,d)
    c.setFont("SB",7.6); c.setFillColor(lcol)
    if first: c.drawString(x-4,ty-17,l)
    elif last: c.drawRightString(x+4,ty-17,l)
    else: c.drawCentredString(x,ty-17,l)
y=ty-38

box(ML,y-30,TW,30,SUR2,LINE)
T(ML+14,y-19,"The January 2026 final guidance is operative. It supersedes September 2022.","S",8.8,MUT)
y-=46

y=h2(y,"The four criteria"); y-=8
T(ML,y,"A function is excluded from the device definition only if it meets ALL FOUR.","MB",7.2,AM); y-=18

crit=[("1","Signal exclusion","Not intended to acquire, process or analyze a medical image, a signal from an IVD, or a pattern or signal from a signal acquisition system."),
      ("2","Medical information","Intended to display, analyze or print medical information about a patient or other medical information."),
      ("3","Recommendations","Intended to support or provide recommendations to an HCP about prevention, diagnosis or treatment."),
      ("4","Independent review","Intended to enable the HCP to independently review the basis, so they do not rely primarily on the output.")]
bw=(TW-18)/2
for i,(n,t,d) in enumerate(crit):
    bx=ML+(i%2)*(bw+18); by=y-(i//2)*86-78
    box(bx,by,bw,78,SURF,LINE)
    c.setFillColor(CY if n=="1" else DIM); c.rect(bx,by+76,bw,2,stroke=0,fill=1)
    T(bx+13,by+58,"CRITERION "+n,"MB",6.6,CY if n=="1" else DIM)
    T(bx+13,by+43,t,"SB",10.4,TXT)
    yy=by+30
    for ln in wrap(d,"S",7.9,bw-26)[:4]:
        T(bx+13,yy,ln,"S",7.9,MUT); yy-=10
y=y-180

y=h2(y,"Two changes in the 2026 guidance"); y-=16
for t,d in [("Time critical language removed from Criterion 3","It still bears on Criterion 4."),
            ("New enforcement discretion policy","Where a function gives one clinically appropriate output and therefore fails Criterion 3, but meets every other criterion, FDA intends to exercise enforcement discretion.")]:
    c.setFillColor(EM); c.circle(ML+3,y+3,2.6,stroke=0,fill=1)
    T(ML+14,y,t,"SB",9,TXT); y-=11.5
    y=para(ML+14,y,d,"S",8.4,MUT,TW-14,11)-6

y-=4
box(ML,y-34,TW,34,SUR2,RD)
T(ML+14,y-15,"Neither change helps a function that fails Criterion 1.","SB",9.4,TXT)
T(ML+14,y-26,"Enforcement discretion is scoped to Criterion 3 failures only.","S",8.4,MUT)

footer(2,"THE FINAL GUIDANCE")
c.showPage()

# ---------------------------------------------------------------- PAGE 3
page_bg(); topbar()
y=PH-84
y=eyebrow(y,"SECTION 02  ·  OUR POSITION",RD)
y=h1(y,"Where Amplifier sits"); y-=14

rows=[("1","Signal exclusion","FAIL",RD,"A microphone capturing voice for clinical inference is a system measuring a parameter external to the body for a medical purpose through streaming measurement. FDA states that software interpreting the clinical implications of a signal does not meet Criterion 1."),
      ("2","Medical information","FAIL",RD,"Raw acoustic waveform is not on FDA's list of medical information. Where the input is a note, symptom set or lab value it is satisfied. Where the input is the audio itself it is not."),
      ("3","Recommendations","PASS",EM,"Achievable. Output presented as options for an HCP to consider, not a directive. A binary result would fail, but that failure now falls inside enforcement discretion if all else is met."),
      ("4","Independent review","BUILD",AM,"Achievable and worth building regardless of pathway. Intended use, required inputs, plain language algorithm and validation description, knowns and unknowns.")]
for n,t,v,col,d in rows:
    h=56
    box(ML,y-h,TW,h,SURF,LINE)
    c.setFillColor(col); c.rect(ML,y-h,3.5,h,stroke=0,fill=1)
    T(ML+16,y-19,"CRITERION "+n,"MB",6.6,DIM)
    T(ML+85,y-19,t,"SB",10.2,TXT)
    chip(PW-MR-52,y-23,v,col)
    yy=y-33
    for ln in wrap(d,"S",7.8,TW-110)[:3]:
        T(ML+16,yy,ln,"S",7.8,MUT); yy-=9.6
    y-=h+8

y-=8
bh=112
box(ML,y-bh,TW,bh,SUR2,RD,lw=1.1)
T(ML+16,y-20,"THE ONE ARGUMENT WE HAVE, AND ITS LIMIT","MB",7,RD)
yy=y-38
yy=para(ML+16,yy,"FDA says discrete, episodic or intermittent point in time measurements, giving routine vital signs at a clinical encounter as the example, generally do not by themselves constitute a pattern. A single voice sample at one encounter is arguably not a pattern.","S",8.6,MUT,TW-32,11.2)
yy-=4
para(ML+16,yy,"That defeats the pattern prong. It does not defeat the signal prong, because Criterion 1 excludes a signal from a signal acquisition system independently. Longitudinal voice monitoring, core to the product thesis, fails both.","SB",8.6,TXT,TW-32,11.2)
y-=bh+22

y=h2(y,"FDA's own device examples land close"); y-=18
for d,r in [("Analyzes perspiration, heart rate, eye movement and breathing rate from wearables to monitor whether a person is having a heart attack or narcolepsy episode.","DEVICE  ·  CRITERION 1, IT ANALYZES SIGNALS"),
            ("Analyzes hourly pulse oximetry and heart rate from the EHR to identify signs of patient deterioration and alert an HCP.","DEVICE  ·  CRITERION 1, IT ANALYZES A PATTERN")]:
    lines=wrap(d,"S",8.2,TW-30)
    bh2=len(lines)*10+34
    box(ML,y-bh2,TW,bh2,SURF,LINE)
    yy=y-17
    for ln in lines:
        T(ML+14,yy,ln,"S",8.2,MUT); yy-=10
    T(ML+14,y-bh2+12,r,"MB",6.6,RD)
    y-=bh2+9

y-=6
box(ML,y-52,TW,52,SUR2,CY)
T(ML+16,y-18,"WHAT THIS MEANS","MB",7,CY)
para(ML+16,y-32,"Assume every clinical voice function falls outside the CDS carve out. Counsel confirms this in writing, or builds the contrary argument in writing.","S",8.6,TXT,TW-32,11)

footer(3,"WHERE AMPLIFIER SITS")
c.showPage()

# ---------------------------------------------------------------- PAGE 4
page_bg(); topbar()
y=PH-84
y=eyebrow(y,"SECTION 03  ·  THE THREE LANES",EM)
y=h1(y,"The lanes we actually have"); y-=12
y=para(ML,y,"The prior working assumption was general wellness plus the CDS carve out. The correct statement is general wellness plus non patient care uses. That distinction matters in writing, to investors, to partners and to counsel.","S",9.3,MUT,TW,13.5)
y-=18

lanes=[("LANE A",EM,"General wellness","520(o)(1)(B)","Maintaining or encouraging a healthy lifestyle and unrelated to diagnosis, cure, mitigation, prevention or treatment. Narrow. One disease claim breaks it."),
       ("LANE B",CY,"Non patient care","Outside device definition","Insurance risk, actuarial and underwriting, enterprise analytics, research. Not for diagnosis or treatment of an individual patient."),
       ("LANE C",RD,"Device pathway","510(k) or De Novo","Detects, screens for, diagnoses, predicts or monitors a disease in an individual. The CDS carve out does not rescue these.")]
lw_=(TW-20)/3; lh=148
for i,(tag,col,title,sub,desc) in enumerate(lanes):
    x=ML+i*(lw_+10)
    box(x,y-lh,lw_,lh,SURF,LINE)
    c.setFillColor(col); c.rect(x,y-6,lw_,6,stroke=0,fill=1)
    T(x+13,y-28,tag,"MB",7,col)
    T(x+13,y-47,title,"SB",12.2,TXT)
    T(x+13,y-60,sub,"M",6.8,DIM)
    yy=y-80
    for ln in wrap(desc,"S",7.9,lw_-26):
        T(x+13,yy,ln,"S",7.9,MUT); yy-=10
y-=lh+26

y=h2(y,"Partner map"); y-=6
T(ML,y,"Every counterparty sits in exactly one lane. Where it is unresolved, that is the open item.","S",8.4,DIM); y-=18

pm=[("Glow","A or C",AM,"Largest recurring line and a related party. Endpoint and claim dependent."),
    ("Flagship Pioneering","B",CY,"Per protocol custom models. Confirm no patient facing output."),
    ("Ultimate Human","A",EM,"Consumer wellness. Highest marketing drift risk. Warrants, no cash."),
    ("Canada Life","B",CY,"OSFI E-23 model risk scoping. Not FDA. In negotiation, not executed."),
    ("QBE","UNRESOLVED",RD,"Not in the financial model. Confirm an agreement exists."),
    ("Sutter Health","C",RD,"Clinical in substance. Research use with IRB, or restructure."),
    ("AssemblyAI, Amical","B or C",AM,"They build the product. Responsibility allocation is the issue."),
    ("zebraMD","C",RD,"Clinical integration. Determine the output and who acts on it.")]
rh=22
for i,(name,lane,col,note) in enumerate(pm):
    by=y-(i+1)*rh
    if i%2==0:
        c.setFillColor(SURF); c.rect(ML,by,TW,rh,stroke=0,fill=1)
    T(ML+10,by+8,name,"SB",8.4,TXT)
    chip(ML+128,by+5,lane,col,pad=5,sz=6.0)
    T(ML+196,by+8,wrap(note,"S",7.6,TW-206)[0],"S",7.6,MUT)
y-=len(pm)*rh+16

box(ML,y-46,TW,46,SUR2,AM)
T(ML+16,y-19,"THE CONTROL THAT KEEPS THE LANES SEPARATE","MB",7,AM)
para(ML+16,y-33,"Wellness and clinical endpoints separately gated in the API, separately labeled, separately contracted. One endpoint serving both lanes collapses the distinction the position depends on.","S",8.4,TXT,TW-32,10.5)

footer(4,"THE THREE LANES")
c.showPage()

# ---------------------------------------------------------------- PAGE 5
page_bg(); topbar()
y=PH-84
y=eyebrow(y,"SECTION 04  ·  SEQUENCING")
y=h1(y,"Why clearance is a second phase"); y-=14

ph_h=104
box(ML,y-ph_h,TW/2-9,ph_h,SURF,EM)
c.setFillColor(EM); c.rect(ML,y-6,TW/2-9,6,stroke=0,fill=1)
T(ML+15,y-28,"PHASE ONE  ·  NOW","MB",7,EM)
T(ML+15,y-48,"Sell in clean lanes","SB",13,TXT)
yy=y-66
for ln in wrap("Wellness, non patient care and research deployments generate clinically labeled voice at population scale, in the environment the product runs in.","S",8.2,TW/2-40):
    T(ML+15,yy,ln,"S",8.2,MUT); yy-=10

x2=ML+TW/2+9
box(x2,y-ph_h,TW/2-9,ph_h,SURF,CY)
c.setFillColor(CY); c.rect(x2,y-6,TW/2-9,6,stroke=0,fill=1)
T(x2+15,y-28,"PHASE TWO  ·  SERIES A FUNDED","MB",7,CY)
T(x2+15,y-48,"File on one indication","SB",13,TXT)
yy=y-66
for ln in wrap("The dataset built in phase one is the submission. Regulatory infrastructure already stands. Every later indication rides the same rails.","S",8.2,TW/2-40):
    T(x2+15,yy,ln,"S",8.2,MUT); yy-=10

ax=ML+TW/2; ay=y-ph_h/2
c.setStrokeColor(CY); c.setLineWidth(1.2)
c.line(ax-6,ay,ax+6,ay); c.line(ax+2,ay+4,ax+6,ay); c.line(ax+2,ay-4,ax+6,ay)
y-=ph_h+24

reasons=[("01","You do not clear a foundation model","You clear one intended use on one indication. A submission is only as strong as the evidence behind that single claim."),
         ("02","The evidence is real world data","Commercial deployments generate clinically labeled voice from the people the product is for. Filing before we hold it means filing a weaker submission."),
         ("03","Trial generated evidence costs multiples more","And it produces data less representative of deployment. Both 510(k) and De Novo scenarios are modeled."),
         ("04","The infrastructure gets built once","QMS, CFR Part 11, validation architecture, labeling discipline, SOC 2 Type II, HIPAA BAA."),
         ("05","The phases do not depend on each other","Revenue today does not require clearance. Clearance does not require revenue. If FDA timelines move, the business keeps running.")]
for n,t,d in reasons:
    T(ML,y,n,"MB",8,CY)
    T(ML+28,y,t,"SB",10,TXT); y-=12
    y=para(ML+28,y,d,"S",8.4,MUT,TW-28,11)-9

y-=2
y=h2(y,"Phase two, four decisions not yet made"); y-=16
dec=[("Which indication first","Clinical value, evidence in hand, prevalence in our dataset, commercial pull, predicate availability. Anemia and depression are the candidates."),
     ("510(k) or De Novo","Turns on predicate availability. De Novo is slower and creates the classification others then use as their predicate. That is an asset, not only a cost."),
     ("Evidence design","Prospective with a prespecified protocol, or retrospective on the existing dataset with an independent holdout."),
     ("Pre Submission","A Q-Sub settles Criterion 1, classification and evidence design with the agency rather than internally. Cheapest de risking step available.")]
bw=(TW-14)/2
for i,(t,d) in enumerate(dec):
    bx=ML+(i%2)*(bw+14); by=y-(i//2)*74-66
    box(bx,by,bw,66,SURF,LINE)
    T(bx+13,by+48,t,"SB",9.6,TXT)
    yy=by+35
    for ln in wrap(d,"S",7.7,bw-26)[:4]:
        T(bx+13,yy,ln,"S",7.7,MUT); yy-=9.4

footer(5,"WHY TWO PHASES")
c.showPage()

# ---------------------------------------------------------------- PAGE 6
page_bg(); topbar()
y=PH-84
y=eyebrow(y,"SECTION 05  ·  CONTROLS",AM)
y=h1(y,"Claim language is the control"); y-=10
y=para(ML,y,"Intended use, as evidenced by labeling and promotional material, determines device status. Not architecture. Not who ships the product. Partner marketing attaches to us too.","S",9.3,MUT,TW,13)
y-=18

colw=(TW-14)/2
box(ML,y-150,colw,150,SURF,RD)
c.setFillColor(RD); c.rect(ML,y-6,colw,6,stroke=0,fill=1)
T(ML+14,y-28,"REMOVE FROM MATERIALS","MB",7,RD)
yy=y-48
for s in ["Diagnostic, diagnose, detects disease","Screens for","Clinical grade vital sign","Identifies patients with","Predicts onset of, monitors for","Any disease name plus a detection verb"]:
    c.setStrokeColor(RD); c.setLineWidth(1.1)
    c.line(ML+15,yy+3,ML+21,yy+9); c.line(ML+21,yy+3,ML+15,yy+9)
    for j,ln in enumerate(wrap(s,"S",8.4,colw-42)):
        T(ML+29,yy,ln,"S",8.4,TXT); yy-=10
    yy-=7
T(ML+14,y-142,"Clinical grade vital sign is live today.","MB",6.6,RD)

bx=ML+colw+14
box(bx,y-150,colw,150,SURF,EM)
c.setFillColor(EM); c.rect(bx,y-6,colw,6,stroke=0,fill=1)
T(bx+14,y-28,"DEFENSIBLE IN LANE A AND B","MB",7,EM)
yy=y-48
for s in ["Acoustic measurement","Vocal biomarker signal","Wellness insight","Performance and recovery signal","Population level risk stratification","Research use only, where accurate"]:
    c.setStrokeColor(EM); c.setLineWidth(1.2)
    c.line(bx+15,yy+5,bx+18,yy+2); c.line(bx+18,yy+2,bx+23,yy+10)
    for j,ln in enumerate(wrap(s,"S",8.4,colw-42)):
        T(bx+29,yy,ln,"S",8.4,TXT); yy-=10
    yy-=7
T(bx+14,y-142,"After clearance: the cleared use verbatim.","MB",6.6,EM)
y-=176

y=eyebrow(y,"SECTION 06  ·  OPEN ITEMS")
T(ML,y+8,"Owners","SB",15.5,TXT); y-=14

items=[("REGULATORY COUNSEL",RD,["Written position on Criterion 1. If there is a contrary argument it goes in writing before it is relied on.","Confirm the written assessment exists and produce the non privileged diligence summary.","Advise whether any live deployment has drifted into Lane C without labeling."]),
       ("CORPORATE COUNSEL",CY,["Review Glow, Flagship, Ultimate Human, AssemblyAI and Amical for regulatory responsibility allocation and claim restriction clauses. Add where missing."]),
       ("PRODUCT AND ENGINEERING",CY,["Separate wellness and clinical endpoints with distinct gating, labeling and contracts.","Build the Criterion 4 disclosure set. It serves the carve out argument, enterprise buyers and the submission."]),
       ("MARKETING AND GTM",AM,["Audit every live asset against the claim language list."]),
       ("AMIT",EM,["Pick the first indication and the pathway.","Schedule the FDA Pre Submission."])]
for owner,col,lst in items:
    T(ML,y,owner,"MB",6.8,col); y-=12
    for s in lst:
        c.setFillColor(col); c.rect(ML+2,y+2,2.5,2.5,stroke=0,fill=1)
        for j,ln in enumerate(wrap(s,"S",8.2,TW-18)):
            T(ML+14,y,ln,"S",8.2,MUT if j else TXT); y-=9.8
        y-=3
    y-=6

box(ML,y-40,TW,34,SUR2,CY)
T(ML+14,y-22,"Amit Mehta, MD, FRCP   ·   amit@amplifierhealth.com","SB",8.6,TXT)
T(PW-MR-14,y-22,"Analysis of published guidance. Not legal advice.","S",7.4,DIM,right=True)
footer(6,"CONTROLS AND OPEN ITEMS")
c.showPage()

c.save()
print("OK")
