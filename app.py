import ctypes
import json
from datetime import datetime
from html import escape

import requests
import streamlit as st


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
DEFAULT_MODEL = "qwen3:4b-instruct"

DEPARTMENTS = {
    "Ban Giám đốc": "Tổng hợp các ý kiến, giải quyết mâu thuẫn và chốt quyết định cuối cùng.",
    "Quản lý dự án": "Chia công việc, xác định ưu tiên, phụ thuộc, tiến độ và rủi ro thực hiện.",
    "Phân tích yêu cầu": "Làm rõ mục tiêu, phạm vi, đối tượng sử dụng và tiêu chí hoàn thành.",
    "Nghiên cứu": "Phân tích lý thuyết, phương pháp, tài liệu và các hướng giải quyết khả thi.",
    "Tìm kiếm dữ liệu": "Xác định nguồn dữ liệu, dataset, giấy phép và độ tin cậy của nguồn.",
    "Xử lý dữ liệu": "Đề xuất làm sạch, chuẩn hóa, gán nhãn, khử trùng lặp và chia dữ liệu.",
    "Phân tích dữ liệu": "Phân tích phân bố, xu hướng, bất thường và các thống kê quan trọng.",
    "Quản trị dữ liệu": "Kiểm soát quyền truy cập, nguồn gốc, phiên bản và dữ liệu nhạy cảm.",
    "AI/ML": "Thiết kế, huấn luyện, triển khai và sử dụng mô hình AI hoặc học máy.",
    "Tối ưu mô hình": "Tối ưu tốc độ, bộ nhớ, hyperparameter và hiệu năng suy luận.",
    "Đánh giá mô hình": "Đề xuất chỉ số, phương pháp kiểm thử, kiểm tra overfitting và độ ổn định.",
    "So sánh kết quả": "So sánh các phương án hoặc mô hình theo cùng tiêu chí và bằng chứng.",
    "Phát triển phần mềm": "Thiết kế và hiện thực frontend, backend, API và tích hợp hệ thống.",
    "Kiến trúc hệ thống": "Thiết kế thành phần, luồng dữ liệu, dịch vụ và khả năng mở rộng.",
    "QA/Testing": "Xây dựng test case, trường hợp biên và tiêu chí xác nhận lỗi đã được sửa.",
    "DevOps": "Phụ trách đóng gói, CI/CD, triển khai, giám sát, sao lưu và rollback.",
    "DevSecOps": "Đưa kiểm tra bảo mật vào code, dependency, secret, container và CI/CD.",
    "Red Team": "Đánh giá bề mặt tấn công và đề xuất kiểm thử trong phạm vi được cho phép.",
    "Blue Team": "Đề xuất logging, phát hiện, cảnh báo, điều tra và ứng phó sự cố.",
    "Purple Team & Phản biện": "Đối chiếu tấn công-phòng thủ và phản biện các kết luận thiếu bằng chứng.",
}

GROUPS = {
    "Điều hành": ["Ban Giám đốc", "Quản lý dự án", "Phân tích yêu cầu"],
    "Nghiên cứu & dữ liệu": ["Nghiên cứu", "Tìm kiếm dữ liệu", "Xử lý dữ liệu", "Phân tích dữ liệu", "Quản trị dữ liệu"],
    "AI & đánh giá": ["AI/ML", "Tối ưu mô hình", "Đánh giá mô hình", "So sánh kết quả"],
    "Phát triển & vận hành": ["Phát triển phần mềm", "Kiến trúc hệ thống", "QA/Testing", "DevOps", "DevSecOps"],
    "An toàn thông tin": ["Red Team", "Blue Team", "Purple Team & Phản biện"],
}

