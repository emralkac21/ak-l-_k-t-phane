# Akıllı Kütüphane
Profesyonel kütüphane yönetimi için tam özellikli masaüstü uygulaması.
# Kütüphane Yönetim Sistemi

Profesyonel kütüphane yönetimi için tam özellikli masaüstü uygulaması.

## Özellikler

### ✅ Gerçek Uygulama Özellikleri

- **Boş Veritabanı**: Artık örnek verilerle gelmiyor, tamamen boş bir veritabanıyla başlıyor
- **Excel/CSV İçe Aktarma**: Kitap listelerinizi Excel veya CSV dosyalarından kolayca içe aktarın
- **Akıllı Sütun Eşleştirme**: Otomatik sütun tanıma ve eşleştirme özelliği
- **Sıfırdan Başlama**: Kendi kütüphanenize özel bilgiler girin

### 📚 Temel Özellikler

- Kitap yönetimi (ekleme, düzenleme, silme, arama)
- Üye yönetimi
- Ödünç işlemleri
- Ceza takibi
- Raporlar ve istatistikler
- Özelleştirilebilir ayarlar

## Kurulum

1. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Uygulamayı çalıştırın:
```bash
python kutuphane_gercek.py
```

## Excel/CSV İçe Aktarma Özelliği

### Desteklenen Formatlar
- Excel: .xlsx, .xls
- CSV: .csv

### Kullanım Adımları

1. **Kitaplar** menüsüne gidin
2. **İçe Aktar** butonuna tıklayın
3. Excel veya CSV dosyanızı seçin
4. Sütunları eşleştirin:
   - Kitap Adı (zorunlu)
   - Yazar (zorunlu)
   - Yayınevi
   - ISBN
   - Kategori
   - Raf
   - Stok

5. **İçe Aktar** butonuna tıklayın

### Örnek Excel/CSV Formatı

```
Kitap Adı          | Yazar              | Yayınevi        | ISBN            | Kategori | Raf  | Stok
-------------------|--------------------|-----------------|-----------------|-----------|----- |-----
Suç ve Ceza        | Dostoyevski        | İş Bankası      | 978-605-332-1   | Klasik   | A-01 | 3
1984               | George Orwell      | Can Yayınları   | 978-605-332-2   | Roman    | A-02 | 5
```

### İpuçları

- **Otomatik Eşleştirme**: Sistem sütun adlarına göre otomatik eşleştirme yapar
- **Yeni Kategoriler**: Olmayan kategoriler otomatik oluşturulur
- **Hata Yönetimi**: Hatalı satırlar atlanır ve rapor edilir
- **Önizleme**: İçe aktarmadan önce ilk 5 satırı önizleyin

## İlk Kullanım

### 1. Kütüphane Bilgilerini Girin
- **Ayarlar** menüsüne gidin
- Kütüphane adı ve adres bilgilerini girin
- Ödünç süresini ve diğer ayarları belirleyin

### 2. Kitapları Ekleyin

**Manuel Ekleme:**
- **Kitaplar** > **Yeni Kitap**
- Kitap bilgilerini girin

**Toplu Ekleme:**
- Excel/CSV dosyanızı hazırlayın
- **Kitaplar** > **İçe Aktar**
- Dosyanızı seçin ve sütunları eşleştirin

### 3. Üye Ekleyin
- **Üyeler** > **Yeni Üye**
- Üye bilgilerini girin

### 4. Ödünç İşlemleri
- **Ödünç İşlemleri** > **Yeni Ödünç**
- Üye ve kitap seçin

## Veritabanı

Uygulama SQLite veritabanı kullanır. İlk çalıştırmada `kutuphane.db` dosyası otomatik oluşturulur.

### Veritabanı Sıfırlama

Baştan başlamak isterseniz `kutuphane.db` dosyasını silin ve uygulamayı yeniden başlatın.

## Sistem Gereksinimleri

- Python 3.7+
- tkinter (genellikle Python ile birlikte gelir)
- Windows, macOS veya Linux

## Destek ve Geri Bildirim

Sorun yaşarsanız veya öneriniz varsa lütfen bildirin.

## Lisans

Bu proje eğitim amaçlı geliştirilmiştir.
