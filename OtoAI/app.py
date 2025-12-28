import streamlit as st
import cv2
import easyocr
import numpy as np
import re
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import plotly.graph_objects as go  # Grafik için gerekli kütüphane

# --- SAYFA AYARLARI VE CSS (SİYAH ARKA PLAN - KIRMIZI YAZI) ---
st.set_page_config(layout="wide", page_title="Otopark Takip Sistemi AI", page_icon="🚗")

# Custom CSS ile Hacker Teması
st.markdown("""
<style>
    /* Ana arka plan */
    .stApp {
        background-color: #000000;
        color: #bab5b5;
    }
    /* Tablo başlıkları */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    
    /* Yazı renkleri */
    h1, h2, h3, p, label, .stMarkdown, .stText {
        color: #bab5b5 !important;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Yükleme butonu */
    .stFileUploader {
        border: 1px solid #ff0000;
        padding: 10px;
        border-radius: 5px;
    }
    
    /* Tablo stilleri */
    .dataframe {
        color: #ff0000 !important;
        background-color: #111 !important;
        border: 1px solid #333;
    }
    
    /* Metrik kutusu stili */
    .metric-box {
        border: 1px solid #ff0000;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        background-color: #0a0a0a;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- CACHED RESOURCES ---
@st.cache_resource
def load_model():
    return easyocr.Reader(['en'], gpu=False)

reader = load_model()

# --- VERİTABANI FONKSİYONLARI ---
def veritabani_baslat():
    conn = sqlite3.connect('otopark_web_v1.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS otopark_kayitlari
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plaka TEXT,
                  giris_zamani TEXT,
                  cikis_zamani TEXT,
                  durum TEXT)''')
    conn.commit()
    conn.close()

def plaka_islem_yonetimi(plaka):
    conn = sqlite3.connect('otopark_web_v1.db')
    c = conn.cursor()
    simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("SELECT id, giris_zamani FROM otopark_kayitlari WHERE plaka = ? AND durum = 'ICERDE'", (plaka,))
    aktif_kayit = c.fetchone()
    
    sonuc_bilgisi = {}

    if aktif_kayit:
        # ÇIKIŞ İŞLEMİ
        kayit_id = aktif_kayit[0]
        giris_zamani_str = aktif_kayit[1]
        c.execute("UPDATE otopark_kayitlari SET cikis_zamani = ?, durum = 'CIKIS_YAPTI' WHERE id = ?", (simdi, kayit_id))
        
        # Süre hesabı
        fmt = "%Y-%m-%d %H:%M:%S"
        t1 = datetime.strptime(giris_zamani_str, fmt)
        t2 = datetime.strptime(simdi, fmt)
        fark = t2 - t1
        
        sonuc_bilgisi = {
            "islem": "CIKIS",
            "zaman": simdi,
            "durum_mesaji": f"ÇIKIŞ YAPILDI. (Süre: {fark})",
            "renk": "red"
        }
    else:
        # GİRİŞ İŞLEMİ
        c.execute("INSERT INTO otopark_kayitlari (plaka, giris_zamani, durum) VALUES (?, ?, 'ICERDE')", 
                  (plaka, simdi))
        sonuc_bilgisi = {
            "islem": "GIRIS",
            "zaman": simdi,
            "durum_mesaji": "GİRİŞ YAPILDI.",
            "renk": "green"
        }
    
    conn.commit()
    conn.close()
    return sonuc_bilgisi

def get_all_records():
    """Tüm veritabanını okur ve Pandas DataFrame döndürür"""
    conn = sqlite3.connect('otopark_web_v1.db')
    df = pd.read_sql_query("SELECT * FROM otopark_kayitlari ORDER BY id DESC", conn)
    conn.close()
    return df

# --- GRAFİK FONKSİYONU (YENİ) ---
def doluluk_grafigi_olustur(df):
    OTOPARK_KAPASITESI = 20  # Kapasiteyi buradan değiştirebilirsin
    
    # İçerideki araç sayısını bul
    if not df.empty:
        icerideki_arac_sayisi = len(df[df['durum'] == 'ICERDE'])
    else:
        icerideki_arac_sayisi = 0
        
    bos_yer = OTOPARK_KAPASITESI - icerideki_arac_sayisi
    if bos_yer < 0: bos_yer = 0 # Hata önleyici

    if OTOPARK_KAPASITESI > 0:
        doluluk_orani = (icerideki_arac_sayisi / OTOPARK_KAPASITESI) * 100
    else:
        doluluk_orani = 0
    
    # Renkler (Hacker teması: Neon Kırmızı Dolu, Koyu Gri Boş)
    colors = ['#ff0000', '#1a1a1a'] 

    fig = go.Figure(data=[go.Pie(
        labels=['Dolu', 'Boş'],
        values=[icerideki_arac_sayisi, bos_yer],
        hole=.7, # Halka genişliği
        marker=dict(colors=colors, line=dict(color='#000000', width=2)),
        textinfo='none', 
        hoverinfo='label+value',
        sort=False
    )])

    # Ortadaki Yüzde Yazısı ve Tasarım Ayarları
    fig.update_layout(
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)', # Arka plan şeffaf
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f"%{int(doluluk_orani)}", x=0.5, y=0.5, font_size=35, showarrow=False, font_color='#ff0000', font_family='Courier New')],
        margin=dict(t=10, b=10, l=10, r=10),
        height=220
    )
    return fig, icerideki_arac_sayisi, OTOPARK_KAPASITESI

# --- GÖRÜNTÜ İŞLEME YARDIMCILARI ---
def akilli_harf_secici(binary_img):
    h_img, w_img = binary_img.shape
    ters_img = cv2.bitwise_not(binary_img)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(ters_img, connectivity=8)
    yeni_maske = np.zeros_like(binary_img)
    for i in range(1, num_labels):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        kenara_degiyor = (x <= 2) or (y <= 2) or (x+w >= w_img-2) or (y+h >= h_img-2)
        yukseklik_orani = h / h_img
        boyut_uygun = (0.20 < yukseklik_orani < 0.90)
        aspect_ratio = w / h
        sekil_uygun = (0.1 < aspect_ratio < 2.0)
        if not kenara_degiyor and boyut_uygun and sekil_uygun:
            yeni_maske[labels == i] = 255 
    return cv2.bitwise_not(yeni_maske)

def check_turk_plaka_formati(text):
    if len(text) < 7 or len(text) > 9: return False
    il_kodu = text[:2]
    if not il_kodu.isdigit() or not (1 <= int(il_kodu) <= 81): return False
    return True

def super_iyilestirme(roi_img):
    scale=2
    width = int(roi_img.shape[1] * scale)
    height = int(roi_img.shape[0] * scale)
    img_big = cv2.resize(roi_img, (width, height), interpolation=cv2.INTER_CUBIC)
    
    invGamma = 1.0 / 1.5
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    img_light = cv2.LUT(img_big, table)
    
    img_gray = cv2.cvtColor(img_light, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img_clahe = clahe.apply(img_gray)
    
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    img_sharp = cv2.filter2D(img_clahe, -1, kernel)
    
    _, img_thresh = cv2.threshold(img_sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img_thresh

# --- ANA UYGULAMA MANTIĞI ---

def main():
    veritabani_baslat()
    
    st.title("🛡️ BRK OTOPARK SİSTEMİ")
    st.markdown("---")

    # İki Sütunlu Yapı
    col1, col2 = st.columns([1, 1.5]) 

    # --- SOL SÜTUN: RESİM YÜKLEME VE İŞLEME ---
    with col1:
        st.subheader("📷 KAMERA / RESİM GİRİŞİ")
        uploaded_file = st.file_uploader("Araç Görseli Yükle", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file is not None:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            st.image(img, channels="BGR", caption="Kamera Görüntüsü", use_container_width=True)
            
            # --- PLAKA TANIMA İŞLEMİ ---
            plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')
            gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            plates = plate_cascade.detectMultiScale(gray_full, scaleFactor=1.05, minNeighbors=6, minSize=(50, 15))

            bulunan_plaka = None
            db_mesaj = None
            
            if len(plates) > 0:
                for (x, y, w, h) in plates:
                    roi_color = img[y:y+h, x:x+w].copy()
                    roi_final = super_iyilestirme(roi_color)
                    roi_clean = akilli_harf_secici(roi_final) 

                    sonuclar = reader.readtext(roi_clean, detail=0, allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                    text_clean = re.sub(r'[^A-Z0-9]', '', "".join(sonuclar))

                    if check_turk_plaka_formati(text_clean):
                        bulunan_plaka = text_clean
                        db_mesaj = plaka_islem_yonetimi(text_clean)
                        break
            
            if bulunan_plaka and db_mesaj:
                st.success(f"PLAKA TESPİT EDİLDİ: {bulunan_plaka}")
                if db_mesaj['renk'] == 'green':
                    st.markdown(f"<h3 style='color: #00FF00;'>✅ {db_mesaj['durum_mesaji']}</h3>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h3 style='color: #FF0000;'>⛔ {db_mesaj['durum_mesaji']}</h3>", unsafe_allow_html=True)
            else:
                st.warning("Plaka bulunamadı veya format uygun değil.")

    # --- SAĞ SÜTUN: VERİTABANI VE DASHBOARD ---
    with col2:
        st.subheader("📊 DOLULUK DURUMU")
        
        # Güncel veriyi çek
        df = get_all_records()
        
        # Grafik oluştur
        fig_grafik, dolu_sayi, kapasite = doluluk_grafigi_olustur(df)
        
        # Grafiği ve sayıyı yan yana göster
        g_col1, g_col2 = st.columns([1, 2])
        
        with g_col1:
            st.markdown(f"""
            <div class="metric-box">
                <h4 style='margin:0; color: #bab5b5;'>KAPASİTE</h4>
                <h1 style='margin:10px 0; color: #ff0000; font-size: 36px; font-weight:bold;'>{dolu_sayi}/{kapasite}</h1>
                <p style='margin:0; font-size:12px; color: #666;'>ARAÇ SAYISI</p>
            </div>
            """, unsafe_allow_html=True)
            
        with g_col2:
            st.plotly_chart(fig_grafik, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("---")
        st.subheader("💾 CANLI VERİ AKIŞI")
        
        if not df.empty:
            def color_status(val):
                color = '#00FF00' if val == 'ICERDE' else '#FF0000' 
                return f'color: {color}; font-weight: bold'

            st.dataframe(
                df.style.map(color_status, subset=['durum']),
                use_container_width=True,
                height=400
            )
        else:
            st.info("Henüz kayıt bulunmamaktadır.")

if __name__ == '__main__':
    main()