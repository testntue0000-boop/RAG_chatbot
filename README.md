# 國立臺北教育大學教務處法規知識庫助理 (NTUE RAG)

這是一個基於 RAG (Retrieval-Augmented Generation) 架構的問答系統，使用 LangChain、FAISS 與 GPT-4o-mini 模型，來協助查詢國立臺北教育大學（NTUE）教務處的相關法規。

## 📁 專案檔案結構

- `app.py`: Streamlit 網頁應用程式主程式（提供對話介面）。
- `build_index.py`: 讀取 PDF、進行文字切塊並建立 FAISS 向量資料庫的腳本。
- `download_pdfs.py`: 批次從國北教大教務處網站下載最新法規 PDF 的爬蟲腳本。
- `requirements.txt`: 專案執行所需的 Python 套件清單。
- `.gitignore`: Git 忽略清單，確保機密資訊與快取不被推送到遠端。

## 🚀 安裝與執行步驟

### 1. 安裝依賴套件
請確保您的環境中已啟用虛擬環境（如 `ntuerag`），接著安裝所需套件：
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

在專案根目錄建立一個 `.env` 檔案，並填入您的 OpenAI API Key：

```env
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. 獲取法規 PDF 檔案

為了維持 GitHub 儲存庫的輕量化，本專案預設不上傳 PDF 檔案。請先執行下載腳本，腳本會自動將檔案下載並存放至 `regulations/` 資料夾中：

```bash
python download_pdfs.py
```

*(備註：部分檔案如「音樂學系學士班單獨招生規定」因存放在 Google Drive，若腳本無法下載，請依終端機提示手動下載並放入 `regulations/` 資料夾)*

### 4. 建立 FAISS 向量資料庫

準備好 PDF 檔案後，請執行以下腳本將法規文字轉換為向量（只需執行一次，或在法規更新時執行）：

```bash
python build_index.py
```

執行完成後，根目錄會生成 `faiss_index/` 資料夾。

### 5. 啟動 Streamlit 應用程式

啟動法規助理的網頁介面：

```bash
streamlit run app.py
```

執行後，瀏覽器將自動開啟對話介面（預設為 `http://localhost:8501`）。

## ⚠️ 注意事項

* 包含法規原始檔的 `regulations/` 、建置好的向量庫 `faiss_index/` 以及機密金鑰 `.env` 均已加入 `.gitignore` 排除清單，請勿將這些檔案上傳至任何公開的版本控制系統中。

```
存檔後，您就可以繼續執行 `git add .`、`git commit` 跟 `git push` 把程式碼推送到您的 Git 儲存庫
```