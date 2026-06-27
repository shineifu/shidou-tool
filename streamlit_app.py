# -*- coding: utf-8 -*-
"""指導計画 おたすけツール（ウェブ版 / Streamlit）"""
import os
import tempfile
import streamlit as st
import nenkan_app as core

st.set_page_config(page_title="指導計画 おたすけツール", page_icon="📋", layout="wide")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PILLARS = ["知識及び技能", "思考力，判断力，表現力等", "学びに向かう力，人間性等"]
PILLAR_LABELS = {"知識及び技能": "知識及び技能",
                 "思考力，判断力，表現力等": "思考力・判断力・表現力等",
                 "学びに向かう力，人間性等": "学びに向かう力・人間性等"}
ANS_MAP = {"はい": 2, "だいたい": 1, "いいえ": 0}
BU_ORDER = ["小学部", "中学部", "高等部"]
SUBJECT_ORDER = {
    "小学部": ["生活科", "国語科", "算数科", "音楽科", "図画工作科", "体育科"],
    "中学部": ["国語科", "社会科", "数学科", "理科", "音楽科", "美術科",
              "保健体育科", "職業家庭科", "外国語科"],
    "高等部": ["国語科", "社会科", "数学科", "理科", "音楽科", "美術科",
              "保健体育科", "家庭科", "外国語科", "職業科"],
}
PERIOD_LABELS = {1: "1か月ごと（年12単元）", 2: "2か月ごと（年6単元）", 3: "3か月ごと（年4単元）"}

st.markdown("""
<style>
/* 開発者向けメニュー・ヘッダーを隠してすっきり見せる */
#MainMenu {visibility:hidden;}
header[data-testid="stHeader"] {display:none !important;}
[data-testid="stToolbar"] {display:none !important;}
[data-testid="stDecoration"] {display:none !important;}
footer {visibility:hidden;}
.block-container {padding-top: 2rem; max-width: 1080px;}
.pillar {background:#3A6B5C; color:white; padding:7px 13px; border-radius:6px;
         font-weight:700; margin-top:12px; font-size:1.05rem;}
.goalrow {background:#F7FAFF; border:1px solid #DCE6F2; border-radius:8px;
          padding:9px 13px; margin:6px 0; font-size:1.03rem; line-height:1.65;}
.goaltag {color:#8A8A8A; font-size:0.85rem;}
.qcard {background:#FBFBF7; border:1px solid #E8E4D8; border-radius:8px;
        padding:8px 12px; margin:6px 0 2px 0; font-weight:600;}
.sec {font-weight:700; color:#3A6B5C; font-size:1.05rem; margin:2px 0 6px 0;}
.homecard {background:#F4F7F5; border:1px solid #D6E2DB; border-radius:12px;
           padding:18px 20px; margin:10px 0;}
.homecard h3 {margin:0 0 6px 0; color:#2f5749;}
div[data-testid="stFormSubmitButton"] button,
div.stButton > button[kind="primary"] {
    background-color:#3A6B5C !important; border-color:#3A6B5C !important; color:#fff !important;}
div[data-testid="stFormSubmitButton"] button:hover,
div.stButton > button[kind="primary"]:hover {
    background-color:#2f5749 !important; border-color:#2f5749 !important; color:#fff !important;}
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
    border:2px solid #BFD3C8 !important; border-radius:8px !important; background:#FFF !important;}
div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
    border-color:#3A6B5C !important;}
</style>
""", unsafe_allow_html=True)


def _correct_password():
    try:
        return st.secrets["APP_PASSWORD"]
    except Exception:
        return os.environ.get("APP_PASSWORD", "shien2026")


def require_password():
    if st.session_state.get("auth_ok"):
        return
    st.title("📋 指導計画 おたすけツール")
    mid = st.columns([1, 2, 1])[1]
    with mid:
        with st.container(border=True):
            st.markdown("#### 🔑 合言葉を入力してください")
            st.caption("このツールを使うには、合言葉（パスワード）が必要です。"
                       "下の枠に入力して「ログイン」を押してください。")
            pw = st.text_input("合言葉", type="password",
                               placeholder="ここに合言葉を入力",
                               key="pw_input", label_visibility="collapsed")
            if st.button("ログイン", type="primary", use_container_width=True):
                if pw == _correct_password():
                    st.session_state["auth_ok"] = True
                    st.rerun()
                else:
                    st.error("合言葉が違います。もう一度お試しください。")
    st.stop()