ROUTING_RULES = {
    "Quản lý dự án": ["kế hoạch", "tiến độ", "phân công", "deadline", "dự án"],
    "Phân tích yêu cầu": ["yêu cầu", "chức năng", "người dùng", "phạm vi"],
    "Nghiên cứu": ["nghiên cứu", "tài liệu", "bài báo", "lý thuyết", "phương pháp"],
    "Tìm kiếm dữ liệu": ["dataset", "nguồn dữ liệu", "tìm dữ liệu", "thu thập"],
    "Xử lý dữ liệu": ["làm sạch", "tiền xử lý", "chuẩn hóa", "gán nhãn", "trùng lặp"],
    "Phân tích dữ liệu": ["phân tích dữ liệu", "thống kê", "phân bố", "biểu đồ"],
    "Quản trị dữ liệu": ["dữ liệu nhạy cảm", "quyền riêng tư", "phân quyền dữ liệu", "data governance"],
    "AI/ML": ["mô hình", "machine learning", "deep learning", "ai", "train", "transformer"],
    "Tối ưu mô hình": ["tối ưu", "gpu", "ram", "inference", "hyperparameter", "tăng tốc"],
    "Đánh giá mô hình": ["accuracy", "precision", "recall", "f1", "roc", "đánh giá mô hình"],
    "So sánh kết quả": ["so sánh", "baseline", "kết quả", "mô hình tốt"],
    "Phát triển phần mềm": ["code", "lập trình", "frontend", "backend", "api", "website", "ứng dụng"],
    "Kiến trúc hệ thống": ["kiến trúc", "database", "service", "hệ thống"],
    "QA/Testing": ["test", "kiểm thử", "lỗi", "bug", "trường hợp biên"],
    "DevOps": ["docker", "deploy", "ci/cd", "server", "monitoring", "backup"],
    "DevSecOps": ["devsecops", "dependency", "secret", "sast", "dast", "pipeline bảo mật"],
    "Red Team": ["red team", "tấn công", "pentest", "lỗ hổng", "xss", "sql injection"],
    "Blue Team": ["blue team", "soc", "log", "cảnh báo", "phát hiện", "ứng phó"],
    "Purple Team & Phản biện": ["purple team", "phản biện", "kiểm chứng", "đối chiếu"],
}


def auto_select_departments(question: str) -> list[str]:
    text = question.lower()
    scored = []
    for department, keywords in ROUTING_RULES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score:
            scored.append((score, department))
    scored.sort(key=lambda item: (-item[0], list(DEPARTMENTS).index(item[1])))
    selected = [department for _, department in scored[:5]]
    defaults = ["Phân tích yêu cầu", "Nghiên cứu", "Phát triển phần mềm"]
    for department in defaults:
        if len(selected) >= 3:
            break
        if department not in selected:
            selected.append(department)
    return selected[:5]


@st.cache_data(ttl=30, show_spinner=False)
def get_ollama_state() -> tuple[bool, list[str]]:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=0.8)
        response.raise_for_status()
        models = [item["name"] for item in response.json().get("models", [])]
        return True, models
    except requests.RequestException:
        return False, []


@st.cache_data(ttl=10, show_spinner=False)
def get_memory_percent() -> int | None:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong),
            ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    try:
        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.memory_load)
    except (AttributeError, OSError):
        pass
    return None


def build_prompt(question: str, selected: list[str]) -> str:
    roles = "\n".join(
        f"{index}. {name}: {DEPARTMENTS[name]}"
        for index, name in enumerate(selected, start=1)
    )
    handoff_route = " → ".join(["Người dùng", *selected, "Ban Giám đốc"])
    department_sections = "\n\n".join(
        f"""### {name}
- Tiếp nhận từ: [người dùng hoặc phòng đứng trước]
- Xử lý: [nhận định, rủi ro và đề xuất thuộc chuyên môn]
- Bàn giao cho: [phòng đứng sau và thông tin cần chuyển tiếp]"""
        for name in selected
    )
    return f"""Bạn đang điều hành một cuộc họp chuyên môn bằng tiếng Việt.

YÊU CẦU CỦA NGƯỜI DÙNG:
{question}

PHÒNG BAN THAM GIA THEO THỨ TỰ:
{roles}

CHUỖI BÀN GIAO:
{handoff_route}

QUY TẮC BẮT BUỘC:
1. Chỉ phân tích đúng yêu cầu và phạm vi được cung cấp.
2. Không tự đặt ngày, thời hạn, con số, kết quả thử nghiệm hoặc sự kiện chưa được cung cấp.
3. Nếu thiếu dữ kiện quan trọng, ghi rõ: "Cần người dùng xác nhận".
4. Không lặp ý giữa các phòng. Mỗi phòng chỉ nêu những nội dung thuộc chuyên môn của mình.
5. Với nội dung an toàn thông tin, chỉ đề xuất kiểm thử trong hệ thống được sở hữu hoặc được cho phép.
6. Không tuyên bố chắc chắn khi chưa có bằng chứng; phải phân biệt sự thật, suy luận và đề xuất.
7. Trả lời ngắn gọn, rõ ràng, hoàn toàn bằng tiếng Việt.
8. Các phòng xử lý đúng thứ tự trong chuỗi bàn giao. Mỗi phòng phải kế thừa thông tin hữu ích từ phòng trước và tạo đầu ra cụ thể cho phòng sau.
9. Không mô tả chung chung rằng đã bàn giao; phải nêu ngắn gọn thông tin nào được chuyển tiếp.

ĐỊNH DẠNG:
## Biên bản cuộc họp
{department_sections}

### Ban Giám đốc kết luận
- Tiếp nhận từ phòng cuối
- Các điểm đã thống nhất
- Thứ tự ưu tiên
- Nội dung cần người dùng xác nhận
"""


