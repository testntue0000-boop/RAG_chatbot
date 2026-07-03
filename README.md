# 國立臺北教育大學 教務處法規知識庫助理

以 RAG（Retrieval-Augmented Generation）架構建立的教務法規問答系統，支援自然語言查詢教務處相關法規與辦理流程，部署於 Render。

---

## 系統架構

```
PDF 法規文件（87 份）
        ↓
  pdfplumber 文字提取 + 清理
        ↓
  LangChain RecursiveCharacterTextSplitter
  （chunk_size=500, overlap=100）
        ↓
  OpenAI text-embedding-3-small 向量化
        ↓
  FAISS 本地向量資料庫
        ↓
使用者提問
  → MMR 向量搜尋（Top-5 相關段落）
  → GPT-4o-mini 生成回答
  → Streamlit 前端顯示
```

---

## 功能

- 查詢學則、選課、畢業審核、轉系、輔系雙主修、招生、成績、學雜費等法規
- 四種使用者身份：在校學生、教職人員／行政、考生／準新生、研究生
- 快速提問按鈕引導常見問題
- 對話記憶，支援多輪追問（保留最近 5 輪）
- MMR 檢索確保回答橫跨多份文件，不重複引用

---

## 專案結構

```
RAG_chatbot/
├── app.py                # Streamlit 主應用程式
├── build_index.py        # 建立 FAISS 向量庫（執行一次）
├── download_pdfs.py      # 批次下載 PDF 法規文件
├── Dockerfile            # Render 容器部署設定
├── requirements.txt      # 鎖定版本的套件清單
├── .gitignore
├── README.md
├── regulations/          # PDF 法規文件（不納入版控）
└── faiss_index/          # FAISS 向量庫（納入版控供 Render 使用）
```

---

## 環境需求

- Python 3.11
- OpenAI API 金鑰（需開通 `text-embedding-3-small` 與 `gpt-4o-mini` 的使用權限）

---

## 本地執行

### 1. 安裝套件

```bash
pip install -r requirements.txt
```

### 2. 設定 API 金鑰

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

編輯 `.env`，填入 OpenAI API 金鑰：

```
OPENAI_API_KEY=sk-你的金鑰
```

### 3. 下載法規 PDF

```bash
python download_pdfs.py
```

PDF 會下載至 `regulations/` 資料夾（共 87 份）。

> ⚠️ 音樂學系學士班單獨招生規定存放於 Google Drive，腳本無法自動下載。
> 請手動下載後命名為 `音樂學系學士班單獨招生規定.pdf` 並放入 `regulations/`。

### 4. 建立向量庫

```bash
python build_index.py
```

首次執行約需 1～2 分鐘，完成後產生 `faiss_index/` 資料夾。向量庫只需建立一次，新增或更新法規後重新執行即可。

### 5. 啟動應用程式

```bash
streamlit run app.py
```

開啟瀏覽器至 `http://localhost:8501`。

---

## 部署（Render）

本專案已包含 `Dockerfile`，Render 會自動偵測並使用容器部署。

### 步驟

1. 將專案 push 至 GitHub
2. 前往 [Render Dashboard](https://dashboard.render.com/)，新建 **Web Service**
3. 連結 GitHub repo，Render 會自動偵測 `Dockerfile`
4. 在 **Environment** 頁面加入環境變數：
   ```
   OPENAI_API_KEY=sk-你的金鑰
   ```
5. 點擊 **Manual Deploy** 觸發部署

> ⚠️ `faiss_index/` 已納入版控，Render 部署時會直接使用。
> 若法規更新需重建向量庫，請在本地執行 `build_index.py` 後重新 push。

---

## 注意事項

- `.env` 含有 API 金鑰，已加入 `.gitignore`，**絕對不可推送至公開儲存庫**
- `regulations/` 含有受版權保護的 PDF，已加入 `.gitignore`
- LangChain 套件版本已鎖定（`requirements.txt` 使用 `==`），升級前請先在本地測試

---

## 技術選型

| 項目 | 選擇 | 原因 |
|------|------|------|
| Embedding | `text-embedding-3-small` | 繁中支援佳，比 ada-002 準確且便宜 5 倍 |
| LLM | `gpt-4o-mini` | 速度快、成本低，temperature=0.1 確保法規回答精確 |
| 向量庫 | FAISS（本地） | 無需額外服務，87 份文件規模完全適用 |
| 檢索策略 | MMR（k=5） | 確保取回段落來自不同條文，避免重複引用 |
| 切塊大小 | 500 字 / 重疊 100 字 | 符合法規條文一條一義的結構 |

---

## 知識庫更新 SOP

系統有兩種更新方式，依情況選擇：

---

### 方式 A：日常更新（QA 問答集 / 單份新法規）

**適用情況：** 新增 QA 問答集、補充單份新法規 PDF

**操作者：** 教務處行政人員（不需碰程式碼）

1. 開啟系統網址，展開左側邊欄底部「🔧 管理員」
2. 輸入管理員密碼
3. 選擇文件類型：
   - **QA 問答集** → 上傳 DOCX（格式見下方說明）
   - **法規文件** → 上傳 PDF
4. 點擊「🚀 上傳並更新知識庫」
5. 出現「✅ 知識庫已更新」後，重新整理頁面即生效

> ⚠️ **不要直接把 PDF 或 Word 檔 push 到 GitHub**，請一律走管理員介面上傳。

---

### 方式 B：大規模更新（法規條文修訂、重建完整知識庫）

**適用情況：** 教務會議後多份法規同時修訂、重建整個向量庫

**操作者：** 系統管理員（需要開發環境）

```bash
# 1. 更新 download_pdfs.py 裡的 PDF 清單（新增或修改連結）

# 2. 本地重新下載與建立 index
python download_pdfs.py
python build_index.py

# 3. push 到 GitHub（Render 自動重新部署）
git add faiss_index/ download_pdfs.py
git commit -m "update: rebuild index YYYY-MM-DD"
git push

# 4. 部署完成後，在 Render Shell 同步 index 到持久化 Disk
cp -r /app/faiss_index /data/
```

> Render Shell 位置：Dashboard → 你的 Web Service → **Shell** 頁籤

---

### QA 問答集 Word 檔格式規範

QA 檔為 DOCX 格式，每個問答配對用以下格式撰寫：

```
Q: 如何申請在學證明？
A: 可至教務處一樓服務台填寫申請表，免費方案為...

Q: 選課衝堂怎麼處理？
A: 請於加退選期間至 iNTUE 系統調整，如有問題...
```

**注意事項：**
- 每個問題以 `Q:` 開頭，答案以 `A:` 開頭
- 一份 Word 檔可包含多個 Q&A
- 檔案大小限制 10MB
- 檔名請使用有意義的中文名稱，例如：`114學年度常見問題.docx`

---

### 兩種方式的差異

| | 方式 A（介面上傳）| 方式 B（GitHub 流程）|
|------|------|------|
| 操作難度 | 低，不需程式背景 | 需要開發環境 |
| 適用文件 | QA 檔、單份新法規 | 多份法規大更新 |
| 生效時間 | 上傳後立即生效 | push 後約 2～5 分鐘 |
| 持久化 | ✅ 存在 Render Disk | 需手動同步到 Disk |
| 重啟後保留 | ✅ 是 | 需再執行 `cp` 指令 |