require_password()


@st.cache_data
def get_data():
    return core.load_data()


data = get_data()


def bu_options():
    return [b for b in BU_ORDER if b in data] or list(data.keys())


def ordered_subjects(bu):
    order = SUBJECT_ORDER.get(bu, [])
    return sorted(data[bu].keys(),
                  key=lambda s: order.index(s) if s in order else 999)


def stage_label(bu, subj, s):
    sub = data[bu][subj]
    keys = sub["stages"]
    labs = sub.get("stage_labels", keys)
    return labs[keys.index(s)] if s in keys else s


# ===================== ホーム =====================
def home_page():
    st.header("📋 指導計画 おたすけツール")
    st.write("特別支援学校（知的障害）向けに、個別の指導計画や年間指導計画づくりを"
             "お手伝いするツールです。左のメニューから使いたいものを選んでください。")
    st.markdown("""
    <div class='homecard'><h3>📋 個別の指導計画</h3>
    学部・教科を選び、かんたんアセスメント（3問）に答えると、段階を推定して
    3観点（知識・技能／思考・判断・表現／学びに向かう力）の目標案を作成します。</div>
    <div class='homecard'><h3>📅 生活単元学習（年間）</h3>
    学部・段階・期間・合わせる教科を選ぶと、1年分の生活単元（大単元・小単元）を
    自動で配置します。Word・Excelで出力できます。</div>
    <div class='homecard'><h3>📚 各教科の年間計画（準備中）</h3>
    各教科の年間指導計画づくり。ウェブ版に順次移行します。</div>
    """, unsafe_allow_html=True)


# ===================== 個別の指導計画 =====================
def render_goals(goals3, subj_used, bu_used, stage_used):
    st.markdown(
        "<div style='background:#EAF4EE;border:1px solid #BFE0CC;border-radius:10px;"
        "padding:16px 20px;margin:4px 0 10px 0;'>"
        f"<div style='font-size:1.5rem;font-weight:800;color:#2f5749;'>"
        f"推定段階：{stage_label(bu_used, subj_used, stage_used)}</div>"
        f"<div style='color:#555;margin-top:6px;font-size:0.95rem;line-height:1.6;'>"
        f"（{bu_used}・{subj_used}）この段階を想定して目標案を作成しています。<br>"
        "実際のお子さんの様子とは異なる場合もありますので、<b>参考程度</b>にご覧いただき、"
        "必要に応じて段階や文章を調整してください。</div></div>", unsafe_allow_html=True)

    edit = st.toggle("✏ 編集する（文章を手入力で修正）", value=False, key="k_edit")

    def _replace(pillar, i, new_item, k):
        goals3[pillar][i] = new_item
        st.session_state.pop(k, None)
        st.rerun()

    for pillar in PILLARS:
        st.markdown(f"<div class='pillar'>{PILLAR_LABELS[pillar]}</div>",
                    unsafe_allow_html=True)
        items = goals3.get(pillar, [])
        if not items:
            st.caption("該当なし")
            continue
        for i, it in enumerate(items):
            tag = f"（{it['bu']}{it['stage']}段階）" if it.get("bu") else ""
            k = f"ta_{pillar}_{i}"
            if edit:
                if k not in st.session_state:
                    st.session_state[k] = it["text"]
                st.text_area(tag or "目標", key=k, height=80)
                it["text"] = st.session_state[k]
            else:
                c1, c2, c3, c4 = st.columns([7, 1, 1, 1])
                c1.markdown(f"<div class='goalrow'>・{it['text']} "
                            f"<span class='goaltag'>{tag}</span></div>",
                            unsafe_allow_html=True)
                if it.get("ryoiki"):
                    if c2.button("別の案", key=f"alt_{pillar}_{i}", use_container_width=True):
                        _replace(pillar, i, core.goal_next_alt(data, it), k)
                if not it.get("manabi"):
                    if c3.button("段階▲", key=f"up_{pillar}_{i}", use_container_width=True):
                        ni, msg = core.goal_change_stage(data, it, 1)
                        st.toast(msg) if msg else _replace(pillar, i, ni, k)
                    if c4.button("段階▼", key=f"dn_{pillar}_{i}", use_container_width=True):
                        ni, msg = core.goal_change_stage(data, it, -1)
                        st.toast(msg) if msg else _replace(pillar, i, ni, k)

    st.divider()
    d1, d2 = st.columns(2)
    with tempfile.TemporaryDirectory() as td:
        wp = os.path.join(td, "k.docx")
        xp = os.path.join(td, "k.xlsx")
        core.export_kobetsu_word(subj_used, goals3, wp)
        core.export_kobetsu_excel(subj_used, goals3, xp)
        with open(wp, "rb") as f:
            d1.download_button("📄 Wordで出力", f.read(),
                               file_name=f"個別の指導計画_{subj_used}.docx",
                               mime=DOCX_MIME, use_container_width=True)
        with open(xp, "rb") as f:
            d2.download_button("📊 Excelで出力", f.read(),
                               file_name=f"個別の指導計画_{subj_used}.xlsx",
                               mime=XLSX_MIME, use_container_width=True)


