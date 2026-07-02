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
