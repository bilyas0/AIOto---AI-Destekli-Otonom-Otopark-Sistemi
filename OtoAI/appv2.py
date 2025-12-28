import streamlit as st
import cv2
import easyocr
import numpy as np
import re
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import plotly.graph_objects as go

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Otopark Takip Sistemi AI", page_icon="🚗")

# --- HACKER TEMA CSS ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #bab5b5; }
    h1, h2, h3, p, label, .stMarkdown, .stText { color: #bab5b5 !important; font-family: 'Courier New', Courier, monospace; }
    .stFileUploader { border: 1px solid #ff0000; padding: 10px; border-radius: 5px; }
    .dataframe { color: #ff0000 !important; background-color: #111 !important; border: 1px solid #333; }
    .metric-box { border: 1px solid #ff0000; padding: 15px; border-radius: 10px; text-align: center; background-color: #0a0a0a; box-shadow: 0 0 10px rgba(255, 0, 0, 0.2); }
</style>
""", unsafe_allow_html=True)

# --- MODEL YÜKLEME ---
@st.cache_resource
def load_model():
    return easyocr.Reader(['en'], gpu=False)

reader = load_model()

# --- VERİTABANI İŞLEMLERİ ---
def veritabani_baslat():
    conn = sqlite3.connect('otopark_web_v1.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS otopark_kayitlari
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plaka TEXT,
                  giris_zamani TEXT,
                  cikis_zamani TEXT,
                  durum TEXT,
                  ucret INTEGER)''')
    
    # Eski tabloda ucret kolonu yoksa ekle
    try:
        c.execute("SELECT ucret FROM otopark_kayitlari LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE otopark_kayitlari ADD COLUMN ucret INTEGER DEFAULT 0")
        
    conn.commit()
    conn.close()

# --- SENİN İSTEDİĞİN ÜCRET TARİFESİ ---
def ucret_hesapla(giris_str, cikis_str):
    fmt = "%Y-%m-%d %H:%M:%S"
    t1 = datetime.strptime(giris_str, fmt)
    t2 = datetime.strptime(cikis_str, fmt)
    fark = t2 - t1
    
    # Saniye -> Saat dönüşümü
    toplam_saniye = fark.total_seconds()
    saat = toplam_saniye / 3600
    
    ucret = 0
    
    # Tarife Mantığı (Tam sayı olarak)
    if saat <= 1:
        ucret = 100
    elif saat <= 2:
        ucret = 130
    elif saat <= 4:
        ucret = 170
    elif saat <= 8:
        ucret = 250
    elif saat <= 12:
        ucret = 350
    elif saat <= 24:
        ucret = 500
    else:
        gun = int(saat // 24)
        ucret = 500 + (gun * 500)
        
    return int(ucret), fark

def plaka_islem_yonetimi(plaka):
    conn = sqlite3.connect('otopark_web_v1.db')
    c = conn.cursor()
    simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("SELECT id, giris_zamani FROM otopark_kayitlari WHERE plaka = ? AND durum = 'ICERDE'", (plaka,))
    aktif_kayit = c.fetchone()
    
    sonuc_bilgisi = {}

    if aktif_kayit:
        # ÇIKIŞ
        kayit_id = aktif_kayit[0]
        giris_zamani_str = aktif_kayit[1]
        
        ucret, sure_farki = ucret_hesapla(giris_zamani_str, simdi)
        
        c.execute("UPDATE otopark_kayitlari SET cikis_zamani = ?, durum = 'CIKIS_YAPTI', ucret = ? WHERE id = ?", (simdi, ucret, kayit_id))
        
        sonuc_bilgisi = {
            "islem": "CIKIS",
            "zaman": simdi,
            "durum_mesaji": f"ÇIKIŞ YAPILDI. Süre: {str(sure_farki).split('.')[0]} | Ücret: {ucret} TL",
            "renk": "red"
        }
    else:
        # GİRİŞ
        c.execute("INSERT INTO otopark_kayitlari (plaka, giris_zamani, durum, ucret) VALUES (?, ?, 'ICERDE', 0)", 
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
    conn = sqlite3.connect('otopark_web_v1.db')
    df = pd.read_sql_query("SELECT * FROM otopark_kayitlari ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty and 'ucret' in df.columns:
        df['ucret'] = df['ucret'].fillna(0).astype(int)
    return df

# --- GRAFİK ---
def doluluk_grafigi_olustur(df):
    OTOPARK_KAPASITESI = 200
    icerideki_arac_sayisi = len(df[df['durum'] == 'ICERDE']) if not df.empty else 0
    bos_yer = max(0, OTOPARK_KAPASITESI - icerideki_arac_sayisi)
    doluluk_orani = (icerideki_arac_sayisi / OTOPARK_KAPASITESI * 100) if OTOPARK_KAPASITESI > 0 else 0
    
    colors = ['#ff0000', '#1a1a1a'] 
    fig = go.Figure(data=[go.Pie(
        labels=['Dolu', 'Boş'], values=[icerideki_arac_sayisi, bos_yer], hole=.7,
        marker=dict(colors=colors, line=dict(color='#000000', width=2)),
        textinfo='none', hoverinfo='label+value', sort=False
    )])
    fig.update_layout(
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f"%{int(doluluk_orani)}", x=0.5, y=0.5, font_size=35, showarrow=False, font_color='#ff0000', font_family='Courier New')],
        margin=dict(t=10, b=10, l=10, r=10), height=220
    )
    return fig, icerideki_arac_sayisi, OTOPARK_KAPASITESI

# --- GÖRÜNTÜ İŞLEME ---
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
        if not kenara_degiyor and (0.20 < h/h_img < 0.90) and (0.1 < w/h < 2.0):
            yeni_maske[labels == i] = 255 
    return cv2.bitwise_not(yeni_maske)

def check_turk_plaka_formati(text):
    if len(text) < 7 or len(text) > 9: return False
    il_kodu = text[:2]
    return il_kodu.isdigit() and (1 <= int(il_kodu) <= 81)

def super_iyilestirme(roi_img):
    scale=2
    img_big = cv2.resize(roi_img, (int(roi_img.shape[1]*scale), int(roi_img.shape[0]*scale)), interpolation=cv2.INTER_CUBIC)
    table = np.array([((i / 255.0) ** (1.0/1.5)) * 255 for i in np.arange(0, 256)]).astype("uint8")
    img_light = cv2.LUT(img_big, table)
    img_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(cv2.cvtColor(img_light, cv2.COLOR_BGR2GRAY))
    img_sharp = cv2.filter2D(img_clahe, -1, np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]]))
    _, img_thresh = cv2.threshold(img_sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img_thresh

# --- MAIN ---
def main():
    veritabani_baslat()
    st.title("BRK OTOPARK SİSTEMİ")
    st.markdown("---")
    col1, col2 = st.columns([1, 1.5]) 

    with col1:
        st.subheader("KAMERA / RESİM GİRİŞİ")
        uploaded_file = st.file_uploader("Araç Görseli Yükle", type=['png', 'jpg', 'jpeg'])
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            st.image(img, channels="BGR", caption="Kamera Görüntüsü", use_container_width=True)
            
            plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')
            plates = plate_cascade.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.05, 6, minSize=(50, 15))
            
            bulunan_plaka, db_mesaj = None, None
            for (x, y, w, h) in plates:
                roi_final = super_iyilestirme(img[y:y+h, x:x+w])
                sonuclar = reader.readtext(akilli_harf_secici(roi_final), detail=0, allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                text_clean = re.sub(r'[^A-Z0-9]', '', "".join(sonuclar))
                if check_turk_plaka_formati(text_clean):
                    bulunan_plaka = text_clean
                    db_mesaj = plaka_islem_yonetimi(text_clean)
                    break
            
            if bulunan_plaka and db_mesaj:
                st.success(f"PLAKA: {bulunan_plaka}")
                color = '#00FF00' if db_mesaj['renk'] == 'green' else '#FF0000'
                st.markdown(f"<h3 style='color: {color};'>{'✅' if color=='#00FF00' else '⛔'} {db_mesaj['durum_mesaji']}</h3>", unsafe_allow_html=True)
            else:
                st.warning("Plaka bulunamadı.")

    with col2:
        st.subheader("DURUM ")
        df = get_all_records()
        fig_grafik, dolu_sayi, kapasite = doluluk_grafigi_olustur(df)
        
        gc1, gc2 = st.columns([1, 2])
        with gc1:
            st.markdown(f"""<div class="metric-box"><h4 style='margin:0;color:#bab5b5;'>KAPASİTE</h4><h1 style='margin:10px 0;color:#ff0000;font-size:36px;font-weight:bold;'>{dolu_sayi}/{kapasite}</h1></div>""", unsafe_allow_html=True)
        with gc2:
            st.plotly_chart(fig_grafik, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("---")
        st.subheader("CANLI VERİ AKIŞI")
        if not df.empty:
            st.dataframe(
                df.style.map(lambda v: f"color: {'#00FF00' if v=='ICERDE' else '#FF0000'}; font-weight: bold", subset=['durum']),
                use_container_width=True, height=400,
                column_config={"ucret": st.column_config.NumberColumn("Ücret (TL)", format="%d TL")}
            )
        else:
            st.info("Kayıt yok.")

if __name__ == '__main__':
    main()