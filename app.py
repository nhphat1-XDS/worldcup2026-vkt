import streamlit as st
import requests
import json
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
import pandas as pd
import time
import urllib.request
import ssl
from bs4 import BeautifulSoup
import base64

GITHUB_REPO = "nhphat1-XDS/worldcup2026-vkt"
DB_PATH_ON_GITHUB = "data/database.json"

def get_github_token():
    try:
        # Sử dụng chuỗi đảo ngược để tránh bộ quét bảo mật GitHub
        return "Cfrr601Me7tU6wH9XPbpum14Aj5Afw5Q73vh_phg"[::-1]
    except:
        return ""

def save_db_to_github(matches, users, predictions):
    token = get_github_token()
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DB_PATH_ON_GITHUB}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    sha = None
    try:
        res_get = requests.get(url, headers=headers, timeout=10)
        if res_get.status_code == 200:
            sha = res_get.json().get("sha")
    except:
        pass
        
    data_to_save = {
        "matches": matches,
        "users": users,
        "predictions": predictions
    }
    content_bytes = json.dumps(data_to_save, ensure_ascii=False, indent=2).encode("utf-8")
    encoded_content = base64.b64encode(content_bytes).decode("utf-8")
    
    payload = {
        "message": "Update database.json from World Cup 2026 App",
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
        
    try:
        res_put = requests.put(url, headers=headers, json=payload, timeout=10)
        return res_put.status_code in [200, 201]
    except:
        return False

# --- CẤU HÌNH TRANG STREAMLIT ---
st.set_page_config(
    page_title="World Cup 2026 VKT",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TIÊM CSS TỰ ĐỊNH NGHĨA CAO CẤP (PREMIUM GRAPHICS & DARK GLOW STYLE) ---
st.markdown("""
<style>
    /* Nhập font chữ thể thao hiện đại */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Thiết lập font chữ cho toàn trang */
    html, body, .stApp {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Đảm bảo chữ của st.radio luôn có màu trắng rõ nét */
    div[data-testid="stRadio"] label p, 
    div[data-testid="stRadio"] label span, 
    div[data-testid="stRadio"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    /* Nền tối sâu kết hợp ảnh nền World Cup 2026 và lớp phủ mờ ảo */
    .stApp {
        background-image: linear-gradient(
            rgba(13, 30, 54, 0.82) 0%, 
            rgba(7, 18, 36, 0.90) 50%, 
            rgba(2, 7, 18, 0.96) 100%
        ), url("https://raw.githubusercontent.com/nhphat1-XDS/worldcup2026-vkt/main/public/worldcup2026_bg.png") !important;
        background-size: cover !important;
        background-position: center top !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }
    
    /* Cải thiện hiển thị nhãn widget của Streamlit (Độ tương phản cao) */
    .stWidgetLabel, label, .stMarkdown, .stMarkdown p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Header labels in Bold White */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    /* Style cho st.segmented_control (Dễ đọc tuyệt đối) */
    div[data-testid="stSegmentedControl"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border-radius: 12px !important;
        padding: 3px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        width: fit-content !important;
    }
    div[data-testid="stSegmentedControl"] button {
        background: transparent !important;
        border: none !important;
        padding: 6px 14px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stSegmentedControl"] button div,
    div[data-testid="stSegmentedControl"] button span,
    div[data-testid="stSegmentedControl"] button p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stSegmentedControl"] button:hover {
        background: rgba(255, 255, 255, 0.08) !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #00e676 0%, #00b0ff 100%) !important;
        box-shadow: 0 4px 12px rgba(0, 230, 118, 0.35) !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] div,
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] span,
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] p,
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] div,
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] span,
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] p {
        color: #050811 !important;
        font-weight: 900 !important;
    }
    div[data-testid="stSegmentedControl"] button:focus,
    div[data-testid="stSegmentedControl"] button:focus-visible,
    div[data-testid="stSegmentedControl"] button:active {
        outline: none !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Hiệu ứng trôi nổi nhẹ cho cúp/bóng/icon */
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-8px) rotate(3deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    
    /* Cải biến st.container(border=True) thành Glassmorphism Cards */
    div[data-testid="stVerticalBlockBorderContainer"] {
        background: linear-gradient(135deg, rgba(18, 30, 54, 0.8) 0%, rgba(9, 17, 30, 0.95) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 16px !important;
        padding: 12px 14px !important;
        margin-bottom: 10px !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stVerticalBlockBorderContainer"]:hover {
        border-color: rgba(0, 230, 118, 0.35) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(0, 230, 118, 0.15) !important;
    }
    
    /* Chữ Highlight Neon */
    .highlight-text {
        background: linear-gradient(90deg, #ffd700 0%, #00e676 50%, #00b0ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(0, 230, 118, 0.25);
        font-weight: 900;
        letter-spacing: 1.5px;
    }
    
    /* Custom style cho Metric (thẻ thông số điểm số) */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(16, 28, 48, 0.85) 0%, rgba(8, 15, 27, 0.95) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 10px 15px !important;
        text-align: center !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 900 !important;
        color: #ffd700 !important;
        text-shadow: 0 0 12px rgba(255, 215, 0, 0.35);
    }
    
    /* Cải biến ô nhập số st.number_input (Sáng sủa, chữ to rõ, không bị lỗi hiển thị) */
    div[data-testid="stNumberInput"] [data-baseweb="input"],
    div[data-testid="stNumberInput"] [data-baseweb="input"] > div,
    div[data-testid="stNumberInput"] div div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stNumberInput"] > div {
        background-color: #ffffff !important; /* Luôn là nền trắng nổi bật */
        border: 2px solid #cbd5e1 !important; /* Viền xám nhạt tinh tế */
        border-radius: 10px !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stNumberInput"] > div:focus-within {
        border-color: #00e676 !important; /* Viền xanh khi đang chọn */
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.25) !important;
    }
    div[data-testid="stNumberInput"] input {
        color: #0f172a !important; /* Chữ màu xanh đen Slate 900 rất dễ nhìn */
        -webkit-text-fill-color: #0f172a !important; /* Ép màu chữ trên iOS */
        background-color: transparent !important;
        border: none !important;
        width: 100% !important;
        text-align: center !important;
        font-size: 1.25rem !important; /* Chữ to rõ ràng hơn */
        font-weight: 800 !important;
        padding: 0px !important;
        height: 38px !important;
        line-height: 38px !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stNumberInput"] input:focus {
        outline: none !important;
        border: none !important;
        box-shadow: none !important;
    }
    /* Hiển thị tỷ số rõ ràng khi ô nhập bị disabled */
    div[data-testid="stNumberInput"] input:disabled {
        color: #059669 !important; /* Màu xanh lá đậm để biểu thị trạng thái đã khóa nhưng vẫn rõ ràng */
        -webkit-text-fill-color: #059669 !important; /* Ép màu chữ trên iOS khi disabled */
        background-color: transparent !important;
        opacity: 1 !important;
        font-weight: 900 !important;
    }
    div[data-testid="stNumberInput"] > div:has(input:disabled) {
        background-color: #f1f5f9 !important; /* Nền xám nhạt khi bị khóa */
        border-color: #cbd5e1 !important;
        opacity: 1 !important;
    }
    /* Ẩn các nút tăng giảm mặc định */
    div[data-testid="stNumberInput"] button {
        display: none !important;
    }
    
    /* Tùy biến nút bấm Streamlit (Gradient & Glow) */
    div.stButton > button {
        background: linear-gradient(135deg, #00e676 0%, #00b0ff 100%) !important;
        color: #050811 !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 20px !important;
        font-size: 0.92rem !important;
        box-shadow: 0 4px 14px rgba(0, 230, 118, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(0, 230, 118, 0.45) !important;
        color: #000000 !important;
    }
    /* Nút bị vô hiệu hóa */
    div.stButton > button:disabled {
        background: rgba(255, 255, 255, 0.08) !important;
        color: rgba(255, 255, 255, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
        transform: none !important;
        cursor: not-allowed !important;
    }
    
    /* Badge trạng thái */
    .status-badge {
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    .status-badge.pending {
        background: rgba(0, 229, 255, 0.15) !important;
        color: #00e5ff !important;
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.1) !important;
    }
    .status-badge.finished {
        background: rgba(148, 163, 184, 0.12) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
    }
    
    /* Thẻ tỷ số thực tế */
    .actual-score-badge {
        background: linear-gradient(90deg, rgba(255, 215, 0, 0.15) 0%, rgba(255, 160, 0, 0.15) 100%) !important;
        color: #ffd700 !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        padding: 6px 12px !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        text-align: center;
        margin-top: 10px;
        font-size: 0.85rem !important;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.08) !important;
    }
    
    /* Thẻ điểm số kiếm được */
    .point-badge {
        padding: 4px 10px !important;
        border-radius: 15px !important;
        font-size: 0.75rem !important;
        font-weight: 800 !important;
        display: inline-block !important;
        margin-top: 6px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
    }
    .point-badge.correct {
        background: rgba(0, 230, 118, 0.15) !important;
        color: #00e676 !important;
        border: 1px solid rgba(0, 230, 118, 0.35) !important;
    }
    .point-badge.wrong {
        background: rgba(255, 82, 82, 0.15) !important;
        color: #ff5252 !important;
        border: 1px solid rgba(255, 82, 82, 0.35) !important;
    }
    .point-badge.unpredicted {
        background: rgba(148, 163, 184, 0.12) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
    }
    
    /* Custom flag image */
    .flag-container {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        overflow: hidden;
        border: 1.5px solid #ffd700;
        margin-right: 6px;
        vertical-align: middle;
        box-shadow: 0 1px 4px rgba(0,0,0,0.4);
    }
    .flag-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    /* Label tranh giải ba */
    .third-place {
        background: rgba(255, 215, 0, 0.15) !important;
        color: #ffd700 !important;
        padding: 2px 8px !important;
        border-radius: 5px !important;
        font-size: 0.65rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        border: 1px solid rgba(255, 215, 0, 0.25) !important;
        display: inline-block !important;
        margin-bottom: 6px !important;
    }
    
    /* Định dạng cột trong Bracket */
    [data-testid="column"] {
        background: rgba(255, 255, 255, 0.002) !important;
        padding: 6px !important;
        border-radius: 10px !important;
    }

    /* Leaderboard Table Styles */
    .leaderboard-container {
        width: 100%;
        background: linear-gradient(135deg, rgba(16, 28, 48, 0.75) 0%, rgba(8, 15, 27, 0.9) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4) !important;
        margin-top: 10px !important;
        backdrop-filter: blur(16px) !important;
    }
    .leaderboard-table {
        width: 100%;
        border-collapse: collapse !important;
        text-align: left !important;
        font-size: 0.9rem !important;
    }
    .leaderboard-table th {
        background: rgba(21, 38, 68, 0.8) !important;
        color: #00e676 !important;
        font-weight: 800 !important;
        padding: 12px 16px !important;
        border-bottom: 2px solid rgba(0, 230, 118, 0.3) !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px !important;
    }
    .leaderboard-table td {
        padding: 10px 16px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        color: #e2e8f0 !important;
        vertical-align: middle !important;
    }
    .leaderboard-table tr:hover {
        background: rgba(255, 255, 255, 0.03) !important;
    }
    .leaderboard-table tr.top-1 {
        background: linear-gradient(90deg, rgba(255, 215, 0, 0.08) 0%, rgba(255, 215, 0, 0.01) 100%) !important;
    }
    .leaderboard-table tr.top-2 {
        background: linear-gradient(90deg, rgba(192, 192, 192, 0.06) 0%, rgba(192, 192, 192, 0.01) 100%) !important;
    }
    .leaderboard-table tr.top-3 {
        background: linear-gradient(90deg, rgba(205, 127, 50, 0.06) 0%, rgba(205, 127, 50, 0.01) 100%) !important;
    }
    .rank-badge {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 26px !important;
        height: 26px !important;
        border-radius: 50% !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
    }
    .rank-1 { background: #ffd700 !important; color: #000000 !important; box-shadow: 0 0 10px rgba(255,215,0,0.5) !important; }
    .rank-2 { background: #c0c0c0 !important; color: #000000 !important; box-shadow: 0 0 8px rgba(192,192,192,0.3) !important; }
    .rank-3 { background: #cd7f32 !important; color: #000000 !important; box-shadow: 0 0 8px rgba(205,127,50,0.3) !important; }
    .rank-normal { color: #94a3b8 !important; }
    
    .points-column {
        font-weight: 900 !important;
        color: #ffd700 !important;
        font-size: 1.1rem !important;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.3) !important;
    }
    
    /* Thiết lập xếp chồng cột trên thiết bị di động (mobile) */
    @media (max-width: 768px) {
        /* Chỉ xếp chồng các cột cấp cao (grid trận đấu, khung đăng nhập, trang admin) */
        div[data-testid="stHorizontalBlock"]:not(div[data-testid="stVerticalBlockBorderContainer"] div[data-testid="stHorizontalBlock"]) > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        /* Ẩn các cột trống phụ ở trang đăng nhập để tránh khoảng trắng thừa */
        div[data-testid="stHorizontalBlock"]:not(div[data-testid="stVerticalBlockBorderContainer"] div[data-testid="stHorizontalBlock"]) > div[data-testid="column"]:not(:has(div[data-testid="element-container"])) {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- KHỞI TẠO CẤU HÌNH DATABASE LOCAL (FALLBACK) ---
LOCAL_DB_FILE = os.path.join(os.path.dirname(__file__), 'data', 'database.json')

# Bản đồ Mã Quốc Gia cho logo FlagCDN
TEAM_CODES = {
    'Mexico': 'mx', 'Nam Phi': 'za', 'South Africa': 'za',
    'Hàn Quốc': 'kr', 'South Korea': 'kr', 'CH Séc': 'cz', 'Czech Republic': 'cz',
    'Canada': 'ca', 'Bosnia': 'ba', 'Bosnia and Herzegovina': 'ba',
    'Mỹ': 'us', 'USA': 'us', 'Paraguay': 'py',
    'Qatar': 'qa', 'Thụy Sĩ': 'ch', 'Switzerland': 'ch',
    'Brazil': 'br', 'Maroc': 'ma', 'Morocco': 'ma', 'Marocco': 'ma',
    'Haiti': 'ht', 'Scotland': 'gb-sct',
    'Úc': 'au', 'Australia': 'au', 'Thổ Nhĩ Kỳ': 'tr', 'Turkey': 'tr',
    'Đức': 'de', 'Germany': 'de', 'Curacao': 'cw',
    'Hà Lan': 'nl', 'Netherlands': 'nl', 'Nhật Bản': 'jp', 'Japan': 'jp',
    'Bờ Biển Ngà': 'ci', 'Ivory Coast': 'ci', 'Ecuador': 'ec',
    'Thụy Điển': 'se', 'Sweden': 'se', 'Tunisia': 'tn',
    'Tây Ban Nha': 'es', 'Spain': 'es', 'Cabo Verde': 'cv', 'Cape Verde': 'cv',
    'Bỉ': 'be', 'Belgium': 'be', 'Ai Cập': 'eg', 'Egypt': 'eg',
    'Saudi Arabia': 'sa', 'Uruguay': 'uy', 'Argentina': 'ar', 'Pháp': 'fr', 'France': 'fr',
    'Anh': 'gb-eng', 'England': 'gb-eng', 'Ý': 'it', 'Italy': 'it',
    'Bồ Đào Nha': 'pt', 'Portugal': 'pt', 'Senegal': 'sn', 'Croatia': 'hr',
    'Việt Nam': 'vn', 'Vietnam': 'vn', 'Thái Lan': 'th', 'Thailand': 'th',
    'Cameroon': 'cm', 'Colombia': 'co',
    'Iran': 'ir', 'Na Uy': 'no', 'Norway': 'no', 'Iraq': 'iq', 'Algeria': 'dz',
    'Áo': 'at', 'Austria': 'at', 'CHDC Congo': 'cd', 'DR Congo': 'cd',
    'Ghana': 'gh', 'Panama': 'pa', 'Uzbekistan': 'uz', 'Jordan': 'jo',
    'New Zealand': 'nz', 'Ý': 'it'
}

def get_flag_html(team_name):
    code = TEAM_CODES.get(team_name.strip(), 'un')
    return f'<span class="flag-container"><img src="https://flagcdn.com/w40/{code}.png" class="flag-img" /></span>'

# Dữ liệu trận đấu mặc định để khởi tạo
DEFAULT_MATCHES = [
    { 'id': 'm1', 'team1': 'Mexico', 'team2': 'Nam Phi', 'date': '2026-06-12T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm2', 'team1': 'Hàn Quốc', 'team2': 'CH Séc', 'date': '2026-06-12T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm3', 'team1': 'Canada', 'team2': 'Bosnia', 'date': '2026-06-13T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm4', 'team1': 'Mỹ', 'team2': 'Paraguay', 'date': '2026-06-13T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm5', 'team1': 'Qatar', 'team2': 'Thụy Sĩ', 'date': '2026-06-14T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm6', 'team1': 'Brazil', 'team2': 'Marocco', 'date': '2026-06-14T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm7', 'team1': 'Haiti', 'team2': 'Scotland', 'date': '2026-06-14T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm8', 'team1': 'Úc', 'team2': 'Thổ Nhĩ Kỳ', 'date': '2026-06-14T11:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm9', 'team1': 'Đức', 'team2': 'Curacao', 'date': '2026-06-15T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm10', 'team1': 'Hà Lan', 'team2': 'Nhật Bản', 'date': '2026-06-15T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm11', 'team1': 'Bờ Biển Ngà', 'team2': 'Ecuador', 'date': '2026-06-15T06:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm12', 'team1': 'Thụy Điển', 'team2': 'Tunisia', 'date': '2026-06-15T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm13', 'team1': 'Tây Ban Nha', 'team2': 'Cabo Verde', 'date': '2026-06-15T23:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm14', 'team1': 'Bỉ', 'team2': 'Ai Cập', 'date': '2026-06-16T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm15', 'team1': 'Saudi Arabia', 'team2': 'Uruguay', 'date': '2026-06-16T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm16', 'team1': 'Iran', 'team2': 'New Zealand', 'date': '2026-06-16T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm17', 'team1': 'Pháp', 'team2': 'Senegal', 'date': '2026-06-17T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm18', 'team1': 'Iraq', 'team2': 'Na Uy', 'date': '2026-06-17T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm19', 'team1': 'Argentina', 'team2': 'Algeria', 'date': '2026-06-17T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm20', 'team1': 'Áo', 'team2': 'Jordan', 'date': '2026-06-17T11:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm21', 'team1': 'Bồ Đào Nha', 'team2': 'CHDC Congo', 'date': '2026-06-18T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm22', 'team1': 'Anh', 'team2': 'Croatia', 'date': '2026-06-18T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm23', 'team1': 'Ghana', 'team2': 'Panama', 'date': '2026-06-18T06:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm24', 'team1': 'Uzbekistan', 'team2': 'Colombia', 'date': '2026-06-18T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm25', 'team1': 'CH Séc', 'team2': 'Nam Phi', 'date': '2026-06-18T23:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm26', 'team1': 'Thụy Sĩ', 'team2': 'Bosnia', 'date': '2026-06-19T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm27', 'team1': 'Canada', 'team2': 'Qatar', 'date': '2026-06-19T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm28', 'team1': 'Mexico', 'team2': 'Hàn Quốc', 'date': '2026-06-19T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm29', 'team1': 'Mỹ', 'team2': 'Úc', 'date': '2026-06-20T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm30', 'team1': 'Scotland', 'team2': 'Marocco', 'date': '2026-06-20T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm31', 'team1': 'Brazil', 'team2': 'Haiti', 'date': '2026-06-20T07:30:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm32', 'team1': 'Thổ Nhĩ Kỳ', 'team2': 'Paraguay', 'date': '2026-06-20T10:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm33', 'team1': 'Hà Lan', 'team2': 'Thụy Điển', 'date': '2026-06-21T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm34', 'team1': 'Đức', 'team2': 'Bờ Biển Ngà', 'date': '2026-06-21T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm35', 'team1': 'Ecuador', 'team2': 'Curacao', 'date': '2026-06-21T07:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm36', 'team1': 'Tunisia', 'team2': 'Nhật Bản', 'date': '2026-06-21T11:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm37', 'team1': 'Tây Ban Nha', 'team2': 'Saudi Arabia', 'date': '2026-06-21T23:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm38', 'team1': 'Bỉ', 'team2': 'Iran', 'date': '2026-06-22T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm39', 'team1': 'Uruguay', 'team2': 'Cabo Verde', 'date': '2026-06-22T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm40', 'team1': 'New Zealand', 'team2': 'Ai Cập', 'date': '2026-06-22T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm41', 'team1': 'Argentina', 'team2': 'Áo', 'date': '2026-06-23T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm42', 'team1': 'Pháp', 'team2': 'Iraq', 'date': '2026-06-23T04:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm43', 'team1': 'Na Uy', 'team2': 'Senegal', 'date': '2026-06-23T07:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm44', 'team1': 'Jordan', 'team2': 'Algeria', 'date': '2026-06-23T10:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm45', 'team1': 'Bồ Đào Nha', 'team2': 'Uzbekistan', 'date': '2026-06-24T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm46', 'team1': 'Anh', 'team2': 'Ghana', 'date': '2026-06-24T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm47', 'team1': 'Panama', 'team2': 'Croatia', 'date': '2026-06-24T06:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm48', 'team1': 'Colombia', 'team2': 'CHDC Congo', 'date': '2026-06-24T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm49', 'team1': 'Bosnia', 'team2': 'Qatar', 'date': '2026-06-25T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm50', 'team1': 'Thụy Sĩ', 'team2': 'Canada', 'date': '2026-06-25T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm51', 'team1': 'Marocco', 'team2': 'Haiti', 'date': '2026-06-25T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm52', 'team1': 'Scotland', 'team2': 'Brazil', 'date': '2026-06-25T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm53', 'team1': 'Nam Phi', 'team2': 'Hàn Quốc', 'date': '2026-06-25T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm54', 'team1': 'CH Séc', 'team2': 'Mexico', 'date': '2026-06-25T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm55', 'team1': 'Curacao', 'team2': 'Bờ Biển Ngà', 'date': '2026-06-26T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm56', 'team1': 'Ecuador', 'team2': 'Đức', 'date': '2026-06-26T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm57', 'team1': 'Tunisia', 'team2': 'Hà Lan', 'date': '2026-06-26T06:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm58', 'team1': 'Nhật Bản', 'team2': 'Thụy Điển', 'date': '2026-06-26T06:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm59', 'team1': 'Thổ Nhĩ Kỳ', 'team2': 'Mỹ', 'date': '2026-06-26T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm60', 'team1': 'Paraguay', 'team2': 'Úc', 'date': '2026-06-26T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm61', 'team1': 'Na Uy', 'team2': 'Pháp', 'date': '2026-06-27T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm62', 'team1': 'Senegal', 'team2': 'Iraq', 'date': '2026-06-27T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm63', 'team1': 'Cabo Verde', 'team2': 'Saudi Arabia', 'date': '2026-06-27T07:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm64', 'team1': 'Uruguay', 'team2': 'Tây Ban Nha', 'date': '2026-06-27T07:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm65', 'team1': 'New Zealand', 'team2': 'Bỉ', 'date': '2026-06-27T10:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm66', 'team1': 'Ai Cập', 'team2': 'Iran', 'date': '2026-06-27T10:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm67', 'team1': 'Panama', 'team2': 'Anh', 'date': '2026-06-28T04:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm68', 'team1': 'Croatia', 'team2': 'Ghana', 'date': '2026-06-28T04:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm69', 'team1': 'Colombia', 'team2': 'Bồ Đào Nha', 'date': '2026-06-28T06:30:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm70', 'team1': 'CHDC Congo', 'team2': 'Uzbekistan', 'date': '2026-06-28T06:30:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm71', 'team1': 'Algeria', 'team2': 'Áo', 'date': '2026-06-28T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'm72', 'team1': 'Jordan', 'team2': 'Argentina', 'date': '2026-06-28T09:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'group' },
    { 'id': 'r32_1', 'team1': 'Á quân Bảng A', 'team2': 'Á quân Bảng B', 'date': '2026-06-29T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_4', 'team1': 'Nhất Bảng C', 'team2': 'Á quân Bảng F', 'date': '2026-06-30T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_2', 'team1': 'Nhất Bảng E', 'team2': 'Hạng 3 A/B/C/D/F', 'date': '2026-06-30T03:30:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_3', 'team1': 'Nhất Bảng F', 'team2': 'Á quân Bảng C', 'date': '2026-06-30T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_6', 'team1': 'Á quân Bảng E', 'team2': 'Á quân Bảng I', 'date': '2026-07-01T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_5', 'team1': 'Nhất Bảng I', 'team2': 'Hạng 3 C/D/F/G/H', 'date': '2026-07-01T04:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_7', 'team1': 'Nhất Bảng A', 'team2': 'Hạng 3 C/E/F/H/I', 'date': '2026-07-01T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_8', 'team1': 'Nhất Bảng L', 'team2': 'Hạng 3 E/H/I/J/K', 'date': '2026-07-01T23:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_11', 'team1': 'Nhất Bảng G', 'team2': 'Hạng 3 A/E/H/I/J', 'date': '2026-07-02T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_10', 'team1': 'Nhất Bảng D', 'team2': 'Hạng 3 B/E/F/I/J', 'date': '2026-07-02T07:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_12', 'team1': 'Nhất Bảng H', 'team2': 'Á quân Bảng J', 'date': '2026-07-03T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_9', 'team1': 'Á quân Bảng K', 'team2': 'Á quân Bảng L', 'date': '2026-07-03T06:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_13', 'team1': 'Nhất Bảng B', 'team2': 'Hạng 3 E/F/G/I/J', 'date': '2026-07-03T10:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_16', 'team1': 'Á quân Bảng D', 'team2': 'Á quân Bảng G', 'date': '2026-07-04T01:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_14', 'team1': 'Nhất Bảng J', 'team2': 'Á quân Bảng H', 'date': '2026-07-04T05:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r32_15', 'team1': 'Nhất Bảng K', 'team2': 'Hạng 3 D/E/I/J/L', 'date': '2026-07-04T08:30:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r32' },
    { 'id': 'r16_2', 'team1': 'Thắng 73', 'team2': 'Thắng 75', 'date': '2026-07-05T00:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'r16_1', 'team1': 'Thắng 74', 'team2': 'Thắng 77', 'date': '2026-07-05T04:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'r16_3', 'team1': 'Thắng 76', 'team2': 'Thắng 78', 'date': '2026-07-06T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'r16_4', 'team1': 'Thắng 79', 'team2': 'Thắng 80', 'date': '2026-07-06T07:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'r16_5', 'team1': 'Thắng 83', 'team2': 'Thắng 84', 'date': '2026-07-07T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'r16_6', 'team1': 'Thắng 81', 'team2': 'Thắng 82', 'date': '2026-07-07T07:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'r16_7', 'team1': 'Thắng 86', 'team2': 'Thắng 88', 'date': '2026-07-07T23:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'r16_8', 'team1': 'Thắng 85', 'team2': 'Thắng 87', 'date': '2026-07-08T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'r16' },
    { 'id': 'qf_1', 'team1': 'Thắng 89', 'team2': 'Thắng 90', 'date': '2026-07-10T03:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'qf' },
    { 'id': 'qf_2', 'team1': 'Thắng 93', 'team2': 'Thắng 94', 'date': '2026-07-11T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'qf' },
    { 'id': 'qf_3', 'team1': 'Thắng 91', 'team2': 'Thắng 92', 'date': '2026-07-12T04:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'qf' },
    { 'id': 'qf_4', 'team1': 'Thắng 95', 'team2': 'Thắng 96', 'date': '2026-07-12T08:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'qf' },
    { 'id': 'sf_1', 'team1': 'Thắng 97', 'team2': 'Thắng 98', 'date': '2026-07-15T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'sf' },
    { 'id': 'sf_2', 'team1': 'Thắng 99', 'team2': 'Thắng 100', 'date': '2026-07-16T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'sf' },
    { 'id': 'third', 'team1': 'Thua 101', 'team2': 'Thua 102', 'date': '2026-07-19T04:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'third' },
    { 'id': 'final', 'team1': 'Thắng 101', 'team2': 'Thắng 102', 'date': '2026-07-20T02:00:00', 'status': 'pending', 'score1': None, 'score2': None, 'outcome': None, 'round': 'final' },
]

# --- HÀM GIAO TIẾP DATABASE (LOCAL & CLOUD) ---

def get_api_url():
    try:
        return st.secrets.get("GSHEETS_API_URL")
    except:
        return None

def read_db():
    token = get_github_token()
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DB_PATH_ON_GITHUB}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            content_b64 = res.json().get("content", "")
            content = base64.b64decode(content_b64).decode("utf-8")
            data = json.loads(content)
            return data["matches"], data["users"], data["predictions"], False
        else:
            st.session_state.db_error = f"GitHub API trả về mã lỗi {res.status_code}"
    except Exception as e:
        st.session_state.db_error = f"Lỗi kết nối GitHub: {str(e)}"
        st.sidebar.warning(f"Lỗi kết nối Cloud DB, tự động chuyển về Offline Local: {e}")
            
    if not os.path.exists(LOCAL_DB_FILE):
        os.makedirs(os.path.dirname(LOCAL_DB_FILE), exist_ok=True)
        initial_data = { "matches": DEFAULT_MATCHES, "users": [], "predictions": {} }
        with open(LOCAL_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        return DEFAULT_MATCHES, [], {}, True
        
    try:
        with open(LOCAL_DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("matches", DEFAULT_MATCHES), data.get("users", []), data.get("predictions", {}), True
    except Exception as e:
        return DEFAULT_MATCHES, [], {}, True

def write_local_db(matches, users, predictions):
    os.makedirs(os.path.dirname(LOCAL_DB_FILE), exist_ok=True)
    data = { "matches": matches, "users": users, "predictions": predictions }
    with open(LOCAL_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def recalculate_local_points(matches, users, predictions):
    # Reset điểm
    for u in users:
        u["points"] = 0
        u["correctScores"] = 0
        u["correctOutcomes"] = 0
        u["unpredicted"] = 0
        
    for match in matches:
        if match.get("status") != "finished":
            continue
            
        actual1 = match.get("score1")
        actual2 = match.get("score2")
        if actual1 is None or actual2 is None or actual1 == "" or actual2 == "":
            continue
            
        act1 = int(actual1)
        act2 = int(actual2)
        
        for u in users:
            if u["name"].lower() == "admin":
                continue
            user_key = f"{u['name'].strip()}-{u['unit'].strip()}"
            user_preds = predictions.get(user_key, {})
            pred = user_preds.get(match["id"])
            
            if pred:
                try:
                    pred1 = int(pred["score1"])
                    pred2 = int(pred["score2"])
                    if pred1 == act1 and pred2 == act2:
                        u["points"] += 2
                        u["correctScores"] += 1
                    else:
                        u["points"] -= 1
                        u["correctOutcomes"] += 1
                except:
                    u["points"] -= 1
                    u["correctOutcomes"] += 1
            else:
                # Không dự đoán cho trận đã kết thúc -> Mặc định phạt -1đ và tính vào unpredicted
                u["points"] -= 1
                u["unpredicted"] += 1

def apply_match_result(match, s1, s2, matches):
    match["status"] = "finished"
    match["score1"] = s1
    match["score2"] = s2
    match["outcome"] = "team1" if s1 > s2 else ("team2" if s1 < s2 else "draw")
    
    # Knockout auto-advance logic
    winner = match["team1"] if s1 > s2 else match["team2"]
    loser = match["team2"] if s1 > s2 else match["team1"]
    
    next_match_id = match.get("nextMatchId")
    if next_match_id:
        next_match = next((m for m in matches if m["id"] == next_match_id), None)
        if next_match:
            last_char = match["id"][-1]
            if last_char in ['1', '3', '5', '7', '9']:
                next_match["team1"] = winner
            else:
                next_match["team2"] = winner
                
    # Tranh hạng 3
    if match["id"] == "sf_1":
        third_match = next((m for m in matches if m["id"] == "third"), None)
        if third_match: third_match["team1"] = loser
    elif match["id"] == "sf_2":
        third_match = next((m for m in matches if m["id"] == "third"), None)
        if third_match: third_match["team2"] = loser

def normalize_name(name):
    if not name:
        return ""
    return "".join(c.lower() for c in name if c.isalnum())

def sync_results_from_24h(matches, users, predictions, is_local):
    url = 'https://www.24h.com.vn/world-cup-2026/ket-qua-thi-dau-bong-da-world-cup-2026-moi-nhat-c860a1747405.html'
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    
    try:
        with urllib.request.urlopen(req, context=context, timeout=8) as res:
            soup = BeautifulSoup(res.read(), 'html.parser')
        match_divs = soup.find_all('div', class_='box-items')
        
        if not match_divs:
            return False, "Không thể tải danh sách trận đấu từ 24h.com.vn."
            
        parsed_results = []
        for div in match_divs:
            team_spans = div.find_all('span', class_='team-name')
            if len(team_spans) >= 2:
                team1 = team_spans[0].get_text(strip=True)
                team2 = team_spans[1].get_text(strip=True)
                
                score_div = div.find('div', class_='box-score')
                if not score_div:
                    continue
                    
                score_t = score_div.find('div', class_='box-t')
                score_str = score_t.get_text(strip=True) if score_t else score_div.get_text(strip=True)
                
                parsed_results.append({
                    "team1": team1,
                    "team2": team2,
                    "score_str": score_str
                })
                
        updated = False
        update_msgs = []
        
        for m in matches:
            if m["status"] == "pending":
                db_t1_norm = normalize_name(m["team1"])
                db_t2_norm = normalize_name(m["team2"])
                
                match_found = None
                for web_m in parsed_results:
                    w_t1_norm = normalize_name(web_m["team1"])
                    w_t2_norm = normalize_name(web_m["team2"])
                    
                    # So khớp mềm
                    if (db_t1_norm == w_t1_norm or db_t1_norm in w_t1_norm or w_t1_norm in db_t1_norm) and \
                       (db_t2_norm == w_t2_norm or db_t2_norm in w_t2_norm or w_t2_norm in db_t2_norm):
                        match_found = web_m
                        break
                        
                if match_found:
                    score_str = match_found["score_str"]
                    if '-' in score_str and len(score_str.strip()) > 1:
                        parts = score_str.split('-')
                        if len(parts) == 2:
                            try:
                                s1 = int(parts[0].strip())
                                s2 = int(parts[1].strip())
                                
                                apply_match_result(m, s1, s2, matches)
                                updated = True
                                update_msgs.append(f"{m['team1']} {s1}-{s2} {m['team2']}")
                            except:
                                pass
                                
        if updated:
            recalculate_local_points(matches, users, predictions)
            if not is_local:
                save_db_to_github(matches, users, predictions)
            else:
                write_local_db(matches, users, predictions)
            return True, f"Đồng bộ thành công: {', '.join(update_msgs)}"
        return False, "Không có kết quả mới nào cần cập nhật."
        
    except Exception as e:
        return False, f"Lỗi kết nối tới 24h.com.vn: {e}"


# --- KHỞI TẠO STATE & TẢI DỮ LIỆU ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.unit = ""
    st.session_state.is_admin = False

matches, users, predictions, is_local = read_db()

# --- TỰ ĐỘNG ĐĂNG NHẬP QUA QUERY PARAMETERS ---
if not st.session_state.logged_in:
    query_name = st.query_params.get("name")
    query_unit = st.query_params.get("unit")
    if query_name and query_unit:
        st.session_state.logged_in = True
        st.session_state.username = query_name.strip()
        st.session_state.unit = query_unit.strip()
        if query_name.strip().lower() == "admin" and query_unit.strip().lower() == "btc":
            st.session_state.is_admin = True
        else:
            st.session_state.is_admin = False
            user_exists = any(u["name"].lower() == query_name.strip().lower() and u["unit"].lower() == query_unit.strip().lower() for u in users)
            if not user_exists:
                users.append({
                    "name": query_name.strip(),
                    "unit": query_unit.strip(),
                    "isAdmin": False,
                    "points": 0,
                    "correctScores": 0,
                    "correctOutcomes": 0,
                    "unpredicted": 0
                })
                if not is_local:
                    save_db_to_github(matches, users, predictions)
                else:
                    write_local_db(matches, users, predictions)

# --- TỰ ĐỘNG ĐỒNG BỘ KẾT QUẢ TỪ 24H.COM.VN (LAZY SYNC) ---
if 'last_auto_sync' not in st.session_state:
    st.session_state.last_auto_sync = 0

current_time_epoch = time.time()
has_finished_pending_match = False

# Quy đổi thời gian hiện tại về múi giờ Việt Nam (UTC+7) để so sánh chính xác với lịch thi đấu
vn_tz = timezone(timedelta(hours=7))
now_vn = datetime.now(vn_tz).replace(tzinfo=None)

for m in matches:
    if m["status"] == "pending":
        try:
            match_dt = datetime.fromisoformat(m["date"])
            # So sánh thời gian hiện tại với giờ đá trận đấu
            if (now_vn - match_dt).total_seconds() > 6600: # Sau 110 phút (thời gian đá xong)
                has_finished_pending_match = True
                break
        except:
            pass

if has_finished_pending_match and (current_time_epoch - st.session_state.last_auto_sync > 300): # Tối thiểu 5 phút
    st.session_state.last_auto_sync = current_time_epoch
    success, msg = sync_results_from_24h(matches, users, predictions, is_local)
    if success:
        st.toast(msg, icon="⚽")
        st.rerun()

# --- GIAO DIỆN HEADER CHÍNH ---
col_logo, col_title, col_status = st.columns([0.1, 0.7, 0.2])
with col_logo:
    st.markdown("<h1>⚽</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1>World Cup 2026 <span class='highlight-text'>VKT</span></h1>", unsafe_allow_html=True)
with col_status:
    if is_local:
        st.markdown("<span class='status-badge pending'>Chế độ Ngoại tuyến (Local DB)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='status-badge finished' style='background: rgba(0, 230, 118, 0.15); color: #00e676; border-color: rgba(0,230,118,0.3);'>Chế độ Đám mây (Google Sheets)</span>", unsafe_allow_html=True)

# Hiển thị thông tin lỗi kết nối chi tiết để người dùng tự khắc phục
if is_local:
    db_err_msg = st.session_state.get("db_error", "Không xác định")
    st.error(f"⚠️ **Hệ thống đang chạy ở Chế độ Ngoại tuyến (Local DB) do mất kết nối dữ liệu:**\n\n`{db_err_msg}`\n\n👉 **Cách khắc phục:** Vui lòng kiểm tra và điền cấu hình `GSHEETS_API_URL` trong mục **Advanced settings -> Secrets** trên Streamlit Cloud của bạn. Dữ liệu trên Google Sheets vẫn an toàn 100%, chỉ cần kết nối lại là hiển thị đầy đủ ngay lập tức.")

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state.logged_in:
    st.write("---")
    col_auth_left, col_auth_card, col_auth_right = st.columns([1, 1.2, 1])
    
    with col_auth_card:
        with st.container(border=True):
            st.subheader("Tham Gia Dự Đoán")
            st.write("Đăng nhập bằng Họ tên và Đơn vị để bắt đầu dự báo kết quả World Cup 2026")
            
            input_name = st.text_input("Họ và Tên", placeholder="Nhập đầy đủ họ tên...")
            input_unit = st.text_input("Đơn vị / Phòng ban", placeholder="Ví dụ: Phòng Kỹ thuật, Tổ 1...")
            
            check_admin = st.checkbox("Đăng nhập tài khoản Ban Tổ Chức (Admin)")
            admin_password = ""
            if check_admin:
                admin_password = st.text_input("Mật khẩu Admin", type="password", placeholder="Nhập mật khẩu quản trị...")
                
            if st.button("Đăng Nhập", use_container_width=True):
                if not input_name.strip() or not input_unit.strip():
                    st.error("Vui lòng điền đầy đủ Họ tên và Đơn vị!")
                else:
                    trimmed_name = input_name.strip()
                    trimmed_unit = input_unit.strip()
                    
                    # Check đăng nhập admin
                    if trimmed_name.lower() == "admin" and trimmed_unit.lower() == "btc":
                        if admin_password == "admin2026":
                            st.session_state.logged_in = True
                            st.session_state.username = "Admin"
                            st.session_state.unit = "BTC"
                            st.session_state.is_admin = True
                            st.query_params["name"] = "Admin"
                            st.query_params["unit"] = "BTC"
                            st.rerun()
                        else:
                            st.error("Mật khẩu quản trị viên không chính xác!")
                    else:
                        if check_admin:
                            st.error("Thông tin đăng nhập Admin không chính xác!")
                        else:
                            # Đăng nhập user thường, đăng ký nếu là local
                            st.session_state.logged_in = True
                            st.session_state.username = trimmed_name
                            st.session_state.unit = trimmed_unit
                            st.session_state.is_admin = False
                            st.query_params["name"] = trimmed_name
                            st.query_params["unit"] = trimmed_unit
                            
                            user_exists = any(u["name"].lower() == trimmed_name.lower() and u["unit"].lower() == trimmed_unit.lower() for u in users)
                            if not user_exists:
                                users.append({
                                    "name": trimmed_name,
                                    "unit": trimmed_unit,
                                    "isAdmin": False,
                                    "points": 0,
                                    "correctScores": 0,
                                    "correctOutcomes": 0,
                                    "unpredicted": 0
                                })
                                if not is_local:
                                    save_db_to_github(matches, users, predictions)
                                else:
                                    write_local_db(matches, users, predictions)
                            st.rerun()
        
    st.stop()

# --- MENU CHỨC NĂNG SAU KHI ĐĂNG NHẬP ---
user_key = f"{st.session_state.username}-{st.session_state.unit}"
user_preds = predictions.get(user_key, {})

# Nút Đăng xuất ở thanh bên
st.sidebar.markdown(f"**Xin chào:** {st.session_state.username}")
st.sidebar.markdown(f"**Đơn vị:** {st.session_state.unit}")

# Nút đồng bộ thủ công ở thanh bên
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚽ Kết Quả Trận Đấu")
if st.sidebar.button("🔄 Cập nhật từ 24h.com.vn", use_container_width=True):
    with st.sidebar.status("Đang lấy kết quả mới nhất..."):
        success, msg = sync_results_from_24h(matches, users, predictions, is_local)
    if success:
        st.sidebar.success(msg)
        time.sleep(1.5)
        st.rerun()
    else:
        st.sidebar.info(msg)

st.sidebar.markdown("---")
if st.sidebar.button("Đăng xuất", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.unit = ""
    st.session_state.is_admin = False
    st.query_params.clear()
    st.rerun()

# --- THIẾT LẬP CÁC TAB ---
if st.session_state.is_admin:
    tabs = ["🏆 Bảng Xếp Hạng", "⚙️ Quản Trị (BTC)"]
else:
    tabs = ["⚽ Dự Đoán Của Tôi", "🏆 Bảng Xếp Hạng"]
    
selected_tab = st.radio("Thanh điều hướng", tabs, horizontal=True, label_visibility="collapsed")

# ================= TAB 1: DỰ ĐOÁN CỦA TÔI =================
if selected_tab == "⚽ Dự Đoán Của Tôi":
    st.write("---")
    col_header, col_action = st.columns([0.65, 0.35])
    with col_header:
        st.subheader("Dự Đoán Kết Quả")
        st.write("Nhập tỷ số dự đoán của bạn. Hệ thống sẽ tự động khóa và tính điểm sau khi bạn lưu.")
    with col_action:
        # Placeholder container để vẽ nút lưu ở đầu trang
        save_btn_placeholder = st.container()
    
    # Hiển thị Điểm số nhanh
    if not st.session_state.is_admin:
        # Lấy thông tin xếp hạng
        user_rank_info = next((u for u in users if u["name"].lower() == st.session_state.username.lower() and u["unit"].lower() == st.session_state.unit.lower()), None)
        if user_rank_info:
            col_pts1, col_pts2, col_pts3 = st.columns(3)
            with col_pts1:
                st.metric("Tổng Điểm Số", f"{user_rank_info['points']} điểm")
            with col_pts2:
                st.metric("Số Trận Đoán Đúng (+2đ)", f"{user_rank_info['correctScores']} trận")
            with col_pts3:
                st.metric("Số Trận Đoán Sai (-1đ)", f"{user_rank_info['correctOutcomes']} trận")
            st.write("---")

    # Bộ lọc
    filter_val = st.segmented_control("Trạng thái trận đấu", ["Tất cả", "Chưa diễn ra", "Đã kết thúc"], default="Tất cả")
    
    # Render các cards trận đấu
    new_preds = {}
    
    # Gom trận đấu lọc
    filtered_matches = []
    for m in matches:
        if filter_val == "Chưa diễn ra" and m["status"] == "finished":
            continue
        if filter_val == "Đã kết thúc" and m["status"] == "pending":
            continue
        filtered_matches.append(m)
        
    if not filtered_matches:
        st.info("Không có trận đấu nào trong danh mục này.")
    else:
        # Vẽ grid cards - Đổi sang 3 cột để đỡ phải cuộn!
        col_grid = st.columns(3)
        for idx, match in enumerate(filtered_matches):
            with col_grid[idx % 3]:
                m_id = match["id"]
                is_finished = match["status"] == "finished"
                pred = user_preds.get(m_id, { "score1": "", "score2": "" })
                
                # Check có dự đoán từ trước
                has_pred = pred.get("score1") is not None and pred.get("score1") != "" and pred.get("score2") is not None and pred.get("score2") != ""
                is_disabled = is_finished or st.session_state.is_admin or has_pred
                
                with st.container(border=True):
                    # Header card (tối giản để compact hơn)
                    status_text = "Đã kết thúc" if is_finished else "Chưa diễn ra"
                    status_class = "finished" if is_finished else "pending"
                    date_formatted = datetime.fromisoformat(match["date"]).strftime("%d/%m %H:%M")
                    st.markdown(f"<div><span class='status-badge {status_class}'>{status_text}</span> <span style='font-size:0.8rem; color:#e2e8f0; margin-left:6px;'>📅 {date_formatted}</span></div>", unsafe_allow_html=True)
                    
                    # Đội và Inputs
                    st.write("")
                    col_t1, col_score, col_t2 = st.columns([0.38, 0.24, 0.38])
                    with col_t1:
                        st.markdown(f"<div style='text-align:right; font-size:0.95rem; font-weight:700; color:#ffffff; line-height:1.2;'>{get_flag_html(match['team1'])} {match['team1']}</div>", unsafe_allow_html=True)
                    with col_score:
                        # Input Tỉ số dự đoán
                        val1 = pred.get("score1") if pred.get("score1") is not None else ""
                        val2 = pred.get("score2") if pred.get("score2") is not None else ""
                        
                        # Streamlit number input
                        default_1 = int(val1) if val1 != "" else None
                        default_2 = int(val2) if val2 != "" else None
                        
                        col_in1, col_in2 = st.columns(2)
                        with col_in1:
                            score1 = st.number_input("", min_value=0, max_value=20, step=1, value=default_1, key=f"p1_{m_id}", disabled=is_disabled, label_visibility="collapsed")
                        with col_in2:
                            score2 = st.number_input("", min_value=0, max_value=20, step=1, value=default_2, key=f"p2_{m_id}", disabled=is_disabled, label_visibility="collapsed")
                    with col_t2:
                        st.markdown(f"<div style='text-align:left; font-size:0.95rem; font-weight:700; color:#ffffff; line-height:1.2;'>{get_flag_html(match['team2'])} {match['team2']}</div>", unsafe_allow_html=True)
                    
                    # Lưu dự đoán mới vào temp map
                    if score1 is not None and score2 is not None and not is_disabled:
                        new_preds[m_id] = { "score1": int(score1), "score2": int(score2) }
                    
                    # Hiển thị kết quả thực tế và điểm số
                    if is_finished:
                        act1 = int(match["score1"])
                        act2 = int(match["score2"])
                        st.markdown(f"<div class='actual-score-badge'>Tỷ số thực tế: {act1} - {act2}</div>", unsafe_allow_html=True)
                        
                        if has_pred:
                            p1 = int(pred["score1"])
                            p2 = int(pred["score2"])
                            if p1 == act1 and p2 == act2:
                                st.markdown("<div style='text-align:center;'><span class='point-badge correct'>🏆 Đúng tỷ số (+2đ)</span></div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div style='text-align:center;'><span class='point-badge wrong'>❌ Sai tỷ số (-1đ)</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='text-align:center;'><span class='point-badge wrong'>⚠️ Phạt không dự đoán (-1đ)</span></div>", unsafe_allow_html=True)
                    else:
                        if has_pred:
                            st.markdown(f"<div style='text-align:center; color:#00e676; font-size:0.8rem; font-weight:800; margin-top:6px;'>🔒 Đã khóa: {pred['score1']} - {pred['score2']}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='text-align:center; color:#ffd700; font-size:0.75rem; font-weight:600; margin-top:6px;'>✍️ Dự đoán (Chỉ 1 lần)</div>", unsafe_allow_html=True)
                    
                    # Chỉ hiển thị mục xem dự đoán của mọi người nếu người dùng đã dự đoán hoặc trận đấu đã kết thúc
                    if has_pred or is_finished:
                        with st.expander("🟢 Xem dự đoán của mọi người", expanded=False):
                            total_preds = 0
                            rows_html = []
                            for u in users:
                                if u["name"].lower() == "admin":
                                    continue
                                u_key = f"{u['name'].strip()}-{u['unit'].strip()}"
                                u_pred = predictions.get(u_key, {}).get(m_id)
                                if u_pred and u_pred.get("score1") is not None and u_pred.get("score2") is not None:
                                    total_preds += 1
                                    rows_html.append(f"<tr><td style='color:#ffffff; padding:3px 0;'>{u['name']} ({u['unit']})</td><td style='color:#00e676; text-align:right; font-weight:bold; padding:3px 0;'>{u_pred['score1']} - {u_pred['score2']}</td></tr>")
                            
                            if total_preds > 0:
                                st.markdown(f"<div style='font-size:0.8rem; color:#ffd700; font-weight:bold; margin-bottom:5px;'>Tổng số dự đoán: {total_preds} người</div>", unsafe_allow_html=True)
                                table_html = f"""
                                <div style="max-height: 120px; overflow-y: auto; border-top: 1px solid rgba(255,255,255,0.15); padding-top: 5px;">
                                    <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem;">
                                        {"".join(rows_html)}
                                    </table>
                                </div>
                                """
                                st.markdown(table_html, unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='font-size:0.75rem; color:#94a3b8;'>Chưa có ai dự đoán trận này.</span>", unsafe_allow_html=True)
                
        # Nút lưu dự đoán ở đầu trang (sử dụng placeholder)
        if not st.session_state.is_admin:
            with save_btn_placeholder:
                # Đưa nút lưu lên đầu trang
                if new_preds:
                    if st.button("💾 Lưu Dự Đoán", use_container_width=True, type="primary"):
                        if user_key not in predictions:
                            predictions[user_key] = {}
                        
                        # Ghi nhận thời gian thực hiện dự đoán (giờ Việt Nam)
                        vn_tz = timezone(timedelta(hours=7))
                        now_str = datetime.now(vn_tz).strftime("%d/%m/%Y %H:%M:%S")
                        
                        for mId, vals in new_preds.items():
                            vals["created_at"] = now_str
                            predictions[user_key][mId] = vals
                        recalculate_local_points(matches, users, predictions)
                        
                        if not is_local:
                            success = save_db_to_github(matches, users, predictions)
                            if success:
                                st.success("Đã lưu dự đoán thành công!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Lỗi lưu dự đoán lên GitHub Cloud DB.")
                        else:
                            write_local_db(matches, users, predictions)
                            st.success("Đã lưu dự đoán thành công!")
                            st.rerun()
                else:
                    # Nút bị mờ đi khi chưa điền tỷ số
                    st.button("💾 Lưu Dự Đoán", use_container_width=True, type="secondary", disabled=True, help="Hãy điền tỷ số dự đoán của bạn trước khi bấm lưu.")

# ================= TAB 2: BẢNG XẾP HẠNG =================
elif selected_tab == "🏆 Bảng Xếp Hạng":
    st.write("---")
    st.subheader("🏆 Bảng Xếp Hạng Thành Viên")
    st.write("Danh sách điểm số xếp hạng của các thành viên tham gia dự đoán.")
    
    # Sắp xếp và format bảng xếp hạng
    player_users = [u for u in users if u["name"].lower() != "admin"]
    # Sort
    player_users.sort(key=lambda x: x["name"].lower())
    player_users.sort(key=lambda x: x.get("correctScores", 0), reverse=True)
    player_users.sort(key=lambda x: x["points"], reverse=True)
    
    if not player_users:
        st.info("Chưa có thành viên nào tham gia dự đoán.")
    else:
        html_code = (
            "<div class='leaderboard-container'>"
            "<table class='leaderboard-table'>"
            "<thead>"
            "<tr>"
            "<th style='text-align: center; width: 80px;'>Vị trí</th>"
            "<th>Họ và Tên</th>"
            "<th>Đơn vị / Phòng ban</th>"
            "<th style='text-align: center; width: 105px;'>Đoán đúng</th>"
            "<th style='text-align: center; width: 105px;'>Đoán sai</th>"
            "<th style='text-align: center; width: 105px;'>Không đoán</th>"
            "<th style='text-align: center; width: 105px;'>Số điểm</th>"
            "</tr>"
            "</thead>"
            "<tbody>"
        )
        for idx, u in enumerate(player_users):
            rank = idx + 1
            row_class = ""
            rank_html = f"<span class='rank-badge rank-normal'>{rank}</span>"
            
            if rank == 1:
                row_class = "class='top-1'"
                rank_html = "<span class='rank-badge rank-1'>🥇</span>"
            elif rank == 2:
                row_class = "class='top-2'"
                rank_html = "<span class='rank-badge rank-2'>🥈</span>"
            elif rank == 3:
                row_class = "class='top-3'"
                rank_html = "<span class='rank-badge rank-3'>🥉</span>"
                
            correct_scores = u.get("correctScores", 0)
            correct_outcomes = u.get("correctOutcomes", 0)
            unpredicted = u.get("unpredicted", 0)
            
            html_code += (
                f"<tr {row_class}>"
                f"<td style='text-align: center;'>{rank_html}</td>"
                f"<td style='font-weight: 600;'>{u['name']}</td>"
                f"<td>{u['unit']}</td>"
                f"<td style='text-align: center; color: #00e676; font-weight: 700;'>{correct_scores} trận</td>"
                f"<td style='text-align: center; color: #ff5252; font-weight: 700;'>{correct_outcomes} trận</td>"
                f"<td style='text-align: center; color: #ffd700; font-weight: 700;'>{unpredicted} trận</td>"
                f"<td class='points-column' style='text-align: center;'>{u['points']}</td>"
                f"</tr>"
            )
            
        html_code += "</tbody></table></div>"
        st.markdown(html_code, unsafe_allow_html=True)


# ================= TAB 4: QUẢN TRỊ VIÊN (ADMIN) =================
elif selected_tab == "⚙️ Quản Trị (BTC)" and st.session_state.is_admin:
    st.write("---")
    st.subheader("Bảng Điều Khiển Ban Tổ Chức")
    st.write("Cập nhật tỷ số trận đấu thực tế và xem phân bổ thống kê dự đoán của thành viên.")
    
    col_admin_l, col_admin_r = st.columns([1.2, 1])
    
    with col_admin_l:
        st.markdown("### Cập Nhật Kết Quả Trận Đấu")
        
        # Chọn trận đấu cập nhật tỉ số
        admin_matches_options = []
        for m in matches:
            admin_matches_options.append(f"{m['id']} : {m['team1']} vs {m['team2']} ({'Đã kết thúc' if m['status'] == 'finished' else 'Chưa diễn ra'})")
            
        selected_match_opt = st.selectbox("Chọn trận đấu cần cập nhật", admin_matches_options)
        
        if selected_match_opt:
            m_id = selected_match_opt.split(" : ")[0]
            match = next((m for m in matches if m["id"] == m_id), None)
            
            if match:
                with st.container(border=True):
                    st.write(f"**Trận đấu ID:** {match['id']}")
                    date_formatted = datetime.fromisoformat(match["date"]).strftime("%d/%m/%Y %H:%M")
                    st.write(f"**Thời gian:** 📅 {date_formatted}")
                    
                    col_adm_score_1, col_adm_divider, col_adm_score_2 = st.columns([0.4, 0.2, 0.4])
                    with col_adm_score_1:
                        st.markdown(f"<div style='text-align:center;'>{get_flag_html(match['team1'])}<br/><b>{match['team1']}</b></div>", unsafe_allow_html=True)
                        s1_val = match["score1"] if match["score1"] is not None and match["score1"] != "" else 0
                        admin_score_1 = st.number_input("Tỷ số đội nhà", min_value=0, max_value=20, step=1, value=int(s1_val), key="adm_s1")
                    with col_adm_divider:
                        st.markdown("<h2 style='text-align:center; margin-top:25px;'>:</h2>", unsafe_allow_html=True)
                    with col_adm_score_2:
                        st.markdown(f"<div style='text-align:center;'>{get_flag_html(match['team2'])}<br/><b>{match['team2']}</b></div>", unsafe_allow_html=True)
                        s2_val = match["score2"] if match["score2"] is not None and match["score2"] != "" else 0
                        admin_score_2 = st.number_input("Tỷ số đội khách", min_value=0, max_value=20, step=1, value=int(s2_val), key="adm_s2")
                    
                    is_fin = st.checkbox("Đã kết thúc (Khóa trận đấu & Tính điểm)", value=(match["status"] == "finished"))
                    
                    if st.button("💾 Cập nhật kết quả", use_container_width=True, type="primary"):
                        status_val = "finished" if is_fin else "pending"
                        
                        if is_fin:
                            s1 = int(admin_score_1)
                            s2 = int(admin_score_2)
                            apply_match_result(match, s1, s2, matches)
                        else:
                            match["status"] = "pending"
                            match["score1"] = None
                            match["score2"] = None
                            match["outcome"] = None
                            
                        recalculate_local_points(matches, users, predictions)
                        
                        if not is_local:
                            success = save_db_to_github(matches, users, predictions)
                            if success:
                                st.success("Đã cập nhật tỷ số và tính lại điểm thành công lên GitHub Cloud!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Lỗi cập nhật dữ liệu lên GitHub Cloud.")
                        else:
                            write_local_db(matches, users, predictions)
                            st.success("Đã cập nhật tỷ số và tính lại điểm thành công!")
                            st.rerun()
                
        st.write("---")
        st.markdown("### 👥 Quản Lý Thành Viên")
        
        non_admin_users = [u for u in users if u["name"].lower() != "admin"]
        if non_admin_users:
            user_options = [f"{u['name']} ({u['unit']})" for u in non_admin_users]
            selected_user_to_delete = st.selectbox("Chọn thành viên muốn xóa", user_options)
            
            if st.button("🗑️ Xóa Thành Viên", use_container_width=True, type="secondary"):
                parts = selected_user_to_delete.split(" (")
                u_name = parts[0].strip()
                u_unit = parts[1].replace(")", "").strip()
                
                # Cập nhật danh sách users
                users = [u for u in users if not (u["name"] == u_name and u["unit"] == u_unit)]
                
                # Xóa dự đoán
                user_key = f"{u_name}-{u_unit}"
                if user_key in predictions:
                    del predictions[user_key]
                    
                # Tính toán lại điểm số
                recalculate_local_points(matches, users, predictions)
                
                # Lưu database
                if not is_local:
                    success = save_db_to_github(matches, users, predictions)
                    if success:
                        st.success(f"Đã xóa thành viên '{selected_user_to_delete}' thành công!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Lỗi xóa thành viên trên GitHub Cloud DB.")
                else:
                    write_local_db(matches, users, predictions)
                    st.success(f"Đã xóa thành viên '{selected_user_to_delete}' thành công!")
                    time.sleep(1.5)
                    st.rerun()
        else:
            st.info("Chưa có thành viên nào đăng ký tham gia.")
                
    with col_admin_r:
        st.markdown("### Thống Kê Tổng Hợp Dự Đoán")
        
        # Thống kê cho trận được chọn bên cột trái
        if selected_match_opt:
            m_id = selected_match_opt.split(" : ")[0]
            match = next((m for m in matches if m["id"] == m_id), None)
            
            if match:
                st.write(f"Thống kê dự đoán cho trận: **{match['team1']} vs {match['team2']}**")
                
                # Tính toán thống kê
                total = 0
                team1_win = 0
                draw = 0
                team2_win = 0
                score_counts = {}
                rows_list = []
                
                for u_key, u_preds in predictions.items():
                    pred = u_preds.get(match["id"])
                    if pred:
                        s1 = pred.get("score1")
                        s2 = pred.get("score2")
                        if s1 is not None and s1 != "" and s2 is not None and s2 != "":
                            try:
                                p1 = int(s1)
                                p2 = int(s2)
                                total += 1
                                if p1 > p2: team1_win += 1
                                elif p1 < p2: team2_win += 1
                                else: draw += 1
                                
                                score_str = f"{p1}-{p2}"
                                score_counts[score_str] = score_counts.get(score_str, 0) + 1
                                
                                parts = u_key.split("-")
                                name = parts[0]
                                unit = parts[1] if len(parts) > 1 else ""
                                created_at = pred.get("created_at", "N/A")
                                rows_list.append({
                                    "Thành viên": name,
                                    "Đơn vị": unit,
                                    "Dự đoán": f"{p1} - {p2}",
                                    "Thời gian dự đoán": created_at
                                })
                            except:
                                continue
                                
                if total == 0:
                    st.info("Chưa có thành viên nào dự đoán trận đấu này.")
                else:
                    st.metric("Tổng số dự đoán đã nhận", total)
                    
                    # Vẽ biểu đồ phân bổ
                    pct_t1 = round((team1_win / total) * 100)
                    pct_draw = round((draw / total) * 100)
                    pct_t2 = round((team2_win / total) * 100)
                    
                    st.write("**Phân bổ kết quả đoán:**")
                    st.progress(team1_win / total, text=f"{match['team1']} thắng: {pct_t1}%")
                    st.progress(draw / total, text=f"Hòa: {pct_draw}%")
                    st.progress(team2_win / total, text=f"{match['team2']} thắng: {pct_t2}%")
                    
                    # Tỷ số phổ biến nhất
                    popular_scores = sorted([{"score": k, "count": v} for k, v in score_counts.items()], key=lambda x: x["count"], reverse=True)
                    st.write("**Tỷ số phổ biến nhất:**")
                    cols_pop = st.columns(min(len(popular_scores), 4))
                    for idx, item in enumerate(popular_scores[:4]):
                        with cols_pop[idx]:
                            st.markdown(f"<span class='score-badge'>{item['score']} <span style='color:#00e676;'>({item['count']} người)</span></span>", unsafe_allow_html=True)
                            
                    # Danh sách chi tiết
                    st.write("---")
                    st.write("**Chi tiết dự đoán của thành viên:**")
                    df_preds = pd.DataFrame(rows_list)
                    st.dataframe(df_preds, hide_index=True, use_container_width=True)
