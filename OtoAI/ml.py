import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import datetime
import random

# --- 1. Veri Seti Oluşturma (Simülasyon) ---
num_samples = 2000
data = []
start_date = datetime.datetime(2025, 1, 1)

for i in range(num_samples):
    # Rastgele giriş zamanı
    random_days = random.randint(0, 30)
    giris = start_date + datetime.timedelta(days=random_days, seconds=random.randint(0, 86400))
    
    # Hafta sonu daha uzun, hafta içi karışık süreler simülasyonu
    if giris.weekday() >= 5:
        duration = int(np.random.normal(180, 60)) # Ort. 3 saat
    else:
        duration = int(np.random.normal(500, 100)) if random.random() > 0.3 else int(np.random.normal(45, 15))
            
    cikis = giris + datetime.timedelta(minutes=max(5, duration))
    
    # Rastgele Plaka Üretimi
    plaka = f"{random.randint(1, 81):02d}{''.join(random.choices('ABC', k=2))}{random.randint(100, 999)}"
    
    data.append({"id": i, "plaka": plaka, "giris_zamani": giris, "cikis_zamani": cikis, "durum": "CIKIS_YAPTI"})

df = pd.DataFrame(data)

df_ml = df.drop(columns=["id", "durum"])

# Makine Öğrenmesi için sayısal veriler üretme
df_ml['plaka_il_kodu'] = df_ml['plaka'].str[:2].astype(int)
df_ml['giris_saati'] = df_ml['giris_zamani'].dt.hour
df_ml['haftanin_gunu'] = df_ml['giris_zamani'].dt.dayofweek
df_ml['kalis_suresi'] = (df_ml['cikis_zamani'] - df_ml['giris_zamani']).dt.total_seconds() / 60

# --- 3. Random Forest Eğitimi ---
X = df_ml[['plaka_il_kodu', 'giris_saati', 'haftanin_gunu']]
y = df_ml['kalis_suresi']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
rf_model = RandomForestRegressor(n_estimators=100)
rf_model.fit(X_train, y_train)

print("Model başarıyla eğitildi.")