def stream_ollama(prompt: str, model: str):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "keep_alive": "45s",
        "options": {
            "num_ctx": 3072,
            "num_predict": 700,
            "temperature": 0.25,
            "top_p": 0.85,
        },
    }
    with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            content = data.get("message", {}).get("content", "")
            if content:
                yield content


def render_pipeline(
    selected: list[str],
    active_index: int = 0,
    completed: bool = False,
    failed: bool = False,
) -> str:
    middle_stages = selected or ["Định tuyến phòng ban"]
    stages = [
        ("Tiếp nhận", "Yêu cầu người dùng"),
        *((name, "Phân tích & bàn giao") for name in middle_stages),
        ("Ban Giám đốc", "Tổng hợp kết luận"),
    ]
    nodes = []

    for index, (name, description) in enumerate(stages):
        if completed or index < active_index:
            state = "done"
            state_label = "Đã xong"
            marker = "✓"
        elif failed and index == active_index:
            state = "failed"
            state_label = "Đã dừng"
            marker = "!"
        elif index == active_index:
            state = "active"
            state_label = "Đang xử lý"
            marker = str(index + 1).zfill(2)
        else:
            state = "waiting"
            state_label = "Chờ"
            marker = str(index + 1).zfill(2)

        nodes.append(
            f"""
            <div class="aegis-pipeline__node {state}">
                <div class="aegis-pipeline__top">
                    <span class="aegis-pipeline__marker">{marker}</span>
                    <span class="aegis-pipeline__state">{state_label}</span>
                </div>
                <strong>{name}</strong>
                <small>{description}</small>
            </div>
            """
        )
        if index < len(stages) - 1:
            nodes.append('<div class="aegis-pipeline__arrow">→</div>')

    return '<div class="aegis-pipeline">' + "".join(nodes) + "</div>"


