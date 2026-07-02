# 國立臺北教育大學教務處法規知識庫系統
## 系統設計規格書 (System Spec)

---

## 1. 專案目標

建立一個以 RAG（Retrieval-Augmented Generation）為核心的法規問答系統，讓在校學生、教職人員、考生、研究生等不同身份的使用者，能透過自然語言查詢教務處相關法規與辦理流程，取得精準的官方回答。

---

## 2. 使用者輪廓

| 身份 | 常見需求 |
|------|------|
| 在校學生 | 選課規定、輔系雙主修、停修、延畢、學分抵免、校際選課 |
| 教職人員／行政 | 教師評鑑、升等審查、教學優良獎、論文相關 |
| 考生／準新生 | 碩士班考科、招生管道、保留入學資格、轉學規定 |
| 研究生 | 學位考試、論文指導費、學術倫理、論文延後公開 |

---

## 3. 系統架構

```
PDF 法規文件（87 份，regulations/ 資料夾）
        ↓
  download_pdfs.py
  批次下載，以法規標題命名
        ↓
  build_index.py
  pdfplumber 解析 → RecursiveCharacterTextSplitter
  chunk_size=500, overlap=100
        ↓
  OpenAI text-embedding-3-small 向量化
        ↓
  FAISS 本地向量資料庫（faiss_index/）
        ↓
使用者提問
  → MMR 向量搜尋（k=5, fetch_k=20, lambda_mult=0.7）
  → GPT-4o-mini（temperature=0.1, max_tokens=800）
  → 回答
        ↑
  Streamlit 前端（app.py）
  四種身份 Tab + 快速提問按鈕 + 對話記憶（5輪）
```

---

## 4. 檔案結構

```
RAG_chatbot/
├── app.py                # Streamlit 主應用程式
├── build_index.py        # 建立 FAISS 向量庫（本地執行一次）
├── download_pdfs.py      # 批次下載 PDF，以標題命名
├── Dockerfile            # Render 容器部署
├── requirements.txt      # 鎖定版本（全部用 ==）
├── .env.example          # 環境變數範例
├── .gitignore            # 排除 .env、regulations/
├── README.md
├── faiss_index/          # 向量庫（納入版控，供 Render 使用）
│   ├── index.faiss
│   └── index.pkl
└── regulations/          # PDF 文件（不納入版控）
```

---

## 5. 文件分類（CATEGORY_MAP）

`build_index.py` 依檔名關鍵字自動分類，metadata 存入 FAISS：

| 類別 ID | 對應關鍵字（部分） | 文件數 |
|------|------|------|
| `academic_rules` | 學則、School Regulations | 2 |
| `graduation` | 畢業資格、畢業生學位證書 | 3 |
| `transfer` | 轉系、逕修讀博士、修讀碩士班課程 | 5 |
| `double_major` | 輔系、雙主修 | 2 |
| `course_selection` | 選課辦法、停修、校際選課、暑期修課 | 12 |
| `curriculum` | 開課實施、學分學程、課程委員會、遠距教學 | 7 |
| `admission` | 招生、入學規定、轉學招生 | 15 |
| `grade` | 成績管理、抵免學分、學業成績 | 6 |
| `degree` | 學位授予、學位考試、學術倫理、論文 | 5 |
| `teacher` | 教師評鑑、升等、授課時數、教學優良獎 | 13 |
| `scholarship` | 獎學金、優秀新生 | 3 |
| `tuition` | 學雜費、雜費調整、原住民族師資生 | 2 |
| `chinese_center` | 華語文中心、學人宿舍 | 3 |
| `journal` | 教育實踐與研究、徵稿、編輯委員會 | 2 |
| `moe_law` | 大學法、學位授予法、總量發展 | 4 |
| `other` | 基本能力、專業表現優異 | 2 |

---

## 6. 核心技術選型

| 項目 | 選擇 | 說明 |
|------|------|------|
| PDF 解析 | `pdfplumber` | 繁中排版提取效果優於 pypdf |
| 文件切塊 | `RecursiveCharacterTextSplitter` | chunk=500, overlap=100，符合法規一條一義結構 |
| Embedding | `text-embedding-3-small` | 繁中支援佳，比 ada-002 準確且便宜 5 倍 |
| 向量庫 | FAISS（本地） | 87 份文件規模無需外部服務 |
| 檢索策略 | MMR（k=5） | 確保段落來自不同條文，避免重複 |
| LLM | `gpt-4o-mini` | temperature=0.1，法規問答精確度足夠 |
| 前端 | Streamlit | 快速建置，支援對話介面 |
| 對話記憶 | `ConversationBufferWindowMemory`（k=5） | 保留最近 5 輪上下文 |

