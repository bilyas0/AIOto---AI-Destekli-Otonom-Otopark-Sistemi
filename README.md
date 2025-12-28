# 🚗 BRK Otopark Takip Sistemi (V2)

Bu proje, görüntü işleme ve veri yönetimi teknolojilerini bir araya getiren, modern arayüzlü bir **Akıllı Otopark Yönetim Paneli**'dir. Sistem, araç plakalarını görsellerden otomatik olarak tanımlar, giriş-çıkış kayıtlarını tutar ve süreye göre ücret hesaplaması yapar.

## 🌟 Öne Çıkan Özellikler

* **Otomatik Plaka Tanıma (ALPR):** `EasyOCR` ve `OpenCV` kütüphanelerini kullanarak araç fotoğraflarından plaka metnini ayıklar.
* **Gelişmiş Görüntü İşleme:** Plaka okuma başarısını artırmak için gürültü azaltma, keskinleştirme ve `super_iyilestirme` (CLAHE ve Thresholding) algoritmalarını kullanır.
* **Dinamik Ücretlendirme:** Araçların içeride kaldığı süreye göre (saatlik veya günlük) otomatik ücret hesaplar (Örn: 0-1 saat 100 TL, 24+ saat günlük 500 TL).
* **Canlı Dashboard:** Otopark kapasitesini, doluluk oranını ve güncel araç listesini `Streamlit` ve `Plotly` ile anlık olarak görselleştirir.
* **Hacker/Dark Tema:** Kullanıcı dostu, özelleştirilmiş karanlık mod arayüz tasarımı.

# Ön İşleme Adımları

<img width="1208" height="536" alt="image" src="https://github.com/user-attachments/assets/08350897-72ba-454a-9af6-af4cbb1e61bf" />

## 🛠️ Kurulum

Sistemi yerel bilgisayarınızda çalıştırmak için Python 3.x yüklü olmalıdır. Gerekli kütüphaneleri aşağıdaki komutla yükleyebilirsiniz:

pip install streamlit opencv-python easyocr numpy pandas plotly
Not: EasyOCR ilk çalıştığında plaka tanıma için gerekli olan AI modellerini otomatik olarak indirecektir.
🚀 KullanımUygulamayı başlatmak için terminale şu komutu yazın:Bashstreamlit run appv2.py
Görsel Yükle: Sisteme bir araç fotoğrafı yükleyin.Otomatik Tanıma: Sistem plakayı bulur ve Türkiye plaka formatına uygunluğunu denetler.
İşlem Yönetimi: - Araç içeride değilse: GİRİŞ kaydı oluşturulur.Araç zaten içerideyse: ÇIKIŞ işlemi yapılır ve süreye göre ücret yansıtılır.
📂 Proje Yapısı: appv2.py- Arayüz, görüntü işleme ve veritabanı mantığını içeren ana dosya.otopark_web_v1.db- Tüm kayıtların tutulduğu SQLite veritabanı (Otomatik oluşturulur).ml.py: (Geliştirme Aşamasında) Otoparkta kalış süresi tahmini için hazırlanan makine öğrenmesi modeli.

<img width="1916" height="908" alt="image" src="https://github.com/user-attachments/assets/65802b4c-c652-40ad-ae20-233534967acc" />
