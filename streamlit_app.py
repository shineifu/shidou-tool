# -*- coding: utf-8 -*-
"""
年間指導計画・個別の指導計画 おたすけツール（ウェブ版 / Streamlit）
- 全員共通パスワードでアクセス制限
- 既存の処理（nenkan_app.py）をそのまま再利用
- まずは「個別の指導計画」を実装（生活単元・各教科は順次追加）
"""
import os
import tempfile
import streamlit as st
import nenkan_app as core

st.set_page_config(page_title="個別の指導計画作成ツール",
                   page_icon="📋", layout="wide")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PILLARS = ["知識及び技能", "思考力，判断力，表現力等", "学びに向かう力，人間性等"]


# ---------------- パスワード認証 ----------------
def _correct_password():
    try:
        return st.secrets["APP_PASSWORD"]
    except Exception:
        # ローカル動作用の予備。公開時は Secrets に APP_PASSWORD を設定してください。
        return os.environ.get("APP_PASSWORD", "shien2026")


def require_password():
    if st.session_state.get("auth_ok"):
        return
    st.title("年間指導計画・個別の指導計画 おたすけツール")
    st.caption("ご利用にはパスワードが必要です。")

    def _check():
        st.session_state["auth_ok"] = (
            st.session_state.get("pw_input", "") == _correct_password())

    st.text_input("パスワード", type="password", key="pw_input", on_change=_check)
    if "auth_ok" in st.session_state and not st.session_state["auth_ok"]:
        st.error("パスワードが違います。")
    st.stop()


require_password()


# ---------------- データ ----------------
@st.cache_data
def get_data():
    return core.load_data()


data = get_data()


# ---------------- 個別の指導計画 ----------------
def kobetsu_page():
    st.header("個別の指導計画作成ツール")
    st.caption("学部・教科・段階・重視する領域を選んで「つくる」を押すと、3観点の目標案を作成します。")

    c1, c2, c3 = st.columns(3)
    bu = c1.selectbox("学部", list(data.keys()))
    subj = c2.selectbox("教科", list(data[bu].keys()))
    stages = data[bu][subj]["stages"]
    labels = data[bu][subj].get("stage_labels", stages)

    def stage_label(s):
        return labels[stages.index(s)] if s in stages else s

    stage = c3.selectbox("段階", stages, format_func=stage_label)

    focus = core.kobetsu_focus(data, bu, subj)
    focus_labels = [f[0] for f in focus]
    chosen = st.multiselect("重視する領域（1つ以上）", focus_labels,
                            default=focus_labels[:2])

    if st.button("個別の指導計画をつくる", type="primary"):
        if not chosen:
            st.warning("重視する領域を1つ以上選んでください。")
        else:
            ryos = [r for (lab, rl) in focus if lab in chosen for r in rl]
            st.session_state["goals3"] = core.kobetsu_generate(data, bu, subj, stage, ryos)
            st.session_state["k_subj"] = subj
            # 旧い編集ウィジェットの値をクリア
            for k in list(st.session_state.keys()):
                if k.startswith("ta_"):
                    del st.session_state[k]

    goals3 = st.session_state.get("goals3")
    if not goals3:
        return

    st.divider()
    edit_mode = st.toggle("✏ 編集する（文章を手入力で書き換え）", value=False)

    for pillar in PILLARS:
        st.subheader(pillar)
        items = goals3.get(pillar, [])
        if not items:
            st.write("―")
            continue
        for i, it in enumerate(items):
            tag = f"（{it['bu']}{it['stage']}段階）" if it.get("bu") else ""
            key = f"ta_{pillar}_{i}"
            if key not in st.session_state:
                st.session_state[key] = it["text"]
            if edit_mode:
                cc = st.columns([9, 1])
                cc[0].text_area(tag or "目標", key=key, height=70,
                                label_visibility="collapsed")
                it["text"] = st.session_state[key]
            else:
                cc = st.columns([9, 1])
                cc[0].markdown(f"・{st.session_state[key]}　<span style='color:#888'>{tag}</span>",
                               unsafe_allow_html=True)
                it["text"] = st.session_state[key]
                if it.get("ryoiki"):
                    if cc[1].button("別の案", key=f"alt_{pillar}_{i}"):
                        goals3[pillar][i] = core.goal_next_alt(data, it)
                        st.session_state.pop(key, None)
                        st.rerun()

    st.divider()
    subj_now = st.session_state.get("k_subj", subj)
    d1, d2 = st.columns(2)
    with tempfile.TemporaryDirectory() as td:
        wp = os.path.join(td, "k.docx")
        xp = os.path.join(td, "k.xlsx")
        core.export_kobetsu_word(subj_now, goals3, wp)
        core.export_kobetsu_excel(subj_now, goals3, xp)
        with open(wp, "rb") as f:
            d1.download_button("📄 Wordで出力", f.read(),
                               file_name=f"個別の指導計画_{subj_now}.docx", mime=DOCX_MIME)
        with open(xp, "rb") as f:
            d2.download_button("📊 Excelで出力", f.read(),
                               file_name=f"個別の指導計画_{subj_now}.xlsx", mime=XLSX_MIME)


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
