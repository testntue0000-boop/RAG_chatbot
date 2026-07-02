"""
build_index.py — 預先建立 FAISS 向量庫
執行一次即可，之後 app.py 直接載入。

使用方式：
    python build_index.py

環境變數：
    OPENAI_API_KEY — 放在 .env 或 Render 環境設定
"""

import os, re
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import pdfplumber

load_dotenv()

# ── 設定 ──────────────────────────────────────────
PDF_DIR       = Path("regulations")
INDEX_DIR     = Path("faiss_index")
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 100

# ── 類別對應（檔名關鍵字 → category）──────────────
CATEGORY_MAP = {
    # 本校學則
    "學則":                  "academic_rules",
    "School Regulations":    "academic_rules",
    # 畢業相關
    "畢業資格":              "graduation",
    "畢業生學位證書":        "graduation",
    "學位證書更正":          "graduation",
    # 學籍相關
    "轉系":                  "transfer",
    "輔系":                  "double_major",
    "雙主修":                "double_major",
    "逕修讀博士":            "transfer",
    "修讀碩士班課程":        "transfer",
    # 選課相關
    "選課辦法":              "course_selection",
    "停修":                  "course_selection",
    "校際選課":              "course_selection",
    "暑期修課":              "course_selection",
    "服役彈性修業":          "course_selection",
    "服務學習":              "course_selection",
    "外語課程":              "course_selection",
    "自主學習":              "course_selection",
    "Course Selection":      "course_selection",
    "Interschool":           "course_selection",
    "Withdraw from Courses": "course_selection",
    "Summer Course":         "course_selection",
    # 課務相關
    "開課實施":              "curriculum",
    "學分學程":              "curriculum",
    "課程委員會":            "curriculum",
    "課程大綱":              "curriculum",
    "遠距教學":              "curriculum",
    "大學先修":              "curriculum",
    "優課":                  "curriculum",
    "災害應變":              "curriculum",
    # 招生相關
    "招生":                  "admission",
    "入學規定":              "admission",
    "轉學招生":              "admission",
    "單獨招生":              "admission",
    "特殊選才":              "admission",
    "申請入學":              "admission",
    "運動績優":              "admission",
    "僑生":                  "admission",
    "港澳生":                "admission",
    "新住民":                "admission",
    # 成績相關
    "成績管理":              "grade",
    "抵免學分":              "grade",
    "學業成績":              "grade",
    "Grade Management":      "grade",
    "Transfer of Credits":   "grade",
    "Ranking":               "grade",
    # 學位授予相關
    "學位授予":              "degree",
    "學位考試":              "degree",
    "學術倫理":              "degree",
    "論文指導":              "degree",
    "學位論文":              "degree",
    "名譽博士":              "degree",
    "Academic Ethics":       "degree",
    "Degree Conferral":      "degree",
    # 教師相關
    "教師評鑑":              "teacher",
    "教師評審":              "teacher",
    "教師聘任":              "teacher",
    "教師升等":              "teacher",
    "教師授課":              "teacher",
    "教師請假":              "teacher",
    "教學優良":              "teacher",
    "教學意見":              "teacher",
    "業界專家":              "teacher",
    "內聘專任":              "teacher",
    "Teacher Evaluation":    "teacher",
    "Leave Pay":             "teacher",
    "Teaching Excellence":   "teacher",
    # 獎學金與學雜費
    "獎學金":                "scholarship",
    "優秀新生":              "scholarship",
    "學雜費":                "tuition",
    "雜費調整":              "tuition",
    "原住民族師資生":        "tuition",
    # 證明相關
    "證件工本費":            "certification",
    "請領":                  "certification",
    # 華語文中心
    "華語文中心":            "chinese_center",
    "學人宿舍":              "chinese_center",
    # 期刊
    "教育實踐與研究":        "journal",
    "徵稿":                  "journal",
    "編輯委員會":            "journal",
    # 行政資訊
    "office_info":           "org",
    # 教育部法規
    "大學法":                "moe_law",
    "學位授予法":            "moe_law",
    "總量發展":              "moe_law",
    "各類學位名稱":          "moe_law",
    # 其他
    "基本能力":              "other",
    "專業表現優異":          "other",
}


def get_category(filename: str) -> str:
    for keyword, category in CATEGORY_MAP.items():
        if keyword in filename:
            return category
    return "other"


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


def extract_pdf(pdf_path: Path) -> list:
    docs = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = clean_text(page.extract_text() or "")
            if not text:
                continue
            docs.append(Document(
                page_content=text,
                metadata={
                    "source":   pdf_path.name,
                    "category": get_category(pdf_path.name),
                    "page":     i + 1,
                }
            ))
    return docs



def build_index():
    print("=" * 55)
    print("📚 NTUE 教務處法規知識庫 — 建立向量索引")
    print("=" * 55)

    all_docs = []

    if PDF_DIR.exists():
        pdf_files = sorted(PDF_DIR.glob("*.pdf"))
        print(f"\n📄 找到 {len(pdf_files)} 份 PDF：")
        for pdf in pdf_files:
            docs = extract_pdf(pdf)
            cat  = get_category(pdf.name)
            print(f"  ✅ [{cat:20s}] {pdf.name[:45]} → {len(docs)} 頁")
            all_docs.extend(docs)
    else:
        print(f"\n⚠️  找不到 {PDF_DIR}/ 資料夾")

    if not all_docs:
        print("\n❌ 沒有任何文件，請確認 regulations 存在")
        return

    print(f"\n📊 原始文件總數：{len(all_docs)} 份")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(all_docs)
    avg = sum(len(c.page_content) for c in chunks) // len(chunks)
    print(f"✂️  切塊後：{len(chunks)} 塊（平均 {avg} 字/塊）")

    print(f"\n🔢 向量化中（text-embedding-3-small）...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    BATCH = 100
    vectorstore = None
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i + BATCH]
        print(f"   批次 {i//BATCH+1}/{(len(chunks)-1)//BATCH+1}（{len(batch)} 塊）")
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embeddings)
        else:
            vectorstore.add_documents(batch)

    INDEX_DIR.mkdir(exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))
    print(f"\n✅ 向量庫已儲存至 {INDEX_DIR}/（共 {vectorstore.index.ntotal} 個向量）")
    print("🎉 完成！執行 streamlit run app.py 啟動應用程式")


if __name__ == "__main__":
    build_index()