def kobetsu_page():
    st.header("📋 個別の指導計画作成ツール")
    with st.container(border=True):
        st.markdown("<div class='sec'>① 学部・教科をえらぶ</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        bu = c1.selectbox("学部", bu_options(), index=0, key="bu")
        subs = ordered_subjects(bu)
        sd = subs.index("国語科") if "国語科" in subs else 0
        subj = c2.selectbox("教科", subs, index=sd, key=f"subj_{bu}")

    stages = data[bu][subj]["stages"]
    assess = core.get_assess(subj, bu)
    focus = core.kobetsu_focus(data, bu, subj)
    focus_labels = [f[0] for f in focus]

    with st.form("kobetsu_form", border=True):
        ans, manual_stage = None, None
        if assess:
            st.markdown("<div class='sec'>② かんたんアセスメント（3問）</div>", unsafe_allow_html=True)
            st.caption("お子さんの様子に近いものを選んでください。")
            ans = []
            for i, qd in enumerate(assess):
                st.markdown(f"<div class='qcard'>Q{i + 1}. {qd['q']}</div>", unsafe_allow_html=True)
                ans.append(ANS_MAP[st.radio("回答", list(ANS_MAP.keys()), horizontal=True,
                                            index=0, key=f"q_{bu}_{subj}_{i}",
                                            label_visibility="collapsed")])
        else:
            st.markdown("<div class='sec'>② 段階をえらぶ</div>", unsafe_allow_html=True)
            manual_stage = st.selectbox("段階", stages,
                                        format_func=lambda s: stage_label(bu, subj, s))
        st.markdown("<div class='sec'>③ 指導する領域（チェック／複数可）</div>", unsafe_allow_html=True)
        chosen = []
        if focus_labels:
            cols = st.columns(3)
            for i, lab in enumerate(focus_labels):
                with cols[i % 3]:
                    if st.checkbox(lab, value=(i < 2), key=f"ryo_{bu}_{subj}_{i}"):
                        chosen.append(lab)
        else:
            st.caption("この教科には選べる領域がありません。")
        st.write("")
        submitted = st.form_submit_button("✅ 個別の指導計画をつくる",
                                          type="primary", use_container_width=True)

    if submitted:
        if not chosen:
            st.warning("「③ 指導する領域」を1つ以上チェックしてください。")
        else:
            stage = core.estimate_stage(subj, ans, stages) if ans is not None else manual_stage
            ryos = [r for (lab, rl) in focus if lab in chosen for r in rl]
            st.session_state["goals3"] = core.kobetsu_generate(data, bu, subj, stage, ryos)
            st.session_state["used"] = (subj, bu, stage)
            for kk in list(st.session_state.keys()):
                if kk.startswith("ta_"):
                    del st.session_state[kk]

    goals3 = st.session_state.get("goals3")
    if goals3 and st.session_state.get("used"):
        st.divider()
        su, bb, sg = st.session_state["used"]
        render_goals(goals3, su, bb, sg)


# ===================== 生活単元学習（年間） =====================
def render_seikatsu(plan, bu, stage, subjects, period):
    for (mlabel, theme, detail) in plan:
        st.markdown(f"<div class='pillar'>【{mlabel}】 "
                    f"{core.theme_display_name(theme['name'], bu)}</div>",
                    unsafe_allow_html=True)
        subs_idx = theme.get("_subs")
        subs = (core.get_subunits(theme["name"], bu, stage, indices=subs_idx)
                if subs_idx is not None else
                core.get_subunits(theme["name"], bu, stage, core.subunit_limit(period)))
        for si, su in enumerate(subs, 1):
            with st.container(border=True):
                st.markdown(f"**小単元{si}　{su['title']}**　"
                            f"<span style='color:#666'>{su['activity']}</span>",
                            unsafe_allow_html=True)
                lines = []
                for subj, items in su["subjects"].items():
                    msubj = core.map_subunit_subj(bu, subj)
                    if msubj not in subjects:
                        continue
                    for it in items:
                        ryo = core.map_subunit_ryoiki(bu, it["領域"])
                        lines.append(f"- **{msubj.replace('科', '')}**〔{ryo}〕{it['学習']}")
                st.markdown("\n".join(lines) if lines else "（選択教科に該当なし）")

    st.divider()
    d1, d2 = st.columns(2)
    with tempfile.TemporaryDirectory() as td:
        wp = os.path.join(td, "s.docx")
        xp = os.path.join(td, "s.xlsx")
        core.export_seikatsu_word(data, bu, stage, subjects, plan, wp, period)
        core.export_seikatsu_excel(data, bu, stage, subjects, plan, xp, period)
        with open(wp, "rb") as f:
            d1.download_button("📄 Wordで出力", f.read(),
                               file_name="生活単元学習_年間指導計画.docx",
                               mime=DOCX_MIME, use_container_width=True)
        with open(xp, "rb") as f:
            d2.download_button("📊 Excelで出力", f.read(),
                               file_name="生活単元学習_年間指導計画.xlsx",
                               mime=XLSX_MIME, use_container_width=True)


def seikatsu_page():
    st.header("📅 生活単元学習　年間指導計画")
    with st.container(border=True):
        st.markdown("<div class='sec'>① 学部・段階・期間</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        bu = c1.selectbox("学部", bu_options(), index=0, key="s_bu")
        stages = data[bu]["国語科"]["stages"]
        stage = c2.selectbox("段階", stages,
                             format_func=lambda s: stage_label(bu, "国語科", s), key="s_stage")
        period = c3.selectbox("期間", [1, 2, 3], index=1,
                              format_func=lambda d: PERIOD_LABELS[d], key="s_period")
        st.markdown("<div class='sec'>② 合わせる教科（チェック／複数可）</div>", unsafe_allow_html=True)
        pool = core.seikatsu_subject_pool(bu)
        subjects = []
        if pool:
            cols = st.columns(min(4, len(pool)))
            for i, s in enumerate(pool):
                with cols[i % len(cols)]:
                    if st.checkbox(s.replace("科", ""), value=(i < 3), key=f"ssub_{bu}_{i}"):
                        subjects.append(s)

    if st.button("📅 年間計画をつくる", type="primary", use_container_width=True, key="s_gen"):
        if not subjects:
            st.warning("合わせる教科を1つ以上チェックしてください。")
        else:
            n_units = core.DURATIONS[period]
            themes, dur = core.seikatsu_arrange(bu, n_units)
            plan = []
            for i, th in enumerate(themes):
                ms = core.SCHOOL_MONTHS[i * dur]
                me = core.SCHOOL_MONTHS[i * dur + dur - 1]
                mlabel = f"{ms}月" if dur == 1 else f"{ms}月〜{me}月"
                th = dict(th)
                th["_subs"] = core.subunit_default_indices(th["name"], core.subunit_limit(period))
                detail = core.seikatsu_unit_detail(data, bu, stage, th, subjects)
                plan.append((mlabel, th, detail))
            st.session_state["s_plan"] = plan
            st.session_state["s_used"] = (bu, stage, list(subjects), period)

    plan = st.session_state.get("s_plan")
    if plan and st.session_state.get("s_used"):
        st.divider()
        bb, sg, subs2, pr2 = st.session_state["s_used"]
        render_seikatsu(plan, bb, sg, subs2, pr2)


# ===================== メニュー =====================
st.sidebar.title("メニュー")
st.sidebar.success("ログイン中")
mode = st.sidebar.radio("使うもの",
                        ["🏠 ホーム", "📋 個別の指導計画",
                         "📅 生活単元学習（年間）", "📚 各教科の年間計画（準備中）"])
if st.sidebar.button("ログアウト"):
    st.session_state.clear()
    st.rerun()

if mode == "🏠 ホーム":
    home_page()
elif mode == "📋 個別の指導計画":
    kobetsu_page()
elif mode == "📅 生活単元学習（年間）":
    seikatsu_page()
else:
    st.header("各教科の年間計画")
    st.info("この機能はウェブ版に順次移行します。今しばらくお待ちください。")
