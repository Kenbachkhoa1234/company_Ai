AEGIS COUNCIL - HƯỚNG DẪN CHẠY TRÊN WINDOWS

CHẠY ỨNG DỤNG
1. Mở CMD tại thư mục AI_Department_Meeting.
2. Chạy: .venv\Scripts\activate
3. Chạy: python -m streamlit run app.py
4. Mở http://localhost:8501 nếu trình duyệt không tự mở.
5. Nhấn Ctrl+C trong CMD để dừng ứng dụng.

YÊU CẦU
- Windows 10 trở lên.
- Ollama đang chạy.
- Python và các thư viện trong requirements.txt đã được cài.
- Ít nhất một model Ollama đã được tải.

MODEL
- App tự đọc danh sách model đã cài từ Ollama.
- Máy hiện có thể dùng qwen3:4b-instruct.
- Muốn giảm RAM, có thể cài qwen3:1.7b bằng: ollama pull qwen3:1.7b
- Sau khi cài, model nhẹ sẽ tự xuất hiện trong sidebar của app.

CÀI LẠI THƯ VIỆN NẾU CẦN
.venv\Scripts\python.exe -m pip install -r requirements.txt

Ứng dụng chạy local, không cần ChatGPT Plus và không cần API key.
