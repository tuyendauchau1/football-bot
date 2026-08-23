import time
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# CẤU HÌNH TỪ BIẾN MÔI TRƯỜNG GITHUB
# ==========================================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Đọc danh sách API Key từ file keys.txt
def tai_danh_sach_key():
    danh_sach = []
    if os.path.exists("keys.txt"):
        try:
            with open("keys.txt", "r", encoding="utf-8") as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith("#"):
                        danh_sach.append(clean_line)
        except Exception as e:
            print(f"Lỗi đọc file keys.txt: {e}")
            
    if not danh_sach:
        danh_sach = ["c6d17e7c8e8597ee502a843ac8110518"]
    return danh_sach

DANH_SACH_API_KEY = tai_danh_sach_key()

# Danh sách lưu các chỉ số (index) của những key đã bị hết lượt trong phiên chạy này
key_da_het_luot = set()
index_key_hien_tai = 0

REGION = "eu"
SANH_MUC_TIEU = ["saba", "ibc", "cmd", "bti", "sbo", "1xbet"]

DANH_SACH_GIAI_TAM_DIEM = [
    "soccer_epl",                  
    "soccer_uefa_champs_league",   
    "soccer_spain_la_liga",        
    "soccer_italy_serie_a",        
    "soccer_germany_bundesliga",   
    "soccer_france_ligue_one",     
    "soccer_uefa_europa_league",   
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_brazil_campeonato",    
    "soccer_argentina_primera_division", 
    "soccer_usa_mls",              
    "soccer_turkey_super_lig",     
    "soccer_scotland_premiership", 
    "soccer_belgium_first_div"     
]

def gui_tin_nhan_telegram(noi_dung):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": noi_dung,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def lam_tron_tien(so_tien):
    return round(so_tien, -3)

def chuyen_doi_gio_viet_nam(chuoi_thoi_gian):
    try:
        dt_utc = datetime.strptime(chuoi_thoi_gian, "%Y-%m-%dT%H:%M:%SZ")
        dt_vn = dt_utc + timedelta(hours=7)
        return dt_vn.strftime("%H:%M - %d/%m/%Y")
    except:
        return chuoi_thoi_gian

def lay_api_key_hoat_dong():
    global index_key_hien_tai
    
    # Kiểm tra xem tất cả các key trong file đã cạn sạch lượt chưa
    if len(key_da_het_luot) >= len(DANH_SACH_API_KEY):
        return None # Hết toàn bộ key
        
    # Tìm key tiếp theo chưa bị đánh dấu hết lượt
    so_lan_thu = 0
    while so_lan_thu < len(DANH_SACH_API_KEY):
        if index_key_hien_tai not in key_da_het_luot:
            return DANH_SACH_API_KEY[index_key_hien_tai]
        
        # Nếu key này đã đánh dấu hết lượt, tự động chuyển sang index tiếp theo
        index_key_hien_tai = (index_key_hien_tai + 1) % len(DANH_SACH_API_KEY)
        so_lan_thu += 1
        
    return None

def danh_dau_key_hiet_luot():
    global index_key_hien_tai
    key_da_het_luot.add(index_key_hien_tai)
    print(f"⚠️ Key số {index_key_hien_tai + 1} đã cạn lượt, đưa vào danh sách chờ hồi phục.")
    # Chuyển sang index tiếp theo cho lần lấy sau
    index_key_hien_tai = (index_key_hien_tai + 1) % len(DANH_SACH_API_KEY)

