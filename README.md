# AIOto--AI-Destekli-Otonom-Otopark-Sistemi

Bu proje, otopark giriş-çıkış süreçlerini otomatize etmek için geliştirilmiş, Yapay Zeka destekli bir yönetim panelidir. Kamera görüntülerinden plaka tanıma, otomatik ücret hesaplama ve geçmiş verilerle kalış süresi tahmini gibi özellikleri bir arada sunar.

Öne Çıkan Özellikler
Plaka Tanıma: EasyOCR ve OpenCV kullanarak araç plakalarını görüntülerden otomatik olarak okur.

Akıllı Ücretlendirme: Giriş ve çıkış saatleri arasındaki farka göre dinamik (saatlik/günlük) ücret hesabı yapar.

Canlı Dashboard: Streamlit tabanlı, "Hacker/Dark Mode" temalı kullanıcı dostu arayüz.

Veri Analitiği: Otopark doluluk oranlarını gerçek zamanlı olarak Plotly grafiklerine yansıtır.

Makine Öğrenmesi: Random Forest algoritması ile plaka il kodu, giriş saati ve güne göre bir aracın ne kadar süre otoparkta kalacağını tahmin eder.

Veritabanı Yönetimi: SQLite entegrasyonu ile tüm giriş-çıkış kayıtlarını ve ücret bilgilerini saklar.

🛠️ Kullanılan Teknolojiler
Dil: Python 

Görüntü İşleme: OpenCV, EasyOCR

Web Arayüz: Streamlit

Makine Öğrenmesi: Scikit-learn, Pandas, NumPy

Veritabanı: SQLite3

Görselleştirme: Plotly

# Ön İşleme Adımları

<img width="1208" height="536" alt="image" src="https://github.com/user-attachments/assets/08350897-72ba-454a-9af6-af4cbb1e61bf" />





🚀 Kurulum ve Çalıştırma
1. Depoyu Klonlayın
Bash

git clone https://github.com/kullanici_adiniz/otopark-takip-sistemi.git
cd otopark-takip-sistemi
2. Gerekli Kütüphaneleri Yükleyin
Sistemde kullanılan kütüphaneleri aşağıdaki komutla hızlıca yükleyebilirsiniz:

Bash

pip install streamlit opencv-python easyocr numpy pandas scikit-learn plotly
Not: EasyOCR için ilk çalıştırmada model dosyaları (yaklaşık 100-150MB) otomatik olarak indirilecektir.

3. Sistemi Başlatın
A. Makine Öğrenmesi Modelini Eğitmek İçin: Önce simülasyon verileriyle modelin eğitilmesini istiyorsanız:

Bash

python ml.py
B. Web Arayüzünü Başlatmak İçin:

Bash

streamlit run appv2.py
Kullanım Ekranı
Görsel Yükle: Sisteme bir araç plakası fotoğrafı yükleyin.

Otomatik İşlem: Sistem plakayı tanır; araç içerideyse çıkışını yapar ve ücreti hesaplar, içeride değilse giriş kaydı oluşturur.

Takip: Sağ taraftaki panelden doluluk oranını ve güncel araç listesini takip edin.

<img width="1916" height="908" alt="image" src="https://github.com/user-attachments/assets/65802b4c-c652-40ad-ae20-233534967acc" />
