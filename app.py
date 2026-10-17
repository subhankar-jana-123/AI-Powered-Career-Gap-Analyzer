"""AI-Powered Career Gap Analyzer  |  run:  streamlit run app.py"""
import random

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database import DB_PATH, load_data, query, TOP_SKILLS_SQL, DEMAND_BY_ROLE_SQL
from src.pipeline import build
from src.skills import SKILLS
from src.skill_extractor import extract_skills
from src.matcher import (role_demand, gap_analysis, readiness, learning_plan,
                         recommend_roles, analyze_job_description)

st.set_page_config(page_title="AI Career Gap Analyzer", page_icon="🎯", layout="wide")

# ------------------------------------------------------------------ STYLE
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, .stApp, [class*="css"] {font-family:'Poppins',sans-serif;}
.stApp{background:linear-gradient(-45deg,#0f0c29,#1b2a6b,#24243e,#0b4f6c,#3a1c71);background-size:400% 400%;animation:bgshift 20s ease infinite;}
@keyframes bgshift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
[data-testid="stSidebar"]{background:rgba(255,255,255,0.06);backdrop-filter:blur(14px);border-right:1px solid rgba(255,255,255,0.12);}
/* floating bubbles */
.bubbles{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0;}
.bubbles span{position:absolute;bottom:-160px;border-radius:50%;background:radial-gradient(circle at 30% 30%,rgba(255,255,255,.18),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.08);animation:rise linear infinite;}
@keyframes rise{0%{transform:translateY(0) translateX(0) rotate(0);opacity:0}10%{opacity:1}100%{transform:translateY(-125vh) translateX(50px) rotate(360deg);opacity:0}}
/* hero */
.hero{text-align:center;padding:1rem 0 .6rem;animation:fadeUp .9s ease both;}
.hero h1{font-size:2.7rem;font-weight:700;margin:0;background:linear-gradient(90deg,#00e5ff,#a855f7,#ff5ea8,#00e5ff);background-size:300% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shine 6s linear infinite;}
.typing{width:max-content;max-width:100%;margin:.4rem auto 0;font-size:1.05rem;color:#b8c4ff;white-space:nowrap;overflow:hidden;animation:reveal 3.5s steps(70,end) both;}
@keyframes reveal{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes shine{to{background-position:300% 0}}
@keyframes fadeUp{from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:scale(1)}}
@keyframes slideIn{from{opacity:0;transform:translateX(-45px)}to{opacity:1;transform:none}}
@keyframes grow{from{width:0}to{width:var(--w)}}
/* glass cards */
.glass{background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-radius:18px;padding:1rem 1.3rem;margin-bottom:.8rem;backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(0,0,0,.25);transition:transform .3s,box-shadow .3s;animation:fadeUp .7s ease both;}
.glass:hover{transform:translateY(-6px);box-shadow:0 14px 40px rgba(0,229,255,.28);}
.label{font-size:.75rem;opacity:.75;text-transform:uppercase;letter-spacing:.09em;}
.value{font-size:2.3rem;font-weight:700;color:#00e5ff;line-height:1.2;}
/* count-up numbers */
@property --n{syntax:'<integer>';inherits:false;initial-value:0;}
.count{animation:countup 1.6s ease-out forwards;counter-reset:n var(--n);}
.count::after{content:counter(n);}
@keyframes countup{from{--n:0}to{--n:var(--target)}}
/* progress ring */
.ring{display:flex;flex-direction:column;align-items:center;}
.rwrap{position:relative;width:140px;height:140px;}
.rtext{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:1.9rem;font-weight:700;}
@keyframes ringdraw{from{stroke-dashoffset:339.3}to{stroke-dashoffset:var(--off)}}
/* chips */
.chip{display:inline-block;padding:.3rem .85rem;margin:.22rem;border-radius:999px;font-size:.85rem;animation:pop .5s cubic-bezier(.2,1.6,.4,1) both;}
.chip.have{background:rgba(46,204,113,.18);border:1px solid #2ecc71;color:#8dffb8;}
.chip.miss{background:rgba(255,82,82,.16);border:1px solid #ff5252;color:#ffb3b3;}
/* roadmap */
.step{display:flex;align-items:center;gap:1rem;padding:.8rem 1.1rem;margin-bottom:.6rem;border-radius:14px;background:rgba(255,255,255,.06);border-left:4px solid #00e5ff;animation:slideIn .6s ease both;transition:background .3s,transform .3s;}
.step:hover{background:rgba(0,229,255,.12);transform:translateX(8px);}
.step .num{min-width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#00e5ff,#a855f7);display:flex;align-items:center;justify-content:center;font-weight:700;color:#0f0c29;}
.step .grow{flex:1;}
.step a{color:#00e5ff;text-decoration:none;font-weight:600;}
.badge{padding:.15rem .7rem;border-radius:999px;font-size:.75rem;font-weight:600;}
.badge.High{background:#ff5252;color:#fff;}
.badge.Medium{background:#ffb300;color:#000;}
.badge.Nicetohave{background:#26c6da;color:#000;}
/* role bars */
.rbar{height:10px;border-radius:99px;background:rgba(255,255,255,.12);overflow:hidden;margin:.4rem 0;}
.rbar div{height:100%;border-radius:99px;background:linear-gradient(90deg,#00e5ff,#a855f7);animation:grow 1.4s ease-out both;}
.rtop{display:flex;justify-content:space-between;}
button[data-baseweb="tab"]{font-weight:600;}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- HELPERS
def bubbles(n=16):
    rnd = random.Random(7)
    spans = "".join(
        f'<span style="left:{rnd.randint(0, 96)}%;width:{(s := rnd.randint(20, 110))}px;height:{s}px;'
        f'animation-duration:{rnd.randint(16, 32)}s;animation-delay:-{rnd.randint(0, 28)}s"></span>'
        for _ in range(n))
    return f'<div class="bubbles">{spans}</div>'


def stat(label, value, suffix="", delay=0.0):
    return (f'<div class="glass" style="animation-delay:{delay}s"><div class="label">{label}</div>'
            f'<div class="value"><span class="count" style="--target:{int(value)}"></span>{suffix}</div></div>')


def ring(pct, label="Readiness"):
    off = 339.3 * (1 - pct / 100)
    return ('<div class="glass ring"><div class="rwrap"><svg width="140" height="140" viewBox="0 0 120 120">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#00e5ff"/>'
            '<stop offset="100%" stop-color="#a855f7"/></linearGradient></defs>'
            '<circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="10"/>'
            f'<circle cx="60" cy="60" r="54" fill="none" stroke="url(#g)" stroke-width="10" stroke-linecap="round" '
            f'stroke-dasharray="339.3" style="--off:{off};animation:ringdraw 1.8s ease-out both" transform="rotate(-90 60 60)"/>'
            f'</svg><div class="rtext"><span class="count" style="--target:{int(pct)}"></span>%</div></div>'
            f'<div class="label">{label}</div></div>')


def chips(df, status):
    cls, icon = ("have", "✅") if status == "Have" else ("miss", "❌")
    items = df[df["status"] == status]["skill"].tolist()
    body = "".join(f'<span class="chip {cls}" style="animation-delay:{i * 0.06}s">{icon} {s}</span>'
                   for i, s in enumerate(items))
    return body or "<i>None</i>"


def roadmap(plan):
    return "".join(
        f'<div class="step" style="animation-delay:{i * 0.12}s"><div class="num">{i + 1}</div>'
        f'<div class="grow"><b>{r.skill.title()}</b><br><small>{r.est_weeks} weeks · total {r.cumulative_weeks} weeks</small></div>'
        f'<span class="badge {r.tier.replace("-", "")}">{r.tier}</span>'
        f'<a href="{r.resource}" target="_blank">Learn ➜</a></div>'
        for i, r in enumerate(plan.itertuples()))


def role_cards(rec):
    return "".join(
        f'<div class="glass" style="animation-delay:{i * 0.1}s"><div class="rtop"><b>{i + 1}. {r.role}</b>'
        f'<b style="color:#00e5ff">{r.match_pct}%</b></div><div class="rbar"><div style="--w:{r.match_pct}%"></div></div>'
        f'<small>Missing: {r.top_missing_skills or "nothing — you are ready!"}</small></div>'
        for i, r in enumerate(rec.itertuples()))


def style(fig, height=None):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#e8eaf6", margin=dict(l=10, r=10, t=50, b=10),
                      transition={"duration": 600}, height=height)
    return fig


@st.cache_data
def get_data():
    if not DB_PATH.exists():
        build()
    return load_data()


# ------------------------------------------------------------------- PAGE
jobs, job_skills = get_data()
st.markdown(bubbles(), unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🎯 AI-Powered Career Gap Analyzer</h1>'
            '<div class="typing">Find your skill gaps. Get a learning roadmap. Land your dream tech role.</div></div>',
            unsafe_allow_html=True)

st.sidebar.markdown("## 🎓 Your Profile")
picked = st.sidebar.multiselect("Select your skills", sorted(SKILLS))
resume = st.sidebar.text_area("...or paste resume / skills text", height=150)
detected = extract_skills(resume) if resume else set()
student = set(picked) | detected
if detected:
    st.sidebar.caption("Detected: " + ", ".join(sorted(detected)))
CUSTOM = "➕ Custom role..."
role_choice = st.sidebar.selectbox("🎯 Target role", sorted(jobs["title"].unique()) + [CUSTOM])
custom = role_choice == CUSTOM
if custom:
    role = st.sidebar.text_input("Your role name", "My Dream Role")
    custom_skills = st.sidebar.multiselect("Skills this role needs", sorted(SKILLS))
    demand = pd.Series({s: 1.0 for s in custom_skills}, dtype=float)
else:
    role = role_choice
    demand = role_demand(jobs, job_skills, role)
min_demand = st.sidebar.slider("Hide skills required by fewer than (%) of postings", 0, 80, 25) / 100

tab1, tab2, tab3, tab4 = st.tabs(["📊 Gap Analysis", "🏆 Best-Fit Roles", "🌍 Market Insights", "📝 Analyze a Job Description"])

# ---- Tab 1: gap analysis
with tab1:
    gap = gap_analysis(student, demand, 0 if custom else min_demand)
    if gap.empty:
        st.info("👈 Pick the skills your custom role needs in the sidebar." if custom else "No skills found for this role at the chosen threshold.")
    else:
        if not student:
            st.info("👈 Select your skills (or paste your resume) in the sidebar to see your real gap.")
        plan = learning_plan(gap)
        score = readiness(gap)
        c0, c1, c2, c3 = st.columns([1.2, 1, 1, 1])
        c0.markdown(ring(score), unsafe_allow_html=True)
        c1.markdown(stat("Skills you have", (gap.status == "Have").sum(), delay=.1), unsafe_allow_html=True)
        c2.markdown(stat("Skills missing", (gap.status == "Missing").sum(), delay=.2), unsafe_allow_html=True)
        c3.markdown(stat("Weeks to close gap", plan["est_weeks"].sum() if not plan.empty else 0, delay=.3),
                    unsafe_allow_html=True)

        key = (role, tuple(sorted(student)))
        if score >= 80 and student and st.session_state.get("balloon") != key:
            st.balloons()
            st.session_state["balloon"] = key

        a, b = st.columns(2)
        a.markdown(f'<div class="glass"><b>You already have</b><br>{chips(gap, "Have")}</div>', unsafe_allow_html=True)
        b.markdown(f'<div class="glass"><b>You need to learn</b><br>{chips(gap, "Missing")}</div>', unsafe_allow_html=True)

        fig = px.bar(gap.sort_values("demand"), x="demand", y="skill", color="status", orientation="h",
                     color_discrete_map={"Have": "#2ecc71", "Missing": "#ff5252"},
                     labels={"demand": "Share of postings requiring skill"}, title=f"Skill demand for {role}")
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style(fig, max(380, 24 * len(gap))))

        st.subheader("📚 Your learning roadmap")
        st.markdown(roadmap(plan.head(15)) if not plan.empty else
                    '<div class="glass">🎉 You cover every in-demand skill for this role!</div>',
                    unsafe_allow_html=True)

# ---- Tab 2: best-fit roles
with tab2:
    if not student:
        st.info("👈 Add some skills in the sidebar to get role recommendations.")
    else:
        rec = recommend_roles(student, jobs, job_skills, top_n=8)
        st.markdown(role_cards(rec), unsafe_allow_html=True)

# ---- Tab 3: market insights
with tab3:
    m1, m2, m3 = st.columns(3)
    m1.markdown(stat("Job postings", len(jobs)), unsafe_allow_html=True)
    m2.markdown(stat("Tech roles", jobs["title"].nunique(), delay=.1), unsafe_allow_html=True)
    m3.markdown(stat("Skills tracked", len(SKILLS), delay=.2), unsafe_allow_html=True)

    top = query(TOP_SKILLS_SQL, (15,))
    x, y = st.columns(2)
    x.plotly_chart(style(px.bar(top.sort_values("postings"), x="postings", y="skill", orientation="h",
                                color="postings", color_continuous_scale="Viridis",
                                title="Most demanded skills")))
    cat = job_skills.groupby(["category", "skill"]).size().reset_index(name="mentions")
    y.plotly_chart(style(px.sunburst(cat, path=["category", "skill"], values="mentions",
                                     title="Skill categories")))

    dem = query(DEMAND_BY_ROLE_SQL)
    top_sk = dem.groupby("skill")["demand"].sum().nlargest(25).index
    pivot = dem[dem["skill"].isin(top_sk)].pivot(index="role", columns="skill", values="demand").fillna(0)
    st.plotly_chart(style(px.imshow(pivot, aspect="auto", color_continuous_scale="Viridis",
                                    title="Role × skill demand heatmap"), max(520, 24 * len(pivot))))
    st.plotly_chart(style(px.scatter(jobs, x="x", y="y", color="cluster_label", hover_data=["title", "company"],
                                     title="Job clusters by skill profile"), 520))

# ---- Tab 4: paste a job description
with tab4:
    jd = st.text_area("Paste any job description", height=220)
    if jd:
        res = analyze_job_description(jd, student)
        if res.empty:
            st.warning("No known skills detected in this description.")
        else:
            l, r = st.columns([1, 2])
            l.markdown(ring(readiness(res), "Match"), unsafe_allow_html=True)
            r.markdown(f'<div class="glass"><b>You have</b><br>{chips(res, "Have")}</div>'
                       f'<div class="glass"><b>You are missing</b><br>{chips(res, "Missing")}</div>',
                       unsafe_allow_html=True)
