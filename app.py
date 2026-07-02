"""
app.py — 國立臺北教育大學教務處法規知識庫助理
RAG 架構：LangChain + FAISS + GPT-4o-mini
"""

from pathlib import Path
from dotenv import load_dotenv

import streamlit as st
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
# from langchain.chains import ConversationalRetrievalChain
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

load_dotenv()

INDEX_DIR = Path("faiss_index")
TOP_K     = 5
WINDOW_K  = 5

# icon 改用 emoji，清晰且不依賴外部字型
QUICK_QUESTIONS = {
    "student": {
        "label": "在校學生",
        "icon": "🎓",
        "questions": [
            "如何申請停修課程？",
            "輔系與雙主修怎麼辦理？",
            "延畢需要什麼條件？",
            "學分抵免怎麼申請？",
            "校際選課如何辦理？",
        ],
    },
    "staff": {
        "label": "教職人員／行政",
        "icon": "🏛️",
        "questions": [
            "教師評鑑的評鑑準則為何？",
            "教師升等審查的程序？",
            "教學優良獎的評選辦法？",
            "論文原創性比對聲明書何時實施？",
        ],
    },
    "applicant": {
        "label": "考生／準新生",
        "icon": "📝",
        "questions": [
            "心理與諮商學系碩士班考哪些科目？",
            "數學暨資訊教育學系碩士班考科？",
            "新生如何申請保留入學資格？",
            "轉學生可以申請哪些系？",
        ],
    },
    "graduate": {
        "label": "研究生",
        "icon": "📚",
        "questions": [
            "學位考試如何申請？",
            "論文指導費與口試費怎麼支給？",
            "學術倫理時數何時需要繳交？",
            "論文可以申請延後公開嗎？",
        ],
    },
}

SYSTEM_PROMPT = """你是「國立臺北教育大學（NTUE）教務處數位法規助理」。

【核心原則】
1. 只根據下方「參考法規段落」的內容回答，禁止自行推測或補充段落中未出現的資訊。
2. 回答中不需標註任何來源或出處。
3. 若段落無法完整回答，說明「本系統資料未涵蓋此項目」，建議致電 (02)2732-1104。
4. 使用繁體中文，語氣親切專業。
5. 條列式回答，字數 500 字內。

【參考法規段落】
{context}

【回答】"""


@st.cache_resource(show_spinner=False)
def load_chain():
    if not INDEX_DIR.exists():
        return None, None
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.load_local(
        str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": TOP_K, "fetch_k": 20, "lambda_mult": 0.7},
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=800)
    
    # 建立適合新版 RAG 的 ChatPrompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    # 明確定義記憶體
    memory = ConversationBufferWindowMemory(
        k=WINDOW_K, memory_key="chat_history",
        return_messages=True, output_key="answer",
    )
    
    # 建立新版文檔鏈與檢索鏈
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # 【關鍵修正】同時回傳 chain 與 memory，不要用外掛屬性的方式
    return chain, memory


def format_sources(source_docs: list) -> str:
    seen, lines = set(), []
    for doc in source_docs:
        meta   = doc.metadata
        source = meta.get("source", "未知來源")
        page   = meta.get("page", "")
        key    = f"{source}-{page}"
        if key in seen:
            continue
        seen.add(key)
        label = source
        if page:
            label += f"　第 {page} 頁"
        lines.append(label)
    return lines  # 回傳 list，由呼叫方決定渲染方式


