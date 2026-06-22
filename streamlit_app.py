# -*- coding: utf-8 -*-
"""
年間指導計画・個別の指導計画 おたすけツール（ウェブ版 / Streamlit）
- 全員共通パスワードでアクセス制限
- 既存処理（nenkan_app.py）を再利用
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

# ---- 見やすさ用のスタイル ----
st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1100px;}
div[data-testid="stRadio"] label p {font-size: 0.95rem;}
.goalrow {background:#F7FAFF; border:1px solid #DCE6F2; border-radius:8px;
          padding:8px 12px; margin:6px 0; font-size:1.02rem; line-height:1.6;}
.goaltag {color:#8A8A8A; font-size:0.85rem;}
.pillar {background:#3A6B5C; color:white; padding:6px 12px; border-radius:6px;
         font-weight:700; margin-top:10px;}
.qcard {background:#FBFBF7; border:1px solid #E8E4D8; border-radius:8px;
        padding:6px 12px; margin:4px 0;}
</style>
""", unsafe_allow_html=True)


# ---------------- パスワード認証 ----------------
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


def stage_label(bu, subj, s):
    sub = data[bu][subj]
    keys = sub["stages"]
    labs = sub.get("stage_labels", keys)
    return labs[keys.index(s)] if s in keys else s


# ---------------- 結果表示 ----------------
def render_goals(goals3, subj_used, bu_used, stage_used):
    # 編集ウィジェットの値を goals3 に反映
    for pillar in PILLARS:
        for i, it in enumerate(goals3.get(pillar, [])):
            k = f"ta_{pillar}_{i}"
            if k in st.session_state:
                it["text"] = st.session_state[k]

    st.success(f"推定段階：**{stage_label(bu_used, subj_used, stage_used)}**　"
               f"（{subj_used}・{bu_used}）　※下のアセスメントの回答から自動推定")
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
    st.caption("学部・教科を選び、かんたんアセスメント（3問）に答えると、"
               "段階を推定して3観点の目標案を作ります。")

    c1, c2 = st.columns(2)
    bu = c1.selectbox("学部", list(data.keys()), key="bu")
    subj = c2.selectbox("教科", list(data[bu].keys()), key="subj")

    stages = data[bu][subj]["stages"]
    assess = core.get_assess(subj, bu)
    focus = core.kobetsu_focus(data, bu, subj)
    focus_labels = [f[0] for f in focus]

    with st.form("kobetsu_form"):
        ans = None
        manual_stage = None
        if assess:
            st.markdown("**① かんたんアセスメント（3問）**　当てはまるものを選んでください")
            ans = []
            for i, qd in enumerate(assess):
                st.markdown(f"<div class='qcard'>Q{i + 1}. {qd['q']}</div>",
                            unsafe_allow_html=True)
                choice = st.radio(f"Q{i + 1}", list(ANS_MAP.keys()), horizontal=True,
                                  index=0, key=f"q_{bu}_{subj}_{i}",
                                  label_visibility="collapsed")
                ans.append(ANS_MAP[choice])
        else:
            st.markdown("**① 段階を選択**（この教科はアセスメント未対応です）")
            manual_stage = st.selectbox("段階", stages,
                                        format_func=lambda s: stage_label(bu, subj, s))

        st.markdown("**② 重視する領域（1つ以上）**")
        chosen = st.multiselect("領域", focus_labels,
                                default=focus_labels[:2], label_visibility="collapsed")
        submitted = st.form_submit_button("個別の指導計画をつくる", type="primary",
                                          use_container_width=True)

    if submitted:
        if not chosen:
            st.warning("重視する領域を1つ以上選んでください。")
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