def stream_meeting(prompt: str, selected: list[str], pipeline_slot, model: str):
    accumulated = ""
    active_index = 1
    pipeline_slot.markdown(
        render_pipeline(selected, active_index=active_index),
        unsafe_allow_html=True,
    )

    try:
        for content in stream_ollama(prompt, model):
            accumulated += content
            next_active = active_index
            normalized_output = accumulated.lower()

            for index, department in enumerate(selected, start=1):
                if f"### {department}".lower() in normalized_output:
                    next_active = max(next_active, index)

            if "### ban giám đốc" in normalized_output:
                next_active = len(selected) + 1

            if next_active != active_index:
                active_index = next_active
                pipeline_slot.markdown(
                    render_pipeline(selected, active_index=active_index),
                    unsafe_allow_html=True,
                )
            yield content
    except Exception:
        pipeline_slot.markdown(
            render_pipeline(selected, active_index=active_index, failed=True),
            unsafe_allow_html=True,
        )
        raise

    pipeline_slot.markdown(
        render_pipeline(selected, completed=True),
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Aegis Council",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        :root {
            --aegis-navy: #12213f;
            --aegis-blue: #205b8f;
            --aegis-mint: #22b8a7;
            --aegis-ink: #17243c;
            --aegis-muted: #667085;
            --aegis-line: #e4e9f2;
            --aegis-surface: rgba(255, 255, 255, 0.92);
        }

        .stApp {
            background: #f6f8fc;
            color: var(--aegis-ink);
        }

        [data-testid="stHeader"] {
            background: #f6f8fc;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid #dfe5ed;
            background: #eef2f7;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: .65rem;
        }

        .aegis-side-brand {
            margin: .25rem 0 .7rem;
            padding: 1.1rem;
            border-radius: 16px;
            background: #12213f;
            color: #ffffff;
        }

        .aegis-side-brand span {
            display: block;
            margin-bottom: .2rem;
            color: #80dacf;
            font-size: .65rem;
            font-weight: 800;
            letter-spacing: .11em;
            text-transform: uppercase;
        }

        .aegis-side-brand strong {
            font-size: 1.05rem;
        }

        .aegis-side-status {
            display: grid;
            grid-template-columns: 8px 1fr;
            align-items: center;
            gap: .65rem;
            padding: .7rem .8rem;
            border: 1px solid #dce3ec;
            border-radius: 11px;
            background: #ffffff;
            color: #516074;
            font-size: .72rem;
        }

        .aegis-side-status__dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #22a98f;
        }

        .aegis-side-status.offline .aegis-side-status__dot {
            background: #d64545;
        }

        .aegis-side-section {
            margin: .85rem 0 .15rem;
            color: #6d788a;
            font-size: .66rem;
            font-weight: 800;
            letter-spacing: .09em;
            text-transform: uppercase;
        }

        .aegis-history-item {
            margin-bottom: .45rem;
            padding: .7rem .75rem;
            border: 1px solid #dde4ed;
            border-radius: 11px;
            background: rgba(255, 255, 255, .75);
        }

        .aegis-history-item strong {
            display: block;
            overflow: hidden;
            color: #344258;
            font-size: .72rem;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .aegis-history-item span {
            color: #8490a1;
            font-size: .64rem;
        }

        .block-container {
            max-width: 1240px;
            padding-top: 2.25rem;
            padding-bottom: 3.5rem;
        }

        .aegis-hero {
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 2rem;
            min-height: 190px;
            padding: 2.3rem 2.6rem;
            margin-bottom: 1.15rem;
            border: 1px solid rgba(255, 255, 255, .15);
            border-radius: 28px;
            background: linear-gradient(135deg, #12213f, #174267);
            box-shadow: 0 10px 28px rgba(18, 33, 63, .13);
        }

        .aegis-hero__copy,
        .aegis-hero__status {
            position: relative;
            z-index: 1;
        }

        .aegis-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            margin-bottom: 1rem;
            color: #8fe4da;
            font-size: .73rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .aegis-eyebrow::before {
            content: "";
            width: 22px;
            height: 2px;
            border-radius: 999px;
            background: #59d3c5;
        }

        .aegis-hero h1 {
            margin: 0;
            color: #ffffff;
            font-size: clamp(2.2rem, 4vw, 3.55rem);
            font-weight: 760;
            line-height: 1.02;
            letter-spacing: -.045em;
        }

        .aegis-hero p {
            max-width: 650px;
            margin: 1rem 0 0;
            color: rgba(231, 240, 249, .78);
            font-size: 1rem;
            line-height: 1.65;
        }

        .aegis-hero__status {
            flex: 0 0 auto;
            display: inline-flex;
            align-items: center;
            gap: .65rem;
            padding: .72rem 1rem;
            border: 1px solid rgba(255, 255, 255, .16);
            border-radius: 999px;
            background: rgba(255, 255, 255, .08);
            color: #eef9f7;
            font-size: .8rem;
            font-weight: 650;
        }

        .aegis-live-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #55e2bd;
            box-shadow: 0 0 0 5px rgba(85, 226, 189, .12);
        }

        .aegis-live-dot.offline {
            background: #ef7777;
            box-shadow: none;
        }

        .aegis-stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .8rem;
            margin: 0 0 1.6rem;
        }

        .aegis-stat {
            display: flex;
            align-items: center;
            gap: .85rem;
            padding: .9rem 1.1rem;
            border: 1px solid var(--aegis-line);
            border-radius: 16px;
            background: #ffffff;
        }

        .aegis-stat__icon {
            display: grid;
            place-items: center;
            width: 36px;
            height: 36px;
            border-radius: 11px;
            background: #e9f7f5;
            font-size: 1rem;
        }

        .aegis-stat strong {
            display: block;
            color: var(--aegis-ink);
            font-size: .93rem;
        }

        .aegis-stat span {
            display: block;
            margin-top: .1rem;
            color: var(--aegis-muted);
            font-size: .75rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--aegis-line);
            border-radius: 22px;
            background: var(--aegis-surface);
            box-shadow: 0 4px 14px rgba(18, 33, 63, .045);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: .25rem .35rem;
        }

        .aegis-section-head {
            display: flex;
            align-items: center;
            gap: .75rem;
            margin-bottom: .25rem;
        }

        .aegis-step {
            display: inline-grid;
            place-items: center;
            width: 32px;
            height: 32px;
            border-radius: 10px;
            background: var(--aegis-navy);
            color: #fff;
            font-size: .72rem;
            font-weight: 800;
        }

        .aegis-section-head h2 {
            margin: 0;
            color: var(--aegis-ink);
            font-size: 1.16rem;
            letter-spacing: -.015em;
        }

        .aegis-section-copy {
            margin: .35rem 0 1.1rem;
            color: var(--aegis-muted);
            font-size: .82rem;
            line-height: 1.55;
        }

        .stTextArea textarea,
        .stMultiSelect [data-baseweb="select"] > div {
            border-color: #dbe2ec !important;
            border-radius: 13px !important;
            background: #fbfcfe !important;
        }

        .stTextArea textarea:focus {
            border-color: var(--aegis-mint) !important;
            box-shadow: 0 0 0 3px rgba(34, 184, 167, .12) !important;
        }

        div[role="radiogroup"] {
            gap: .5rem;
        }

        div[role="radiogroup"] label {
            padding: .42rem .72rem;
            border: 1px solid var(--aegis-line);
            border-radius: 10px;
            background: #fbfcfe;
        }

        .aegis-suggestion-label {
            margin: .8rem 0 .55rem;
            color: var(--aegis-muted);
            font-size: .76rem;
            font-weight: 700;
            letter-spacing: .04em;
            text-transform: uppercase;
        }

        .aegis-chips {
            display: flex;
            flex-wrap: wrap;
            gap: .45rem;
            margin-bottom: 1rem;
        }

        .aegis-chip {
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            padding: .43rem .68rem;
            border: 1px solid #ccebe6;
            border-radius: 999px;
            background: #eefaf8;
            color: #18796f;
            font-size: .75rem;
            font-weight: 650;
        }

        .aegis-chip::before {
            content: "✓";
            font-size: .68rem;
        }

        .aegis-note {
            display: flex;
            gap: .72rem;
            align-items: flex-start;
            margin: .55rem 0 1rem;
            padding: .85rem .95rem;
            border: 1px solid #dce8f5;
            border-radius: 13px;
            background: #f3f8fd;
            color: #426078;
            font-size: .79rem;
            line-height: 1.5;
        }

        .aegis-note__icon {
            flex: 0 0 auto;
            display: grid;
            place-items: center;
            width: 25px;
            height: 25px;
            border-radius: 8px;
            background: #dcebf8;
        }

        .stButton > button[kind="primary"] {
            min-height: 3rem;
            border: 0;
            border-radius: 13px;
            background: linear-gradient(135deg, #17345c, #1a756f);
            box-shadow: 0 4px 12px rgba(23, 52, 92, .14);
            font-weight: 750;
            letter-spacing: .01em;
            transition: transform .15s ease, box-shadow .15s ease;
        }

        .stButton > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(23, 52, 92, .17);
        }

        .aegis-active-roles {
            margin: .2rem 0 1rem;
            padding: .7rem .85rem;
            border-left: 3px solid var(--aegis-mint);
            border-radius: 0 10px 10px 0;
            background: #f2faf9;
            color: #45645f;
            font-size: .76rem;
            line-height: 1.55;
        }

        .aegis-pipeline-label {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: .25rem 0 .55rem;
            color: var(--aegis-ink);
            font-size: .78rem;
            font-weight: 750;
        }

        .aegis-pipeline-label span {
            color: var(--aegis-muted);
            font-size: .7rem;
            font-weight: 500;
        }

        .aegis-pipeline {
            display: flex;
            align-items: center;
            gap: .38rem;
            overflow-x: auto;
            margin-bottom: 1rem;
            padding: .75rem;
            border: 1px solid #e5eaf1;
            border-radius: 14px;
            background: #f8fafc;
            scrollbar-width: thin;
        }

        .aegis-pipeline__node {
            flex: 0 0 132px;
            min-height: 94px;
            padding: .65rem;
            border: 1px solid #e2e7ee;
            border-radius: 11px;
            background: #ffffff;
        }

        .aegis-pipeline__top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: .4rem;
            margin-bottom: .6rem;
        }

        .aegis-pipeline__marker {
            display: grid;
            place-items: center;
            width: 25px;
            height: 25px;
            border-radius: 8px;
            background: #edf1f5;
            color: #778295;
            font-size: .65rem;
            font-weight: 800;
        }

        .aegis-pipeline__state {
            color: #8a94a5;
            font-size: .62rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .aegis-pipeline__node strong,
        .aegis-pipeline__node small {
            display: block;
        }

        .aegis-pipeline__node strong {
            overflow: hidden;
            color: #526075;
            font-size: .76rem;
            line-height: 1.25;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .aegis-pipeline__node small {
            margin-top: .25rem;
            color: #98a1af;
            font-size: .64rem;
            line-height: 1.25;
        }

        .aegis-pipeline__node.active {
            border-color: #7ecfc5;
            background: #effaf8;
        }

        .aegis-pipeline__node.active .aegis-pipeline__marker {
            background: var(--aegis-navy);
            color: #ffffff;
        }

        .aegis-pipeline__node.active .aegis-pipeline__state,
        .aegis-pipeline__node.active strong {
            color: #167b71;
        }

        .aegis-pipeline__node.done {
            border-color: #d2ebe7;
        }

        .aegis-pipeline__node.done .aegis-pipeline__marker {
            background: #dff5f1;
            color: #148175;
        }

        .aegis-pipeline__node.done .aegis-pipeline__state {
            color: #278c82;
        }

        .aegis-pipeline__node.failed {
            border-color: #efb5b5;
            background: #fff7f7;
        }

        .aegis-pipeline__node.failed .aegis-pipeline__marker {
            background: #fbe2e2;
            color: #b42318;
        }

        .aegis-pipeline__node.failed .aegis-pipeline__state {
            color: #b42318;
        }

        .aegis-pipeline__arrow {
            flex: 0 0 auto;
            color: #aab2bf;
            font-size: .9rem;
        }

        .aegis-empty {
            display: grid;
            place-items: center;
            min-height: 260px;
            padding: 2.5rem;
            text-align: center;
        }

        .aegis-empty__icon {
            display: grid;
            place-items: center;
            width: 66px;
            height: 66px;
            margin: 0 auto 1rem;
            border: 1px solid #d8e8e6;
            border-radius: 20px;
            background: linear-gradient(145deg, #f4fbfa, #e4f3f1);
            color: #1b887e;
            font-size: 1.55rem;
        }

        .aegis-empty h3 {
            margin: 0 0 .45rem;
            color: var(--aegis-ink);
            font-size: 1rem;
        }

        .aegis-empty p {
            max-width: 360px;
            margin: 0;
            color: var(--aegis-muted);
            font-size: .82rem;
            line-height: 1.6;
        }

        .aegis-result-meta {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: .8rem;
            padding-bottom: .75rem;
            border-bottom: 1px solid #edf0f5;
            color: var(--aegis-muted);
            font-size: .75rem;
        }

        .aegis-result-meta strong {
            color: #278c82;
        }

        .aegis-download-card {
            display: flex;
            align-items: center;
            gap: .8rem;
        }

        .aegis-download-card__icon {
            display: grid;
            place-items: center;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: #eaf7f5;
            font-size: 1.1rem;
        }

        .aegis-download-card strong {
            display: block;
            font-size: .9rem;
        }

        .aegis-download-card span {
            color: var(--aegis-muted);
            font-size: .75rem;
        }

        .stDownloadButton > button {
            min-height: 2.8rem;
            border: 1px solid #cfd9e6;
            border-radius: 12px;
            color: var(--aegis-navy);
            font-weight: 700;
        }

        [data-testid="stExpander"] {
            margin-top: .8rem;
            border-color: var(--aegis-line);
            border-radius: 16px;
            background: rgba(255, 255, 255, .65);
        }

        .aegis-footer-title {
            margin: 1.9rem 0 .1rem;
            color: var(--aegis-ink);
            font-size: .95rem;
            font-weight: 750;
        }

        .aegis-footer-copy {
            margin: 0;
            color: var(--aegis-muted);
            font-size: .78rem;
        }

        @media (max-width: 780px) {
            .block-container { padding-top: 1rem; }
            .aegis-hero { align-items: flex-start; flex-direction: column; min-height: auto; padding: 2rem 1.5rem; border-radius: 21px; }
            .aegis-stats { grid-template-columns: 1fr; }
            .aegis-empty { min-height: 270px; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

ollama_online, installed_models = get_ollama_state()
model_options = installed_models or [DEFAULT_MODEL]
preferred_models = ["qwen3:1.7b", DEFAULT_MODEL, "qwen3:0.6b"]
preferred_model = next(
    (model for model in preferred_models if model in model_options),
    model_options[0],
)
memory_percent = get_memory_percent()

with st.sidebar:
    st.markdown(
        """
        <div class="aegis-side-brand">
            <span>Local AI workspace</span>
            <strong>🏛️ Aegis Council</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    online_class = "" if ollama_online else " offline"
    online_label = "Ollama đang hoạt động" if ollama_online else "Ollama chưa kết nối"
    st.markdown(
        f'<div class="aegis-side-status{online_class}"><span class="aegis-side-status__dot"></span><span>{online_label}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="aegis-side-section">Cài đặt cuộc họp</div>', unsafe_allow_html=True)
    selected_model = st.selectbox(
        "Model local",
        model_options,
        index=model_options.index(preferred_model),
        help="Danh sách được đọc trực tiếp từ Ollama và lưu đệm 30 giây.",
    )
    if memory_percent is not None:
        st.caption(f"RAM hệ thống đang dùng: {memory_percent}%")
    st.caption("Mỗi cuộc họp chỉ gọi model một lần để tiết kiệm tài nguyên.")

ollama_label = "Local sẵn sàng" if ollama_online else "Local ngoại tuyến"
hero_dot_class = "" if ollama_online else " offline"

st.markdown(
    f"""
    <section class="aegis-hero">
        <div class="aegis-hero__copy">
            <div class="aegis-eyebrow">Hội đồng chuyên môn AI</div>
            <h1>Aegis Council</h1>
            <p>Tập hợp góc nhìn từ các phòng ban chuyên môn, phản biện có cấu trúc và đưa ra kết luận rõ ràng — hoàn toàn trên máy của bạn.</p>
        </div>
        <div class="aegis-hero__status"><span class="aegis-live-dot{hero_dot_class}"></span> {ollama_label} · {escape(selected_model)}</div>
    </section>
    <div class="aegis-stats">
        <div class="aegis-stat"><div class="aegis-stat__icon">◫</div><div><strong>20 phòng ban</strong><span>Đủ góc nhìn chuyên môn</span></div></div>
        <div class="aegis-stat"><div class="aegis-stat__icon">◎</div><div><strong>5 nhóm năng lực</strong><span>Tự động định tuyến yêu cầu</span></div></div>
        <div class="aegis-stat"><div class="aegis-stat__icon">⌁</div><div><strong>Riêng tư tại máy</strong><span>Dữ liệu xử lý qua Ollama</span></div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([0.82, 1.18], gap="large")

with left:
    with st.container(border=True):
        st.markdown(
            """
            <div class="aegis-section-head"><span class="aegis-step">01</span><h2>Thiết lập cuộc họp</h2></div>
            <p class="aegis-section-copy">Mô tả vấn đề và chọn các đơn vị chuyên môn cần tham gia phản biện.</p>
            """,
            unsafe_allow_html=True,
        )
        question = st.text_area(
            "Nội dung cần thảo luận",
            height=155,
            placeholder="Ví dụ: Đánh giá thiết kế bảo mật cho website bán hàng của nhóm...",
        )
        mode = st.radio(
            "Cách chọn phòng ban",
            ["Tự động đề xuất", "Tự chọn"],
            horizontal=True,
        )

        if mode == "Tự động đề xuất":
            suggested = auto_select_departments(question) if question.strip() else []
            selected = suggested
            if suggested:
                chips = "".join(f'<span class="aegis-chip">{name}</span>' for name in suggested)
                st.markdown(
                    f'<div class="aegis-suggestion-label">Hệ thống đề xuất</div><div class="aegis-chips">{chips}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Nhập nội dung để hệ thống đề xuất phòng ban phù hợp.")
        else:
            selected = st.multiselect(
                "Chọn tối đa 5 phòng chuyên môn",
                [name for name in DEPARTMENTS if name != "Ban Giám đốc"],
                max_selections=5,
                placeholder="Tìm và chọn phòng ban...",
            )

        st.markdown(
            """
            <div class="aegis-note">
                <span class="aegis-note__icon">◆</span>
                <span><strong>Ban Giám đốc luôn tham gia</strong><br>Đơn vị này sẽ tổng hợp ý kiến, xử lý mâu thuẫn và chốt kết luận cuối cùng.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        start = st.button(
            "Bắt đầu cuộc họp  →",
            type="primary",
            use_container_width=True,
        )

with right:
    with st.container(border=True):
        st.markdown(
            """
            <div class="aegis-section-head"><span class="aegis-step">02</span><h2>Biên bản cuộc họp</h2></div>
            <p class="aegis-section-copy">Theo dõi thông tin được xử lý và bàn giao lần lượt giữa các phòng ban.</p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="aegis-pipeline-label">Dây chuyền xử lý <span>Chỉ cập nhật khi chuyển công đoạn</span></div>',
            unsafe_allow_html=True,
        )
        pipeline_slot = st.empty()

        pipeline_departments = selected
        pipeline_completed = False
        if st.session_state.history and not start:
            latest_pipeline = st.session_state.history[0]
            is_latest_request = (
                question.strip() == latest_pipeline["question"].strip()
                and selected == latest_pipeline["departments"]
            )
            if not question.strip() or is_latest_request:
                pipeline_departments = latest_pipeline["departments"]
                pipeline_completed = True

        pipeline_slot.markdown(
            render_pipeline(
                pipeline_departments,
                active_index=0,
                completed=pipeline_completed,
            ),
            unsafe_allow_html=True,
        )

        if start:
            if not question.strip():
                st.error("Hãy nhập nội dung cần thảo luận.")
            elif not selected:
                st.error("Chưa có phòng ban phù hợp. Hãy chuyển sang Tự chọn và chọn ít nhất một phòng.")
            else:
                roles_text = " · ".join(selected + ["Ban Giám đốc"])
                st.markdown(
                    f'<div class="aegis-active-roles"><strong>Đang tham gia</strong><br>{roles_text}</div>',
                    unsafe_allow_html=True,
                )
                try:
                    result = st.write_stream(
                        stream_meeting(
                            build_prompt(question, selected),
                            selected,
                            pipeline_slot,
                            selected_model,
                        )
                    )
                    if not isinstance(result, str):
                        result = str(result)
                    st.session_state.history.insert(
                        0,
                        {
                            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "question": question,
                            "departments": selected,
                            "result": result,
                        },
                    )
                    del st.session_state.history[5:]
                except requests.ConnectionError:
                    st.error("Không kết nối được Ollama. Hãy mở Ollama rồi thử lại.")
                except requests.Timeout:
                    st.error("Model phản hồi quá lâu. Hãy thử yêu cầu ngắn hơn.")
                except requests.HTTPError as error:
                    st.error(f"Ollama trả về lỗi: {error}")
                except Exception as error:
                    st.error(f"Đã xảy ra lỗi: {error}")
        elif st.session_state.history:
            latest = st.session_state.history[0]
            st.markdown(
                f'<div class="aegis-result-meta"><strong>Biên bản gần nhất</strong><span>{latest["time"]}</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(latest["result"])
        else:
            st.markdown(
                """
                <div class="aegis-empty">
                    <div>
                        <div class="aegis-empty__icon">✦</div>
                        <h3>Sẵn sàng triệu tập hội đồng</h3>
                        <p>Nhập vấn đề ở bảng bên trái. Biên bản chuyên môn sẽ xuất hiện tại đây khi cuộc họp bắt đầu.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

if st.session_state.history:
    latest = st.session_state.history[0]
    export_text = (
        f"AEGIS COUNCIL - BIÊN BẢN CUỘC HỌP\n"
        f"Thời gian: {latest['time']}\n"
        f"Phòng tham gia: {', '.join(latest['departments'])}, Ban Giám đốc\n\n"
        f"Yêu cầu:\n{latest['question']}\n\n{latest['result']}"
    )
    with st.container(border=True):
        export_left, export_right = st.columns([1, 0.34], vertical_alignment="center")
        with export_left:
            st.markdown(
                f"""
                <div class="aegis-download-card">
                    <div class="aegis-download-card__icon">↓</div>
                    <div><strong>Biên bản đã sẵn sàng</strong><span>{latest['time']} · {len(latest['departments']) + 1} phòng tham gia</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with export_right:
            st.download_button(
                "Tải bản TXT",
                export_text,
                file_name="bien-ban-cuoc-hop.txt",
                mime="text/plain",
                use_container_width=True,
            )

with st.sidebar:
    st.markdown('<div class="aegis-side-section">Lịch sử gần đây</div>', unsafe_allow_html=True)
    if st.session_state.history:
        for meeting in st.session_state.history:
            safe_question = escape(" ".join(meeting["question"].split()))
            st.markdown(
                f"""
                <div class="aegis-history-item">
                    <strong>{safe_question}</strong>
                    <span>{meeting['time']} · {len(meeting['departments']) + 1} phòng</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("Chưa có biên bản trong phiên làm việc này.")
    st.divider()
    st.caption("Không cần ChatGPT Plus · Không cần API key · Có thể chạy offline")

st.markdown(
    """
    <div class="aegis-footer-title">Khám phá hội đồng chuyên môn</div>
    <p class="aegis-footer-copy">Xem vai trò và phạm vi tư vấn của toàn bộ 20 phòng ban.</p>
    """,
    unsafe_allow_html=True,
)

with st.expander("Danh sách đầy đủ 20 phòng ban"):
    for group, names in GROUPS.items():
        st.markdown(f"**{group}**")
        for name in names:
            st.markdown(f"- **{name}:** {DEPARTMENTS[name]}")
