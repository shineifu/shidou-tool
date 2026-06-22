# -*- coding: utf-8 -*-
"""
指導計画 おたすけツール（ウェブ版 / Streamlit）
- 全員共通パスワードでアクセス制限
- 個別の指導計画：かんたんアセスメント（3問）→段階推定→3観点の目標案
"""
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

# 学部の並び順（小→中→高）
BU_ORDER = ["小学部", "中学部", "高等部"]
# 教科の並び順（学習指導要領の掲載順／学部別）
SUBJECT_ORDER = {
    "小学部": ["生活科", "国語科", "算数科", "音楽科", "図画工作科", "体育科"],
    "中学部": ["国語科", "社会科", "数学科", "理科", "音楽科", "美術科",
              "保健体育科", "職業家庭科", "外国語科"],
    "高等部": ["国語科", "社会科", "数学科", "理科", "音楽科", "美術科",
              "保健体育科", "家庭科", "外国語科", "職業科"],
}

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1080px;}
.pillar {background:#3A6B5C; color:white; padding:6px 12px; border-radius:6px;
         font-weight:700; margin-top:12px; font-size:1.05rem;}
.goalrow {background:#F7FAFF; border:1px solid #DCE6F2; border-radius:8px;
          padding:9px 13px; margin:6px 0; font-size:1.03rem; line-height:1.65;}
.goaltag {color:#8A8A8A; font-size:0.85rem;}
.qcard {background:#FBFBF7; border:1px solid #E8E4D8; border-radius:8px;
        padding:8px 12px; margin:6px 0 2px 0; font-weight:600;}
.sec {font-weight:700; color:#3A6B5C; font-size:1.05rem; margin:2px 0 6px 0;}
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
    st.title("指導計画 おたすけツール")
    st.caption("ご利用にはパスワードが必要です。")

    def _check():
        st.session_state["auth_ok"] = (
            st.session_state.get("pw_input", "") == _correct_password())

    st.text_input("パスワード", type="password", key="pw_input", on_change=_check)
    if "auth_ok" in st.session_state and not st.session_state["auth_ok"]:
        st.error("パスワードが違います。")
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
    subs = list(data[bu].keys())
    return sorted(subs, key=lambda s: order.index(s) if s in order else 999)


def stage_label(bu, subj, s):
    sub = data[bu][subj]
    keys = sub["stages"]
    labs = sub.get("stage_labels", keys)
    return labs[keys.index(s)] if s in keys else s


# ---------------- 結果表示 ----------------
def render_goals(goals3, subj_used, bu_used, stage_used):
    for pillar in PILLARS:
        for i, it in enumerate(goals3.get(pillar, [])):
            k = f"ta_{pillar}_{i}"
            if k in st.session_state:
                it["text"] = st.session_state[k]

    st.success(f"推定段階：**{stage_label(bu_used, subj_used, stage_used)}**"
               f"　（{bu_used}・{subj_used}）")
    edit = st.toggle("✏ 編集する（文章を手入力で修正）", value=False, key="k_edit")

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
            if k not in st.session_state:
                st.session_state[k] = it["text"]
            if edit:
                st.text_area(tag or "目標", key=k, height=80)
                it["text"] = st.session_state[k]
            else:
                c1, c2 = st.columns([9, 1])
                c1.markdown(
                    f"<div class='goalrow'>・{st.session_state[k]} "
                    f"<span class='goaltag'>{tag}</span></div>",
                    unsafe_allow_html=True)
                it["text"] = st.session_state[k]
                if it.get("ryoiki"):
                    if c2.button("別の案", key=f"alt_{pillar}_{i}"):
                        goals3[pillar][i] = core.goal_next_alt(data, it)
                        st.session_state.pop(k, None)
                        st.rerun()

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


# ---------------- 個別の指導計画ページ ----------------
def kobetsu_page():
    st.header("📋 個別の指導計画作成ツール")

    # ===== 選択エリア（枠で囲う）=====
    with st.container(border=True):
        st.markdown("<div class='sec'>① 学部・教科をえらぶ</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        bus = bu_options()
        bu = c1.selectbox("学部", bus, index=0, key="bu")   # 既定：小学部
        subs = ordered_subjects(bu)
        subj_default = subs.index("国語科") if "国語科" in subs else 0  # 既定：国語
        subj = c2.selectbox("教科", subs, index=subj_default, key=f"subj_{bu}")

    stages = data[bu][subj]["stages"]
    assess = core.get_assess(subj, bu)
    focus = core.kobetsu_focus(data, bu, subj)
    focus_labels = [f[0] for f in focus]

    with st.form("kobetsu_form", border=True):
        ans = None
        manual_stage = None
        if assess:
            st.markdown("<div class='sec'>② かんたんアセスメント（3問）</div>",
                        unsafe_allow_html=True)
            st.caption("お子さんの様子に近いものを選んでください。")
            ans = []
            for i, qd in enumerate(assess):
                st.markdown(f"<div class='qcard'>Q{i + 1}. {qd['q']}</div>",
                            unsafe_allow_html=True)
                choice = st.radio("回答", list(ANS_MAP.keys()), horizontal=True,
                                  index=0, key=f"q_{bu}_{subj}_{i}",
                                  label_visibility="collapsed")
                ans.append(ANS_MAP[choice])
        else:
            st.markdown("<div class='sec'>② 段階をえらぶ</div>", unsafe_allow_html=True)
            st.caption("この教科はアセスメント未対応のため、段階を直接選びます。")
            manual_stage = st.selectbox("段階", stages,
                                        format_func=lambda s: stage_label(bu, subj, s))

        st.markdown("<div class='sec'>③ 指導する領域（チェック／複数可）</div>",
                    unsafe_allow_html=True)
        chosen = []
        if focus_labels:
            ncol = 3
            cols = st.columns(ncol)
            for i, lab in enumerate(focus_labels):
                with cols[i % ncol]:
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


# ---------------- メニュー ----------------
st.sidebar.title("メニュー")
st.sidebar.success("ログイン中")
mode = st.sidebar.radio("作成するもの",
                        ["個別の指導計画", "年間指導計画（準備中）", "生活単元学習（準備中）"])
if st.sidebar.button("ログアウト"):
    st.session_state.clear()
    st.rerun()

if mode == "個別の指導計画":
    kobetsu_page()
else:
    st.header(mode.replace("（準備中）", ""))
    st.info("この機能はウェブ版に順次移行します。まず個別の指導計画からご利用ください。")