### 套件版本（鎖定）

```
streamlit==1.58.0
langchain==0.2.16
langchain-openai==0.1.23
langchain-community==0.2.16
langchain-core==0.2.43
langchain-text-splitters==0.2.4
faiss-cpu==1.14.3
openai==1.40.0
pypdf==6.14.2
pdfplumber==0.11.10
python-dotenv==1.2.2
requests==2.34.2
tiktoken==0.13.0
httpx==0.27.0
```

> ⚠️ LangChain 版本需嚴格鎖定，`>=` 會導致 Render 裝到不相容版本而報錯。

---

## 7. System Prompt

```
你是「國立臺北教育大學（NTUE）教務處數位法規助理」。

【核心原則】
1. 只根據下方「參考法規段落」的內容回答，禁止自行推測或補充段落中未出現的資訊。
2. 回答中不需標註任何來源或出處。
3. 若段落無法完整回答，說明「本系統資料未涵蓋此項目」，建議致電 (02)2732-1104。
4. 使用繁體中文，語氣親切專業。
5. 條列式回答，字數 500 字內。

【參考法規段落】
{context}

【回答】
```

> **說明**：回答內文不要求 LLM 標註來源（容易產生幻覺，寫出「文件名稱」四字而非真實名稱）。
> 但底部提供「📄 檢視官方參考法規來源」摺疊區塊，直接從 FAISS metadata 取出實際檢索的檔名與頁碼，不經 LLM 生成，來源資訊可信。

---

## 8. 快速建置步驟

### 前置需求
- Python 3.11
- OpenAI API 金鑰（開通 `text-embedding-3-small` + `gpt-4o-mini`）

### Step 1：安裝套件
```bash
pip install -r requirements.txt
```

### Step 2：設定 API 金鑰
```bash
copy .env.example .env   # Windows
cp .env.example .env     # Mac/Linux
# 編輯 .env，填入 OPENAI_API_KEY
```

### Step 3：下載 PDF
```bash
python download_pdfs.py
# → regulations/ 資料夾，87 份，以標題命名
# ⚠️ 音樂學系招生規定需手動從 Google Drive 下載
```

### Step 4：建立向量庫
```bash
python build_index.py
# → faiss_index/ 資料夾
# 首次約 1~2 分鐘，87 份文件約 400~500 個向量塊
```

### Step 5：啟動
```bash
streamlit run app.py
# → http://localhost:8501
```

---

## 9. 部署（Render）

本專案使用 `Dockerfile` 容器部署，`faiss_index/` 納入版控（不在 `.gitignore` 中）。

```bash
# 推送前確認 faiss_index/ 已 commit
git add faiss_index/
git commit -m "update: rebuild faiss index"
git push
# Render 偵測到 push 後自動重新部署
```

**Render 環境變數設定：**
```
OPENAI_API_KEY=sk-你的金鑰
```

**Render Start Command（Dockerfile 內已設定）：**
```
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

---

## 10. 預估成本

| 項目 | 估算 |
|------|------|
| 一次性向量化（87份PDF）| ~$0.05 USD |
| 每次查詢（5段 context + 回答）| ~$0.002 USD |
| 每月 1000 次查詢 | ~$2 USD |
| Render 主機費（Free Tier）| $0 USD |
| **合計** | **< $3 USD/月** |

---

## 11. 更新法規流程

每次教務會議後有新法規時：

```bash
# 1. 將新 PDF 放入 regulations/
# 2. 重建向量庫
python build_index.py

# 3. 推送更新
git add faiss_index/
git commit -m "update: add new regulations YYYY-MM-DD"
git push
```

---

## 12. 已知限制與後續優化方向

| 項目 | 現況 | 後續優化 |
|------|------|------|
| 來源標註 | 回答內文不標註；底部摺疊區塊顯示 FAISS metadata 真實來源 | 可考慮顯示條號（需 PDF 結構化解析支援）|
| 向量庫持久化 | 納入 git 版控 | 法規量大後改用 Railway Volume 或 Supabase pgvector |
| 使用者回饋 | 無 | 加入 👍 👎 機制，記錄問題品質 |
| 冷啟動 | Render Free Tier 約 30 秒 | 升級付費方案或改用 Railway |
| 教育部外部法規 | 5 份為連結，未納入 | 手動下載 PDF 補入 regulations/ |

---

*Spec 版本：v1.0 | 更新日期：2026-07-03 | 狀態：已部署（Render）*
