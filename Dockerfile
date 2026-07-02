FROM python:3.10-slim

WORKDIR /app

# 暴露 Streamlit 預設埠
EXPOSE 8501

# 直接複製並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製其餘專案檔案
COPY . .

# 啟動命令
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