def xu_ly_quet_keo_chau_a():
    gio_bat_dau_vn = (datetime.utcnow() + timedelta(hours=7)).strftime("%H:%M:%S - %d/%m/%Y")
    gui_tin_nhan_telegram(f"🤖 *Bot điểm danh:* Đã thức dậy và tiến hành quét với tổng số `{len(DANH_SACH_API_KEY)}` keys từ file lúc `{gio_bat_dau_vn}`.")
    
    print(f"[{gio_bat_dau_vn}] Bắt đầu quá trình quét Kèo Châu Á...")
    so_keo_tim_duoc = 0

    i = 0
    while i < len(DANH_SACH_GIAI_TAM_DIEM):
        sport_key = DANH_SACH_GIAI_TAM_DIEM[i]
        
        # Lấy key đang hoạt động
        api_key_dang_dung = lay_api_key_hoat_dong()
        
        if not api_key_dang_dung:
            # Nếu tất cả các key đều đã cạn sạch lượt trong phiên này
            gui_tin_nhan_telegram("🚨 *Cảnh báo nghiêm trọng:* Toàn bộ API Key trong file `keys.txt` đều đã cạn sạch lượt gọi trong ngày! Bot tạm dừng.")
            print("❌ Đã cạn sạch toàn bộ API Key khả dụng.")
            break
            
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={api_key_dang_dung}&regions={REGION}&markets=spreads"
        try:
            response = requests.get(url, timeout=5)
            
            # Nếu phát hiện key hết lượt (429) hoặc lỗi xác thực (401)
            if response.status_code == 429 or response.status_code == 401:
                danh_dau_key_hiet_luot()
                # QUÉT LẠI ngay chính giải đấu hiện tại bằng chiếc Key sống tiếp theo
                continue
                
            if response.status_code != 200:
                i += 1
                continue
                
            data = response.json()
        except:
            i += 1
            continue

        for match in data:
            tran_dau = f"{match.get('home_team')} vs {match.get('away_team')}"
            gio_vn = chuyen_doi_gio_viet_nam(match.get('commence_time', ''))
            bookmakers = match.get('bookmakers', [])
            
            sanh_hop_le = []
            for bm in bookmakers:
                ten_sanh = bm.get('title', '').lower()
                if any(s in ten_sanh for s in SANH_MUC_TIEU):
                    sanh_hop_le.append(bm)
            
            if len(sanh_hop_le) >= 2:
                for x in range(len(sanh_hop_le)):
                    for y in range(x + 1, len(sanh_hop_le)):
                        sanh_a = sanh_hop_le[x]
                        sanh_b = sanh_hop_le[y]
                        
                        try:
                            markets_a = sanh_a.get('markets', [])
                            markets_b = sanh_b.get('markets', [])
                            
                            if not markets_a or not markets_b:
                                continue
                                
                            outcomes_a = markets_a[0].get('outcomes', [])
                            outcomes_b = markets_b[0].get('outcomes', [])
                            
                            if len(outcomes_a) >= 2 and len(outcomes_b) >= 2:
                                doi_a = outcomes_a[0].get('name')
                                chap_a = outcomes_a[0].get('point', 0)
                                odds_a = outcomes_a[0].get('price')
                                odds_b = outcomes_b[1].get('price')
                                
                                nghich_dao_a = 1 / odds_a
                                nghich_dao_b = 1 / odds_b
                                tong_nghich_dao = nghich_dao_a + nghich_dao_b
                                
                                tong_von = 2000000
                                
                                if tong_nghich_dao < 1:
                                    so_keo_tim_duoc += 1
                                    tien_a_goc = tong_von * (nghich_dao_a / tong_nghich_dao)
                                    tien_b_goc = tong_von * (nghich_dao_b / tong_nghich_dao)
                                    
                                    tien_a_tron = lam_tron_tien(tien_a_goc)
                                    tien_b_tron = lam_tron_tien(tien_b_goc)
                                    
                                    loi_nhuan = tong_von * ((1 / tong_nghich_dao) - 1)
                                    phan_tram_lai = (loi_nhuan / tong_von) * 100
                                    
                                    thong_bao = (
                                        "🚨 SĂN KÈO CHÂU Á (SUREBET) 🚨\n\n"
                                        f"⚽ Trận: {tran_dau}\n"
                                        f"📌 Mức chấp: {doi_a} (Chấp {chap_a})\n"
                                        f"⏰ Giờ đá (VN): {gio_vn}\n"
                                        f"📊 Tổng nghịch đảo: {tong_nghich_dao:.4f} (~ Lãi {phan_tram_lai:.2f}%)\n\n"
                                        f"👉 Cửa 1 ({sanh_a['title']}):\n"
                                        f"   - Odds: {odds_a}\n"
                                        f"   - Tiền đặt: {tien_a_tron:,.0f} VND\n\n"
                                        f"👉 Cửa 2 ({sanh_b['title']}):\n"
                                        f"   - Odds: {odds_b}\n"
                                        f"   - Tiền đặt: {tien_b_tron:,.0f} VND\n\n"
                                        f"💰 Lợi nhuận: +{loi_nhuan:,.0f} VND"
                                    )
                                    gui_tin_nhan_telegram(thong_bao)
                                    print(f"🎯 ĐÃ BẮN KÈO: {tran_dau}")
                        except:
                            continue
        
        i += 1

    gio_ket_thuc_vn = (datetime.utcnow() + timedelta(hours=7)).strftime("%H:%M:%S")
    bao_cao_tong_ket = f"✅ *Đã quét xong!*\n⏰ Hoàn tất lúc: `{gio_ket_thuc_vn}`\n🔍 Kết quả: Tìm thấy *{so_keo_tim_duoc}* kèo Surebet."
    gui_tin_nhan_telegram(bao_cao_tong_ket)

print("BOT ĐÃ KHỞI ĐỘNG TRÊN GITHUB ACTIONS...")
xu_ly_quet_keo_chau_a()