# ── 頁面設定 ────────────────────────────────────────
st.set_page_config(
    page_title="教務處法規助理｜國立臺北教育大學",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── CSS：用 st.markdown 注入（相容所有 Streamlit 版本）──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Noto Sans TC', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 780px !important; }
[data-testid="collapsedControl"] { display: flex !important; visibility: visible !important; opacity: 1 !important; }

/* Header */
.ntue-header {
    display: flex; align-items: center; gap: 1rem;
    padding: 1.2rem 1.5rem; background: #0f2d6b;
    border-radius: 12px; margin-bottom: 1.2rem;
    border-bottom: 3px solid #c8a400;
}
.ntue-badge {
    width: 46px; height: 46px; background: #c8a400;
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 22px; flex-shrink: 0;
}
.ntue-title h1 { font-size: 1.1rem; font-weight: 700; color: #fff; margin: 0 0 3px; }
.ntue-title p  { font-size: 0.76rem; color: #a8bcd8; margin: 0; }

/* Role tabs */
.role-tabs { display: flex; gap: 8px; margin-bottom: 1rem; flex-wrap: wrap; }
.role-tab {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 8px;
    border: 1.5px solid #dde3ed; background: #f8f9fc;
    font-size: 0.82rem; font-weight: 500; color: #5a6a85;
}
.role-tab.active { background: #0f2d6b; color: #fff; border-color: #0f2d6b; }

/* Tab 按鈕容器 */
div[data-testid="stHorizontalBlock"] { gap: 6px !important; }

/* Tab 按鈕：未選中 */
.tab-btn button {
    background: #f8f9fc !important;
    border: 1.5px solid #dde3ed !important;
    color: #5a6a85 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 7px 4px !important;
    width: 100% !important;
}
/* Tab 按鈕：選中 */
.tab-btn-active button {
    background: #0f2d6b !important;
    border: 1.5px solid #0f2d6b !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 7px 4px !important;
    width: 100% !important;
}

/* Quick label */
.quick-label {
    font-size: 0.72rem; color: #9ca3af; font-weight: 600;
    letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 8px;
}

/* Quick buttons */
div[data-testid="column"] button {
    background: #f0f4ff !important; border: 1.5px solid #d0d9f0 !important;
    color: #2b4a9e !important; border-radius: 8px !important;
    font-size: 0.78rem !important; font-weight: 500 !important;
    padding: 6px 10px !important; white-space: normal !important;
    height: 64px !important; line-height: 1.4 !important;
    display: flex !important; align-items: center !important;
    justify-content: center !important; text-align: center !important;
}
div[data-testid="column"] button:hover {
    background: #dde6ff !important; border-color: #2b4a9e !important;
}
div[data-testid="column"] button p {
    margin: 0 !important; white-space: normal !important;
}

/* Source box */
.source-box {
    background: #f5f7ff; border: 1px solid #d8e0f5;
    border-left: 3px solid #0f2d6b; padding: 8px 12px;
    border-radius: 0 8px 8px 0; font-size: 0.76rem;
    color: #4a5568; margin-top: 8px;
}
.source-box .source-title { font-weight: 600; margin-bottom: 4px; color: #0f2d6b; }
.source-box .source-line { padding: 2px 0; border-bottom: 1px solid #e8edf8; }
.source-box .source-line:last-child { border-bottom: none; }

/* Sidebar */
[data-testid="stSidebar"] { background: #f8f9fc !important; }
.sb-title {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #9ca3af; margin-bottom: 8px;
}
.contact-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 5px 0; border-bottom: 1px solid #edf0f7; font-size: 0.82rem;
}
.contact-row:last-child { border-bottom: none; }
.contact-ext { color: #0f2d6b; font-weight: 700; }

hr { border-color: #e8ecf4 !important; margin: 0.8rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────
st.markdown("""
<div class="ntue-header">
    <div class="ntue-badge">🏫</div>
    <div class="ntue-title">
        <h1>國立臺北教育大學 教務處法規助理</h1>
        <p>查詢學則、法規與辦理流程，每則回答均標註官方來源</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────
for key, val in [("messages", []), ("selected_role", "student"), ("pending_input", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── 身份切換（st.button Tab）─────────────────────────
role_keys = list(QUICK_QUESTIONS.keys())
tab_cols  = st.columns(len(role_keys))
for i, (k, v) in enumerate(QUICK_QUESTIONS.items()):
    is_active = (k == st.session_state.selected_role)
    css_class = "tab-btn-active" if is_active else "tab-btn"
    with tab_cols[i]:
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        if st.button(f'{v["icon"]} {v["label"]}', key=f"tab_{k}", use_container_width=True):
            st.session_state.selected_role = k
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

role = st.session_state.selected_role

# ── 快速提問 ──────────────────────────────────────
st.markdown('<div class="quick-label">⚡ 快速提問</div>', unsafe_allow_html=True)
qs   = QUICK_QUESTIONS[role]["questions"]
cols = st.columns(len(qs))
for i, q in enumerate(qs):
    if cols[i].button(q, key=f"q_{role}_{i}", use_container_width=True):
        st.session_state.pending_input = q

st.divider()

# ── 載入 RAG 鏈 ───────────────────────────────────
with st.spinner("載入知識庫中..."):
    chain, memory = load_chain()

if chain is None:
    st.error("尚未建立向量索引，請先執行：python build_index.py")
    st.stop()

# ── 歷史對話 ──────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── 輸入處理 ──────────────────────────────────────
user_input = st.chat_input("輸入問題，例如：如何申請轉系？") or st.session_state.pending_input
if st.session_state.pending_input:
    st.session_state.pending_input = None

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("查閱法規資料庫中..."):
            try:
                # 【關鍵修正】直接從獨立的 memory 物件載入對話紀錄
                memory_vars = memory.load_memory_variables({})
                chat_history = memory_vars.get("chat_history", [])

                # 呼叫時，傳入 input 與 chat_history
                result  = chain.invoke({
                    "input": user_input,
                    "chat_history": chat_history
                })
                answer  = result["answer"]
                sources = format_sources(result.get("context", []))
                
                # 【關鍵修正】直接呼叫獨立的 memory 物件儲存對話上下文
                memory.save_context(
                    {"input": user_input}, 
                    {"answer": answer}
                )
                
                st.markdown(answer)

                if sources:
                    with st.expander("📄 檢視官方參考法規來源"):
                        for src in sources:
                            st.write(f"• {src}")

                st.session_state.messages.append({
                    "role": "assistant", "content": answer
                })
            except Exception as e:
                st.error("系統發生錯誤，請稍後再試或致電 (02)2732-1104")
                print(f"[ERROR] {e}")

# ── 側邊欄 ────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-title">📞 聯絡資訊</div>', unsafe_allow_html=True)
    st.markdown("""
<div style="font-size:0.8rem;color:#374151;margin-bottom:8px">
    <strong>總機</strong>：(02) 2732-1104<br>
    <span style="color:#9ca3af;font-size:0.73rem">週一至週五 08:30–17:30</span>
</div>
""", unsafe_allow_html=True)

    contacts = [
        ("教務長室",     "82011"),
        ("招生與宣傳組", "82221"),
        ("註冊組",       "82231"),
        ("課務組",       "82016"),
        ("華語文中心",   "82025"),
    ]
    rows = "".join(
        f'<div class="contact-row">'
        f'<span>{n}</span>'
        f'<span class="contact-ext">分機 {e}</span></div>'
        for n, e in contacts
    )
    st.markdown(f'<div style="margin-bottom:1rem">{rows}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-title">🔗 常用系統</div>', unsafe_allow_html=True)
    for label, url in [
        ("iNTUE 校務系統",  "https://nsa.ntue.edu.tw/"),
        ("Moodle 教學平台", "https://md.ntue.edu.tw/"),
        ("校園入口網",       "https://protocol.ntue.edu.tw/"),
        ("計算機中心",       "https://cc.ntue.edu.tw/"),
    ]:
        st.markdown(
            f'<a href="{url}" target="_blank" style="display:block;padding:7px 10px;margin-bottom:4px;'
            f'border-radius:8px;background:#f0f4ff;color:#0f2d6b;font-size:0.82rem;'
            f'font-weight:500;text-decoration:none">🔗 {label}</a>',
            unsafe_allow_html=True,
        )

    st.divider()
    if st.button("🗑️ 清除對話紀錄", use_container_width=True):
        st.session_state.messages = []
        # 【關鍵修正】直接對 memory 進行 clear
        if memory:
            memory.clear()
        st.rerun()

    st.markdown(
        '<div style="font-size:0.7rem;color:#9ca3af;margin-top:0.5rem;line-height:1.6">'
        '回答依官方法規生成，如有疑義請以原始文件為準。</div>',
        unsafe_allow_html=True,
    )
