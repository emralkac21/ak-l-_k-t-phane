import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
import pandas as pd

class KutuphaneYonetimSistemi:
    def __init__(self, root):
        self.root = root
        self.root.title("Kütüphane Yönetim Sistemi")
        self.root.geometry("1400x800")
        self.root.configure(bg="#f5f5f5")
        
        # Veritabanı bağlantısı
        self.veritabani_baslat()
        
        # Renk paleti
        self.renkler = {
            'sidebar_bg': '#1e3a5f',
            'sidebar_hover': '#2a4d7c',
            'sidebar_text': '#ffffff',
            'ana_bg': '#f5f5f5',
            'kart_bg': "#ececec",
            'primary': '#4a90e2',
            'success': '#5cb85c',
            'warning': '#f0ad4e',
            'danger': '#d9534f',
            'text_dark': '#333333',
            'text_light': '#666666'
        }
        
        # Ana container
        self.ana_container = tk.Frame(root, bg=self.renkler['ana_bg'])
        self.ana_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar oluştur
        self.sidebar_olustur()
        
        # İçerik alanı
        self.icerik_alani = tk.Frame(self.ana_container, bg=self.renkler['ana_bg'])
        self.icerik_alani.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Başlangıç sayfası
        self.ana_panel_goster()

    def veritabani_baslat(self):
        """Veritabanını başlatır ve tabloları oluşturur"""
        self.conn = sqlite3.connect('kutuphane.db')
        self.cursor = self.conn.cursor()
        
        # Foreign Key desteğini aktif et (Silme işlemleri için önemli)
        self.cursor.execute("PRAGMA foreign_keys = ON")
        
        # Kategoriler tablosu
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS kategoriler
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              ad TEXT NOT NULL UNIQUE)''')
        
        # Kitaplar tablosu
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS kitaplar
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              ad TEXT NOT NULL,
                              yazar TEXT NOT NULL,
                              yayin_evi TEXT,
                              isbn TEXT UNIQUE,
                              kategori_id INTEGER,
                              raf TEXT,
                              stok INTEGER DEFAULT 1,
                              FOREIGN KEY (kategori_id) REFERENCES kategoriler(id))''')
        
        # Üyeler tablosu
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS uyeler
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              ad_soyad TEXT NOT NULL,
                              tc_kimlik TEXT UNIQUE NOT NULL,
                              telefon TEXT,
                              eposta TEXT,
                              sehir TEXT,
                              kayit_tarihi DATE)''')
        
        # Ödünç işlemleri tablosu
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS odunc_islemleri
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              uye_id INTEGER,
                              kitap_id INTEGER,
                              alis_tarihi DATE,
                              son_teslim DATE,
                              iade_tarihi DATE,
                              durum TEXT DEFAULT 'Aktif',
                              FOREIGN KEY (uye_id) REFERENCES uyeler(id),
                              FOREIGN KEY (kitap_id) REFERENCES kitaplar(id))''')
        
        # Cezalar tablosu
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS cezalar
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              odunc_id INTEGER,
                              tutar REAL,
                              odeme_tarihi DATE,
                              durum TEXT DEFAULT 'Ödenmedi',
                              FOREIGN KEY (odunc_id) REFERENCES odunc_islemleri(id))''')
        
        # Ayarlar tablosu
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ayarlar
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              teslim_suresi INTEGER DEFAULT 14,
                              maksimum_kitap INTEGER DEFAULT 5,
                              gunluk_ceza REAL DEFAULT 2.0,
                              otomatik_bildirim INTEGER DEFAULT 1,
                              eposta_bildirim INTEGER DEFAULT 0,
                              kutuphane_adi TEXT DEFAULT '',
                              adres TEXT DEFAULT '')''')
        
        # Varsayılan ayarları ekle (sayısal değerler, metin alanları boş)
        self.cursor.execute("SELECT COUNT(*) FROM ayarlar")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''INSERT INTO ayarlar (teslim_suresi, maksimum_kitap, gunluk_ceza, kutuphane_adi, adres)
                                 VALUES (14, 5, 2.0, '', '')''')
        
        
        self.conn.commit()

    def sidebar_olustur(self):
        """Sol tarafta gezinme menüsü oluşturur"""
        sidebar = tk.Frame(self.ana_container, bg=self.renkler['sidebar_bg'], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Logo
        logo_frame = tk.Frame(sidebar, bg=self.renkler['sidebar_bg'])
        logo_frame.pack(pady=20, padx=10, fill=tk.X)
        
        logo_icon = tk.Label(logo_frame, text="📚", font=("Arial", 24), 
                            bg=self.renkler['sidebar_bg'], fg=self.renkler['sidebar_text'])
        logo_icon.pack()
        
        logo_text1 = tk.Label(logo_frame, text="KütüphaneYS", font=("Arial", 12, "bold"), 
                             bg=self.renkler['sidebar_bg'], fg=self.renkler['sidebar_text'])
        logo_text1.pack()
        
        logo_text2 = tk.Label(logo_frame, text="Yönetim Sistemi", font=("Arial", 8), 
                             bg=self.renkler['sidebar_bg'], fg=self.renkler['sidebar_text'])
        logo_text2.pack()
        
        # Menü başlığı
        menu_baslik = tk.Label(sidebar, text="ANA MENÜ", font=("Arial", 8), 
                              bg=self.renkler['sidebar_bg'], fg="#999999", anchor="w")
        menu_baslik.pack(pady=(20, 10), padx=15, fill=tk.X)
        
        # Menü öğeleri
        menu_items = [
            ("📊 Ana Panel", self.ana_panel_goster),
            ("📖 Kitaplar", self.kitaplar_goster),
            ("📥 Kitap İçe Aktar", self.kitap_ice_aktar),
            ("👥 Üyeler", self.uyeler_goster),
            ("↔️ Ödünç İşlemleri", self.odunc_islemleri_goster),
        ]
        
        for text, command in menu_items:
            btn = tk.Button(sidebar, text=text, font=("Arial", 10), 
                          bg=self.renkler['sidebar_bg'], fg=self.renkler['sidebar_text'],
                          relief=tk.FLAT, anchor="w", padx=20, pady=12, cursor="hand2",
                          activebackground=self.renkler['sidebar_hover'],
                          activeforeground=self.renkler['sidebar_text'],
                          command=command, bd=0)
            btn.pack(fill=tk.X, padx=5, pady=2)
            
            # Hover efekti
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.renkler['sidebar_hover']))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.renkler['sidebar_bg']))
        
        # Yönetim başlığı
        yonetim_baslik = tk.Label(sidebar, text="YÖNETİM", font=("Arial", 8), 
                                 bg=self.renkler['sidebar_bg'], fg="#999999", anchor="w")
        yonetim_baslik.pack(pady=(20, 10), padx=15, fill=tk.X)
        
        # Yönetim menüsü
        yonetim_items = [
            ("🏷️ Kategoriler", self.kategoriler_goster),
            ("⏱️ Gecikme & Ceza", self.gecikme_ceza_goster),
            ("📈 Raporlar", self.raporlar_goster),
            ("⚙️ Ayarlar", self.ayarlar_goster),
        ]
        
        for text, command in yonetim_items:
            btn = tk.Button(sidebar, text=text, font=("Arial", 10), 
                          bg=self.renkler['sidebar_bg'], fg=self.renkler['sidebar_text'],
                          relief=tk.FLAT, anchor="w", padx=20, pady=12, cursor="hand2",
                          activebackground=self.renkler['sidebar_hover'],
                          activeforeground=self.renkler['sidebar_text'],
                          command=command, bd=0)
            btn.pack(fill=tk.X, padx=5, pady=2)
            
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.renkler['sidebar_hover']))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.renkler['sidebar_bg']))

    def icerik_temizle(self):
        """İçerik alanını temizler"""
        for widget in self.icerik_alani.winfo_children():
            widget.destroy()

    def baslik_olustur(self, baslik_text, alt_baslik_text=""):
        """Sayfa başlığı oluşturur"""
        baslik_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        baslik_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
        
        baslik = tk.Label(baslik_frame, text=baslik_text, 
                         font=("Arial", 20, "bold"), 
                         bg=self.renkler['ana_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(anchor="w")
        
        if alt_baslik_text:
            alt_baslik = tk.Label(baslik_frame, text=alt_baslik_text, 
                                 font=("Arial", 10), 
                                 bg=self.renkler['ana_bg'], 
                                 fg=self.renkler['text_light'])
            alt_baslik.pack(anchor="w")

    def kart_olustur(self, parent, baslik, deger, alt_text, icon, renk):
        """İstatistik kartı oluşturur"""
        kart = tk.Frame(parent, bg=self.renkler['kart_bg'], relief=tk.FLAT, bd=0)
        kart.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Gölge efekti için
        kart.config(highlightbackground="#c7c4c4", highlightthickness=1)
        
        icerik_frame = tk.Frame(kart, bg=self.renkler['kart_bg'])
        icerik_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Başlık
        baslik_label = tk.Label(icerik_frame, text=baslik, 
                              font=("Arial", 10), 
                              bg=self.renkler['kart_bg'], 
                              fg=self.renkler['text_light'])
        baslik_label.pack(anchor="w")
        
        # Değer ve ikon
        deger_frame = tk.Frame(icerik_frame, bg=self.renkler['kart_bg'])
        deger_frame.pack(fill=tk.X, pady=(10, 5))
        
        deger_label = tk.Label(deger_frame, text=deger, 
                              font=("Arial", 28, "bold"), 
                              bg=self.renkler['kart_bg'], 
                              fg=self.renkler['text_dark'])
        deger_label.pack(side=tk.LEFT)
        
        icon_label = tk.Label(deger_frame, text=icon, 
                             font=("Arial", 24), 
                             bg=renk, fg="white",
                             width=2, height=1)
        icon_label.pack(side=tk.RIGHT)
        
        # Alt metin
        alt_label = tk.Label(icerik_frame, text=alt_text, 
                             font=("Arial", 9), 
                            bg=self.renkler['kart_bg'], 
                            fg=self.renkler['text_light'])
        alt_label.pack(anchor="w")
        
        return kart

    def ana_panel_goster(self):
        """Ana panel görünümünü gösterir"""
        self.icerik_temizle()
        
        # Başlık
        self.baslik_olustur("Kütüphane Yönetim Sistemi")
        
        # İstatistik kartları
        kartlar_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        kartlar_frame.pack(fill=tk.X, padx=20)
        
        # Verileri al
        self.cursor.execute("SELECT COUNT(*) FROM kitaplar")
        toplam_kitap = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT SUM(stok) FROM kitaplar")
        stok_result = self.cursor.fetchone()[0]
        toplam_stok = stok_result if stok_result else 0
        
        self.cursor.execute("SELECT COUNT(*) FROM uyeler")
        toplam_uye = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM odunc_islemleri WHERE durum='Aktif'")
        aktif_odunc = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM odunc_islemleri WHERE durum='Gecikmiş'")
        geciken_kitap = self.cursor.fetchone()[0]
        
        # Kartları oluştur
        self.kart_olustur(kartlar_frame, "Toplam Kitap", 
                         f"{toplam_kitap:,}", f"+{toplam_stok - toplam_kitap} bu ay",
                          "📚", "#3b5998")
        
        self.kart_olustur(kartlar_frame, "Kayıtlı Üye", 
                         f"{toplam_uye:,}", f"+{min(toplam_uye, 28)} bu ay",
                          "👥", "#4a90e2")
        
        self.kart_olustur(kartlar_frame, "Aktif Ödünç", 
                         str(aktif_odunc), f"{toplam_stok - aktif_odunc} bugün",
                          "↔️", "#5cb85c")
        
        self.kart_olustur(kartlar_frame, "Geciken Kitap", 
                         str(geciken_kitap), f"{geciken_kitap} kritik",
                          "⚠️", "#f0ad4e")
        
        # Alt kısım (Son İşlemler ve En Çok Okunan)
        alt_kisim = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        alt_kisim.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sol: Son İşlemler
        sol_panel = tk.Frame(alt_kisim, bg=self.renkler['kart_bg'])
        sol_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
         
        sol_baslik = tk.Label(sol_panel, text="Son İşlemler", 
                             font=("Arial", 14, "bold"), 
                             bg=self.renkler['kart_bg'], 
                             fg=self.renkler['text_dark'])
        sol_baslik.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Son işlemler listesi
        self.cursor.execute('''SELECT u.ad_soyad, k.ad, o.durum, o.son_teslim
                             FROM odunc_islemleri o 
                             JOIN uyeler u ON o.uye_id = u.id
                             JOIN kitaplar k ON o.kitap_id = k.id
                             WHERE o.iade_tarihi IS NULL OR o.iade_tarihi >= date('now', '-7 days')
                             ORDER BY o.alis_tarihi DESC
                             LIMIT 5''')
        
        son_islemler = self.cursor.fetchall()
        
        for islem in son_islemler:
            islem_frame = tk.Frame(sol_panel, bg=self.renkler['kart_bg'])
            islem_frame.pack(fill=tk.X, padx=20, pady=5)
            
            isim_frame = tk.Frame(islem_frame, bg=self.renkler['kart_bg'])
            isim_frame.pack(fill=tk.X)
            
            isim_label = tk.Label(isim_frame, text=islem[0], 
                                 font=("Arial", 11, "bold"), 
                                 bg=self.renkler['kart_bg'], 
                                 fg=self.renkler['text_dark'])
            isim_label.pack(side=tk.LEFT)
            
            # Durum etiketi
            if islem[2] == 'Aktif':
                durum_renk = '#4a90e2'
                durum_text = 'Ödünç Aldı'
            elif islem[2] == 'Gecikmiş':
                durum_renk = '#d9534f'
                durum_text = 'Ödünç Aldı'
            else:
                durum_renk = '#5cb85c'
                durum_text = 'İade Etti'
            
            durum_label = tk.Label(isim_frame, text=durum_text, 
                                  font=("Arial", 8), 
                                  bg=durum_renk, fg="white",
                                  padx=8, pady=2)
            durum_label.pack(side=tk.RIGHT)
            
            kitap_frame = tk.Frame(islem_frame, bg=self.renkler['kart_bg'])
            kitap_frame.pack(fill=tk.X)
            
            kitap_label = tk.Label(kitap_frame, text=islem[1], 
                                  font=("Arial", 9), 
                                  bg=self.renkler['kart_bg'], 
                                  fg=self.renkler['text_light'])
            kitap_label.pack(side=tk.LEFT)
            
            tarih_obj = datetime.strptime(islem[3], '%Y-%m-%d')
            tarih_label = tk.Label(kitap_frame, 
                                  text=tarih_obj.strftime('%d %b %Y'), 
                                   font=("Arial", 9), 
                                  bg=self.renkler['kart_bg'], 
                                  fg=self.renkler['text_light'])
            tarih_label.pack(side=tk.RIGHT)
            
            # Ayırıcı çizgi
            if islem != son_islemler[-1]:
                tk.Frame(islem_frame, height=1, bg="#bdbaba").pack(fill=tk.X, pady=5)
        
        # Sağ: En Çok Okunan Kitaplar
        sag_panel = tk.Frame(alt_kisim, bg=self.renkler['kart_bg'])
        sag_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sag_baslik = tk.Label(sag_panel, text="En Çok Okunan Kitaplar", 
                             font=("Arial", 14, "bold"), 
                             bg=self.renkler['kart_bg'], 
                             fg=self.renkler['text_dark'])
        sag_baslik.pack(anchor="w", padx=20, pady=(20, 10))
        
        # En çok okunan kitaplar
        self.cursor.execute('''SELECT k.ad, k.yazar, COUNT(o.id) as okuma_sayisi
                             FROM kitaplar k
                              LEFT JOIN odunc_islemleri o ON k.id = o.kitap_id
                             GROUP BY k.id
                             ORDER BY okuma_sayisi DESC
                              LIMIT 5''')
        
        en_cok_okunan = self.cursor.fetchall()
        
        for i, kitap in enumerate(en_cok_okunan, 1):
            kitap_frame = tk.Frame(sag_panel, bg=self.renkler['kart_bg'])
            kitap_frame.pack(fill=tk.X, padx=20, pady=8)
            
            numara_label = tk.Label(kitap_frame, text=str(i), 
                                   font=("Arial", 14, "bold"), 
                                   bg="#c2c0c0", fg=self.renkler['text_dark'],
                                   width=2)
            numara_label.pack(side=tk.LEFT, padx=(0, 10))
            
            bilgi_frame = tk.Frame(kitap_frame, bg=self.renkler['kart_bg'])
            bilgi_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            kitap_ad_label = tk.Label(bilgi_frame, text=kitap[0], 
                                      font=("Arial", 11, "bold"), 
                                     bg=self.renkler['kart_bg'], 
                                     fg=self.renkler['text_dark'],
                                     anchor="w")
            kitap_ad_label.pack(fill=tk.X)
            
            yazar_label = tk.Label(bilgi_frame, text=kitap[1], 
                                  font=("Arial", 9), 
                                  bg=self.renkler['kart_bg'], 
                                  fg=self.renkler['text_light'],
                                  anchor="w")
            yazar_label.pack(fill=tk.X)
            
            okuma_label = tk.Label(kitap_frame, text=f"{kitap[2]} kez", 
                                  font=("Arial", 10), 
                                  bg=self.renkler['kart_bg'], 
                                  fg=self.renkler['text_light'])
            okuma_label.pack(side=tk.RIGHT)

    def kitaplar_goster(self):
        """Kitaplar sayfasını gösterir"""
        self.icerik_temizle()
        
        # Başlık
        baslik_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        baslik_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
         
        baslik = tk.Label(baslik_frame, text="📖 Kitap Yönetimi", 
                         font=("Arial", 20, "bold"), 
                         bg=self.renkler['ana_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(side=tk.LEFT)
        
        self.cursor.execute("SELECT COUNT(*) FROM kitaplar")
        kitap_sayisi = self.cursor.fetchone()[0]
        
        alt_baslik = tk.Label(baslik_frame, text=f"{kitap_sayisi} kitap kayıtlı", 
                             font=("Arial", 10), 
                             bg=self.renkler['ana_bg'], 
                             fg=self.renkler['text_light'])
        alt_baslik.pack(side=tk.LEFT, padx=(10, 0))
        
        # Butonlar (Ekle ve Sil)
        buton_frame = tk.Frame(baslik_frame, bg=self.renkler['ana_bg'])
        buton_frame.pack(side=tk.RIGHT)

        ekle_btn = tk.Button(buton_frame, text="+ Kitap Ekle", 
                           font=("Arial", 10, "bold"), 
                           bg=self.renkler['primary'], fg="white",
                           relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                           command=self.kitap_ekle_dialog)
        ekle_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Düzeltme 3: Kitap Silme Butonu Eklendi
        sil_btn = tk.Button(buton_frame, text="Seçili Kitabı Sil", 
                           font=("Arial", 10, "bold"), 
                           bg=self.renkler['danger'], fg="white",
                           relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                           command=self.kitap_sil)
        sil_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Arama
        arama_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg']) 
        arama_frame.pack(fill=tk.X, padx=30, pady=10)
        
        arama_entry = tk.Entry(arama_frame, font=("Arial", 11), 
                              bg="white", fg=self.renkler['text_dark'],
                              relief=tk.FLAT, bd=2)
        arama_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        arama_entry.insert(0, "🔍 Kitap, yazar veya kategori ara...")
        arama_entry.bind('<FocusIn>', lambda e: arama_entry.delete(0, tk.END) if arama_entry.get().startswith('🔍') else None)
        arama_entry.bind('<FocusOut>', lambda e: arama_entry.insert(0, "🔍 Kitap, yazar veya kategori ara...") if not arama_entry.get() else None)
        arama_entry.bind('<KeyRelease>', lambda e: self.kitaplari_filtrele(arama_entry.get()))
        
        # Tablo
        tablo_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        tablo_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tablo_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        kolonlar = ('Kitap Adı', 'Yazar', 'Yayın Evi', 'ISBN', 'Kategori', 'Raf', 'Stok')
        self.kitaplar_tree = ttk.Treeview(tablo_frame, columns=kolonlar, 
                                          show='headings', yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.kitaplar_tree.yview)
        
        # Kolonları ayarla
        self.kitaplar_tree.heading('Kitap Adı', text='Kitap Adı')
        self.kitaplar_tree.heading('Yazar', text='Yazar')
        self.kitaplar_tree.heading('Yayın Evi', text='Yayın Evi')
        self.kitaplar_tree.heading('ISBN', text='ISBN')
        self.kitaplar_tree.heading('Kategori', text='Kategori')
        self.kitaplar_tree.heading('Raf', text='Raf')
        self.kitaplar_tree.heading('Stok', text='Stok')
        
        self.kitaplar_tree.column('Kitap Adı', width=200)
        self.kitaplar_tree.column('Yazar', width=150)
        self.kitaplar_tree.column('Yayın Evi', width=120)
        self.kitaplar_tree.column('ISBN', width=120)
        self.kitaplar_tree.column('Kategori', width=100)
        self.kitaplar_tree.column('Raf', width=80)
        self.kitaplar_tree.column('Stok', width=60)
        
        self.kitaplar_tree.pack(fill=tk.BOTH, expand=True)
        
        # Sağ tık menüsü
        self.kitaplar_tree.bind('<Button-3>', self.kitap_menu_goster)
        self.kitaplar_tree.bind('<Double-1>', lambda e: self.kitap_duzenle_dialog())
        
        # Verileri yükle
        self.kitaplari_yukle()

    def kitaplari_yukle(self, filtre=''):
        """Kitapları tabloya yükler"""
        # Tabloyu temizle
        for item in self.kitaplar_tree.get_children():
            self.kitaplar_tree.delete(item)
        
        # Verileri çek
        if filtre:
            self.cursor.execute('''SELECT k.id, k.ad, k.yazar, k.yayin_evi, k.isbn, 
                                 kat.ad, k.raf, k.stok
                                 FROM kitaplar k
                                  LEFT JOIN kategoriler kat ON k.kategori_id = kat.id
                                 WHERE k.ad LIKE ? OR k.yazar LIKE ? OR kat.ad LIKE ?
                                 ORDER BY k.ad''',  
                              (f'%{filtre}%', f'%{filtre}%', f'%{filtre}%'))
        else:
            self.cursor.execute('''SELECT k.id, k.ad, k.yazar, k.yayin_evi, k.isbn, 
                                  kat.ad, k.raf, k.stok
                                 FROM kitaplar k
                                 LEFT JOIN kategoriler kat ON k.kategori_id = kat.id
                                  ORDER BY k.ad''')
        
        kitaplar = self.cursor.fetchall()
        
        for kitap in kitaplar:
            # Stok rengini ayarla
            stok = kitap[7]
            if stok == 0: 
                tag = 'stok_yok'
            elif stok <= 2:
                tag = 'stok_az'
            else:
                tag = 'stok_normal'
            
            self.kitaplar_tree.insert('', tk.END, values=kitap[1:], tags=(tag, kitap[0]))
        
         # Tag renklerini ayarla
        self.kitaplar_tree.tag_configure('stok_yok', foreground='red')
        self.kitaplar_tree.tag_configure('stok_az', foreground='orange')
        self.kitaplar_tree.tag_configure('stok_normal', foreground='black')

    def kitaplari_filtrele(self, filtre):
        """Kitapları filtreler"""
        if filtre.startswith('🔍'):
            filtre = ''
        self.kitaplari_yukle(filtre)

    def kitap_menu_goster(self, event):
        """Sağ tık menüsünü gösterir"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Düzenle", command=self.kitap_duzenle_dialog)
        menu.add_command(label="Sil", command=self.kitap_sil)
        menu.post(event.x_root, event.y_root)

    def kitap_ekle_dialog(self):
        """Kitap ekleme dialogunu gösterir"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Yeni Kitap Ekle")
        dialog.geometry("500x600")
        dialog.configure(bg=self.renkler['ana_bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Başlık
        baslik = tk.Label(form_frame, text="Kitap Bilgileri", 
                         font=("Arial", 16, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=(10, 20))
        
        # Form alanları
        alanlar = []
         
        # Kitap Adı
        tk.Label(form_frame, text="Kitap Adı *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        ad_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        ad_entry.pack(fill=tk.X, padx=20, ipady=5)
        alanlar.append(('ad', ad_entry))
        
        # Yazar
        tk.Label(form_frame, text="Yazar *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        yazar_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        yazar_entry.pack(fill=tk.X, padx=20, ipady=5)
        alanlar.append(('yazar', yazar_entry))
        
        # Yayın Evi
        tk.Label(form_frame, text="Yayın Evi", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        yayin_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        yayin_entry.pack(fill=tk.X, padx=20, ipady=5)
        alanlar.append(('yayin_evi', yayin_entry))
        
        # ISBN
        tk.Label(form_frame, text="ISBN", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        isbn_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        isbn_entry.pack(fill=tk.X, padx=20, ipady=5)
        alanlar.append(('isbn', isbn_entry))
        
        # Kategori
        tk.Label(form_frame, text="Kategori", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.cursor.execute("SELECT id, ad FROM kategoriler ORDER BY ad")
        kategoriler = self.cursor.fetchall()
        
        kategori_combo = ttk.Combobox(form_frame, font=("Arial", 11), state='readonly')
        kategori_combo['values'] = [k[1] for k in kategoriler]
        kategori_combo.pack(fill=tk.X, padx=20, ipady=5)
        if kategoriler:
            kategori_combo.current(0)
        alanlar.append(('kategori', kategori_combo))
        
        # Raf
        tk.Label(form_frame, text="Raf", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        raf_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        raf_entry.pack(fill=tk.X, padx=20, ipady=5)
        alanlar.append(('raf', raf_entry))
        
        # Stok
        tk.Label(form_frame, text="Stok Sayısı *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        stok_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        stok_entry.insert(0, "1")
        stok_entry.pack(fill=tk.X, padx=20, ipady=5)
        alanlar.append(('stok', stok_entry))
        
        # Butonlar
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 10))
        
        def kaydet():
            ad = ad_entry.get().strip()
            yazar = yazar_entry.get().strip()
            yayin_evi = yayin_entry.get().strip()
            isbn = isbn_entry.get().strip()
            kategori = kategori_combo.get()
            raf = raf_entry.get().strip()
            stok = stok_entry.get().strip()
            
            if not ad or not yazar:
                messagebox.showerror("Hata", "Kitap adı ve yazar zorunludur!")
                return
            
            if not stok.isdigit():
                messagebox.showerror("Hata", "Stok sayısı geçerli bir sayı olmalıdır!")
                return
            
            # Kategori ID'sini bul
            kategori_id = None
            if kategori:
                for k in kategoriler:
                    if k[1] == kategori: 
                        kategori_id = k[0]
                        break
            
            try:
                self.cursor.execute('''INSERT INTO kitaplar 
                                     (ad, yazar, yayin_evi, isbn, kategori_id, raf, stok)
                                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                  (ad, yazar, yayin_evi if yayin_evi else None, 
                                   isbn if isbn else None, kategori_id, 
                                   raf if raf else None, int(stok)))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Kitap başarıyla eklendi!")
                dialog.destroy()
                self.kitaplari_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu ISBN numarası zaten kayıtlı!")
        
        kaydet_btn = tk.Button(buton_frame, text="Kaydet", 
                              font=("Arial", 10, "bold"), 
                              bg=self.renkler['success'], fg="white",
                              relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                              command=kaydet)
        kaydet_btn.pack(side=tk.LEFT, padx=5)
        
        iptal_btn = tk.Button(buton_frame, text="İptal", 
                             font=("Arial", 10), 
                             bg="#999999", fg="white",
                             relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                             command=dialog.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def kitap_duzenle_dialog(self):
        """Seçili kitabı düzenler"""
        secili = self.kitaplar_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir kitap seçin!")
            return
        
        # Seçili kitabın ID'sini al
        tags = self.kitaplar_tree.item(secili[0], 'tags')
        kitap_id = tags[1]
        
        # Kitap bilgilerini çek
        self.cursor.execute('''SELECT ad, yazar, yayin_evi, isbn, kategori_id, raf, stok
                             FROM kitaplar WHERE id=?''', (kitap_id,))
        kitap = self.cursor.fetchone()
        
         # Dialog oluştur
        dialog = tk.Toplevel(self.root)
        dialog.title("Kitap Düzenle")
        dialog.geometry("500x600")
        dialog.configure(bg=self.renkler['ana_bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Başlık
        baslik = tk.Label(form_frame, text="Kitap Bilgilerini Düzenle", 
                         font=("Arial", 16, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=(10, 20))
        
        # Form alanları
        # Kitap Adı
        tk.Label(form_frame, text="Kitap Adı *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        ad_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        ad_entry.insert(0, kitap[0])
        ad_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Yazar
        tk.Label(form_frame, text="Yazar *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        yazar_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        yazar_entry.insert(0, kitap[1])
        yazar_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Yayın Evi
        tk.Label(form_frame, text="Yayın Evi", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        yayin_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        if kitap[2]:
            yayin_entry.insert(0, kitap[2])
        yayin_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # ISBN
        tk.Label(form_frame, text="ISBN", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        isbn_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        if kitap[3]:
            isbn_entry.insert(0, kitap[3])
        isbn_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Kategori
        tk.Label(form_frame, text="Kategori", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.cursor.execute("SELECT id, ad FROM kategoriler ORDER BY ad")
        kategoriler = self.cursor.fetchall()
        
        kategori_combo = ttk.Combobox(form_frame, font=("Arial", 11), state='readonly')
        kategori_combo['values'] = [k[1] for k in kategoriler]
        kategori_combo.pack(fill=tk.X, padx=20, ipady=5)
        
        # Mevcut kategoriyi seç
        if kitap[4]:
            for i, k in enumerate(kategoriler):
                if k[0] == kitap[4]:
                    kategori_combo.current(i)
                    break
        
        # Raf
        tk.Label(form_frame, text="Raf", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        raf_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        if kitap[5]:
            raf_entry.insert(0, kitap[5])
        raf_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Stok
        tk.Label(form_frame, text="Stok Sayısı *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        stok_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        stok_entry.insert(0, str(kitap[6]))
        stok_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Butonlar
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 10))
        
        def guncelle():
            ad = ad_entry.get().strip()
            yazar = yazar_entry.get().strip()
            yayin_evi = yayin_entry.get().strip()
            isbn = isbn_entry.get().strip()
            kategori = kategori_combo.get()
            raf = raf_entry.get().strip()
            stok = stok_entry.get().strip()
            
            if not ad or not yazar:
                messagebox.showerror("Hata", "Kitap adı ve yazar zorunludur!")
                return
            
            if not stok.isdigit():
                messagebox.showerror("Hata", "Stok sayısı geçerli bir sayı olmalıdır!")
                return
            
            # Kategori ID'sini bul
            kategori_id = None
            if kategori:
                for k in kategoriler:
                    if k[1] == kategori: 
                        kategori_id = k[0]
                        break
            
            try:
                self.cursor.execute('''UPDATE kitaplar 
                                     SET ad=?, yazar=?, yayin_evi=?, isbn=?, 
                                         kategori_id=?, raf=?, stok=?
                                     WHERE id=?''',
                                  (ad, yazar, yayin_evi if yayin_evi else None, 
                                   isbn if isbn else None, kategori_id, 
                                   raf if raf else None, int(stok), kitap_id))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Kitap başarıyla güncellendi!")
                dialog.destroy()
                self.kitaplari_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu ISBN numarası başka bir kitaba ait!")
        
        kaydet_btn = tk.Button(buton_frame, text="Güncelle", 
                              font=("Arial", 10, "bold"), 
                              bg=self.renkler['primary'], fg="white",
                              relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                              command=guncelle)
        kaydet_btn.pack(side=tk.LEFT, padx=5)
        
        iptal_btn = tk.Button(buton_frame, text="İptal", 
                             font=("Arial", 10), 
                             bg="#999999", fg="white",
                             relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                             command=dialog.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def kitap_sil(self):
        """Seçili kitabı siler"""
        secili = self.kitaplar_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir kitap seçin!")
            return
        
        # Seçili kitabın ID'sini al
        tags = self.kitaplar_tree.item(secili[0], 'tags')
        kitap_id = tags[1]
        
        # Onay al
        cevap = messagebox.askyesno("Onay", "Bu kitabı silmek istediğinizden emin misiniz?")
        if cevap:
            try:
                self.cursor.execute("DELETE FROM kitaplar WHERE id=?", (kitap_id,))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Kitap başarıyla silindi!")
                self.kitaplari_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu kitap ödünç işlemlerinde kullanılıyor, silinemez!")

    def uyeler_goster(self):
        """Üyeler sayfasını gösterir"""
        self.icerik_temizle()
        
        # Başlık
        baslik_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        baslik_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
         
        baslik = tk.Label(baslik_frame, text="👥 Üye Yönetimi", 
                         font=("Arial", 20, "bold"), 
                         bg=self.renkler['ana_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(side=tk.LEFT)
        
        self.cursor.execute("SELECT COUNT(*) FROM uyeler")
        uye_sayisi = self.cursor.fetchone()[0]
        
        alt_baslik = tk.Label(baslik_frame, text=f"{uye_sayisi} üye kayıtlı", 
                             font=("Arial", 10), 
                             bg=self.renkler['ana_bg'], 
                             fg=self.renkler['text_light'])
        alt_baslik.pack(side=tk.LEFT, padx=(10, 0))
        
        # Butonlar (Ekle ve Sil)
        buton_frame = tk.Frame(baslik_frame, bg=self.renkler['ana_bg'])
        buton_frame.pack(side=tk.RIGHT)

        ekle_btn = tk.Button(buton_frame, text="+ Üye Ekle", 
                           font=("Arial", 10, "bold"), 
                           bg=self.renkler['primary'], fg="white",
                           relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                           command=self.uye_ekle_dialog)
        ekle_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Düzeltme 2: Üye Silme Butonu Eklendi
        sil_btn = tk.Button(buton_frame, text="Seçili Üyeyi Sil", 
                           font=("Arial", 10, "bold"), 
                           bg=self.renkler['danger'], fg="white",
                           relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                           command=self.uye_sil)
        sil_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Arama
        arama_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        arama_frame.pack(fill=tk.X, padx=30, pady=10)
        
        arama_entry = tk.Entry(arama_frame, font=("Arial", 11), 
                              bg="white", fg=self.renkler['text_dark'],
                              relief=tk.FLAT, bd=2)
        arama_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        arama_entry.insert(0, "🔍 İsim, TC veya telefon ile ara...")
        arama_entry.bind('<FocusIn>', lambda e: arama_entry.delete(0, tk.END) if arama_entry.get().startswith('🔍') else None)
        arama_entry.bind('<FocusOut>', lambda e: arama_entry.insert(0, "🔍 İsim, TC veya telefon ile ara...") if not arama_entry.get() else None)
        arama_entry.bind('<KeyRelease>', lambda e: self.uyeleri_filtrele(arama_entry.get()))
        
        # Tablo
        tablo_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        tablo_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tablo_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        kolonlar = ('Ad Soyad', 'TC Kimlik', 'Telefon', 'E-posta', 'Şehir', 'Kayıt Tarihi')
        self.uyeler_tree = ttk.Treeview(tablo_frame, columns=kolonlar, 
                                        show='headings', yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.uyeler_tree.yview)
        
        # Kolonları ayarla
        for kolon in kolonlar:
            self.uyeler_tree.heading(kolon, text=kolon)
        
        self.uyeler_tree.column('Ad Soyad', width=180)
        self.uyeler_tree.column('TC Kimlik', width=130)
        self.uyeler_tree.column('Telefon', width=130)
        self.uyeler_tree.column('E-posta', width=180)
        self.uyeler_tree.column('Şehir', width=120)
        self.uyeler_tree.column('Kayıt Tarihi', width=120)
        
        self.uyeler_tree.pack(fill=tk.BOTH, expand=True)
        
        # Sağ tık menüsü
        self.uyeler_tree.bind('<Button-3>', self.uye_menu_goster)
        self.uyeler_tree.bind('<Double-1>', lambda e: self.uye_duzenle_dialog())
        
        # Verileri yükle
        self.uyeleri_yukle()

    def uyeleri_yukle(self, filtre=''):
        """Üyeleri tabloya yükler"""
        # Tabloyu temizle
        for item in self.uyeler_tree.get_children():
            self.uyeler_tree.delete(item)
        
        # Verileri çek
        if filtre:
            self.cursor.execute('''SELECT id, ad_soyad, tc_kimlik, telefon, eposta, sehir, kayit_tarihi
                                 FROM uyeler
                                 WHERE ad_soyad LIKE ? OR tc_kimlik LIKE ? OR telefon LIKE ?
                                 ORDER BY ad_soyad''', 
                              (f'%{filtre}%', f'%{filtre}%', f'%{filtre}%'))
        else:
            self.cursor.execute('''SELECT id, ad_soyad, tc_kimlik, telefon, eposta, sehir, kayit_tarihi
                                 FROM uyeler
                                 ORDER BY ad_soyad''')
        
        uyeler = self.cursor.fetchall()
        
        for uye in uyeler:
            # Tarihi formatla
            tarih = datetime.strptime(uye[6], '%Y-%m-%d').strftime('%Y-%m-%d')
            self.uyeler_tree.insert('', tk.END, 
                                   values=(uye[1], uye[2], uye[3], uye[4], uye[5], tarih), 
                                   tags=(uye[0],))

    def uyeleri_filtrele(self, filtre):
        """Üyeleri filtreler"""
        if filtre.startswith('🔍'):
            filtre = ''
        self.uyeleri_yukle(filtre)

    def uye_menu_goster(self, event):
        """Sağ tık menüsünü gösterir"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Düzenle", command=self.uye_duzenle_dialog)
        menu.add_command(label="Sil", command=self.uye_sil)
        menu.post(event.x_root, event.y_root)

    def uye_ekle_dialog(self):
        """Üye ekleme dialogunu gösterir"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Yeni Üye Ekle")
        dialog.geometry("500x650")
        dialog.configure(bg=self.renkler['ana_bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Başlık
        baslik = tk.Label(form_frame, text="Üye Bilgileri", 
                         font=("Arial", 16, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=(10, 20))
        
        # Ad Soyad
        tk.Label(form_frame, text="Ad Soyad *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        ad_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        ad_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # TC Kimlik
        tk.Label(form_frame, text="TC Kimlik No *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        tc_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        tc_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Telefon
        tk.Label(form_frame, text="Telefon", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        telefon_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        telefon_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # E-posta
        tk.Label(form_frame, text="E-posta", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        eposta_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        eposta_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Şehir
        tk.Label(form_frame, text="Şehir", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        sehir_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        sehir_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Butonlar
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 10))
        
        def kaydet():
            ad_soyad = ad_entry.get().strip()
            tc_kimlik = tc_entry.get().strip()
            telefon = telefon_entry.get().strip()
            eposta = eposta_entry.get().strip()
            sehir = sehir_entry.get().strip()
            
            if not ad_soyad or not tc_kimlik:
                messagebox.showerror("Hata", "Ad Soyad ve TC Kimlik No zorunludur!")
                return
            
            if len(tc_kimlik) != 11 or not tc_kimlik.isdigit():
                messagebox.showerror("Hata", "TC Kimlik No 11 haneli olmalıdır!")
                return
            
            kayit_tarihi = datetime.now().strftime('%Y-%m-%d')
            
            try:
                self.cursor.execute('''INSERT INTO uyeler 
                                      (ad_soyad, tc_kimlik, telefon, eposta, sehir, kayit_tarihi)
                                     VALUES (?, ?, ?, ?, ?, ?)''',
                                  (ad_soyad, tc_kimlik, telefon if telefon else None, 
                                   eposta if eposta else None, sehir if sehir else None, 
                                   kayit_tarihi))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Üye başarıyla eklendi!")
                dialog.destroy()
                self.uyeleri_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu TC Kimlik No zaten kayıtlı!")
        
        kaydet_btn = tk.Button(buton_frame, text="Kaydet", 
                              font=("Arial", 10, "bold"), 
                              bg=self.renkler['success'], fg="white",
                              relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                              command=kaydet)
        kaydet_btn.pack(side=tk.LEFT, padx=5)
        
        iptal_btn = tk.Button(buton_frame, text="İptal", 
                             font=("Arial", 10), 
                             bg="#999999", fg="white",
                             relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                             command=dialog.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def uye_duzenle_dialog(self):
        """Seçili üyeyi düzenler"""
        secili = self.uyeler_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir üye seçin!")
            return
        
        # Seçili üyenin ID'sini al
        tags = self.uyeler_tree.item(secili[0], 'tags')
        uye_id = tags[0]
        
        # Üye bilgilerini çek
        self.cursor.execute('''SELECT ad_soyad, tc_kimlik, telefon, eposta, sehir
                             FROM uyeler WHERE id=?''', (uye_id,))
        uye = self.cursor.fetchone()
        
        # Dialog oluştur
        dialog = tk.Toplevel(self.root)
        dialog.title("Üye Düzenle")
        dialog.geometry("500x650")
        dialog.configure(bg=self.renkler['ana_bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Başlık
        baslik = tk.Label(form_frame, text="Üye Bilgilerini Düzenle", 
                         font=("Arial", 16, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=(10, 20))
        
        # Ad Soyad
        tk.Label(form_frame, text="Ad Soyad *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        ad_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        ad_entry.insert(0, uye[0])
        ad_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # TC Kimlik
        tk.Label(form_frame, text="TC Kimlik No *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        tc_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        tc_entry.insert(0, uye[1])
        tc_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Telefon
        tk.Label(form_frame, text="Telefon", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        telefon_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        if uye[2]:
            telefon_entry.insert(0, uye[2])
        telefon_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # E-posta
        tk.Label(form_frame, text="E-posta", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        eposta_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        if uye[3]:
            eposta_entry.insert(0, uye[3])
        eposta_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Şehir
        tk.Label(form_frame, text="Şehir", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        sehir_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        if uye[4]:
            sehir_entry.insert(0, uye[4])
        sehir_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Butonlar
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 10))
        
        def guncelle():
            ad_soyad = ad_entry.get().strip()
            tc_kimlik = tc_entry.get().strip() 
            telefon = telefon_entry.get().strip()
            eposta = eposta_entry.get().strip()
            sehir = sehir_entry.get().strip()
            
            if not ad_soyad or not tc_kimlik:
                messagebox.showerror("Hata", "Ad Soyad ve TC Kimlik No zorunludur!")
                return
            
            if len(tc_kimlik) != 11 or not tc_kimlik.isdigit():
                messagebox.showerror("Hata", "TC Kimlik No 11 haneli olmalıdır!")
                return
            
            try:
                self.cursor.execute('''UPDATE uyeler 
                                     SET ad_soyad=?, tc_kimlik=?, telefon=?, eposta=?, sehir=?
                                     WHERE id=?''',
                                  (ad_soyad, tc_kimlik, telefon if telefon else None, 
                                   eposta if eposta else None, sehir if sehir else None, 
                                   uye_id))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Üye başarıyla güncellendi!")
                dialog.destroy()
                self.uyeleri_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu TC Kimlik No başka bir üyeye ait!")
        
        kaydet_btn = tk.Button(buton_frame, text="Güncelle", 
                              font=("Arial", 10, "bold"), 
                              bg=self.renkler['primary'], fg="white",
                              relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                              command=guncelle)
        kaydet_btn.pack(side=tk.LEFT, padx=5)
        
        iptal_btn = tk.Button(buton_frame, text="İptal", 
                             font=("Arial", 10), 
                             bg="#999999", fg="white",
                             relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                             command=dialog.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def uye_sil(self):
        """Seçili üyeyi siler"""
        secili = self.uyeler_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir üye seçin!")
            return
        
        # Seçili üyenin ID'sini al
        tags = self.uyeler_tree.item(secili[0], 'tags')
        uye_id = tags[0]
        
        # Onay al
        cevap = messagebox.askyesno("Onay", "Bu üyeyi silmek istediğinizden emin misiniz?")
        if cevap:
            try:
                self.cursor.execute("DELETE FROM uyeler WHERE id=?", (uye_id,))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Üye başarıyla silindi!")
                self.uyeleri_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu üye ödünç işlemlerinde kullanılıyor, silinemez!")

    def odunc_islemleri_goster(self):
        """Ödünç işlemleri sayfasını gösterir"""
        self.icerik_temizle()
        
        # Başlık
        baslik_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        baslik_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
         
        baslik = tk.Label(baslik_frame, text="↔️ Ödünç İşlemleri", 
                         font=("Arial", 20, "bold"), 
                         bg=self.renkler['ana_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(side=tk.LEFT)
        
        self.cursor.execute("SELECT COUNT(*) FROM odunc_islemleri WHERE durum='Aktif'")
        aktif_sayisi = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM odunc_islemleri WHERE durum='Gecikmiş'")
        geciken_sayisi = self.cursor.fetchone()[0]
        
        alt_baslik = tk.Label(baslik_frame, 
                             text=f"{aktif_sayisi} aktif, {geciken_sayisi} gecikmiş", 
                             font=("Arial", 10), 
                             bg=self.renkler['ana_bg'], 
                             fg=self.renkler['text_light'])
        alt_baslik.pack(side=tk.LEFT, padx=(10, 0))
        
        ekle_btn = tk.Button(baslik_frame, text="+ Ödünç Ver", 
                           font=("Arial", 10, "bold"), 
                           bg=self.renkler['success'], fg="white",
                           relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                           command=self.odunc_ver_dialog)
        ekle_btn.pack(side=tk.RIGHT)
        
        # Arama
        arama_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        arama_frame.pack(fill=tk.X, padx=30, pady=10)
        
        arama_entry = tk.Entry(arama_frame, font=("Arial", 11), 
                              bg="white", fg=self.renkler['text_dark'],
                              relief=tk.FLAT, bd=2)
        arama_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        arama_entry.insert(0, "🔍 Üye veya kitap ara...")
        arama_entry.bind('<FocusIn>', lambda e: arama_entry.delete(0, tk.END) if arama_entry.get().startswith('🔍') else None)
        arama_entry.bind('<FocusOut>', lambda e: arama_entry.insert(0, "🔍 Üye veya kitap ara...") if not arama_entry.get() else None)
        arama_entry.bind('<KeyRelease>', lambda e: self.odunc_islemlerini_filtrele(arama_entry.get()))
        
        # Tablo
        tablo_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        tablo_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tablo_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        kolonlar = ('Üye', 'Kitap', 'Alış Tarihi', 'Son Teslim', 'İade Tarihi', 'Durum', 'İşlem')
        self.odunc_tree = ttk.Treeview(tablo_frame, columns=kolonlar, 
                                        show='headings', yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.odunc_tree.yview)
        
        # Kolonları ayarla
        for kolon in kolonlar:
            self.odunc_tree.heading(kolon, text=kolon)
        
        self.odunc_tree.column('Üye', width=150)
        self.odunc_tree.column('Kitap', width=200)
        self.odunc_tree.column('Alış Tarihi', width=100)
        self.odunc_tree.column('Son Teslim', width=100)
        self.odunc_tree.column('İade Tarihi', width=100)
        self.odunc_tree.column('Durum', width=100)
        self.odunc_tree.column('İşlem', width=120)
        
        self.odunc_tree.pack(fill=tk.BOTH, expand=True)
        
        # Sağ tık menüsü
        self.odunc_tree.bind('<Button-3>', self.odunc_menu_goster)
        self.odunc_tree.bind('<Double-1>', lambda e: self.iade_al())
        
        # Verileri yükle
        self.odunc_islemlerini_yukle()

    def odunc_islemlerini_yukle(self, filtre=''):
        """Ödünç işlemlerini tabloya yükler"""
        # Tabloyu temizle
        for item in self.odunc_tree.get_children():
            self.odunc_tree.delete(item)
        
        # Verileri çek
        if filtre:
            self.cursor.execute('''SELECT o.id, u.ad_soyad, k.ad, o.alis_tarihi, 
                                 o.son_teslim, o.iade_tarihi, o.durum
                                 FROM odunc_islemleri o
                                  JOIN uyeler u ON o.uye_id = u.id
                                 JOIN kitaplar k ON o.kitap_id = k.id
                                 WHERE u.ad_soyad LIKE ? OR k.ad LIKE ?
                                  ORDER BY o.alis_tarihi DESC''', 
                              (f'%{filtre}%', f'%{filtre}%'))
        else:
            self.cursor.execute('''SELECT o.id, u.ad_soyad, k.ad, o.alis_tarihi, 
                                 o.son_teslim, o.iade_tarihi, o.durum
                                 FROM odunc_islemleri o
                                 JOIN uyeler u ON o.uye_id = u.id
                                 JOIN kitaplar k ON o.kitap_id = k.id
                                 ORDER BY o.alis_tarihi DESC''')
        
        islemler = self.cursor.fetchall()
        
        for islem in islemler:
            # Tarihleri formatla
            alis_tarihi = datetime.strptime(islem[3], '%Y-%m-%d').strftime('%Y-%m-%d')
            son_teslim = datetime.strptime(islem[4], '%Y-%m-%d').strftime('%Y-%m-%d')
            iade_tarihi = datetime.strptime(islem[5], '%Y-%m-%d').strftime('%Y-%m-%d') if islem[5] else '—'
            
            # Durum rengini ayarla
            if islem[6] == 'Aktif':
                tag = 'aktif'
                islem_text = 'İade Al'
            elif islem[6] == 'Gecikmiş':
                tag = 'geciken'
                islem_text = 'İade Al'
            else:
                tag = 'tamamlandi'
                islem_text = islem[5]
            
            self.odunc_tree.insert('', tk.END, 
                                   values=(islem[1], islem[2], alis_tarihi, son_teslim, 
                                         iade_tarihi, islem[6], islem_text), 
                                   tags=(tag, islem[0]))
        
        # Tag renklerini ayarla
        self.odunc_tree.tag_configure('aktif', foreground='#4a90e2')
        self.odunc_tree.tag_configure('geciken', foreground='#d9534f')
        self.odunc_tree.tag_configure('tamamlandi', foreground='#5cb85c')

    def odunc_islemlerini_filtrele(self, filtre):
        """Ödünç işlemlerini filtreler"""
        if filtre.startswith('🔍'):
            filtre = ''
        self.odunc_islemlerini_yukle(filtre)

    def odunc_menu_goster(self, event):
        """Sağ tık menüsünü gösterir"""
        secili = self.odunc_tree.selection()
        if secili:
            # Seçili işlemin durumunu kontrol et
            values = self.odunc_tree.item(secili[0], 'values')
            durum = values[5]
            
            menu = tk.Menu(self.root, tearoff=0)
            if durum in ['Aktif', 'Gecikmiş']:
                menu.add_command(label="İade Al", command=self.iade_al)
            menu.add_command(label="Sil", command=self.odunc_sil)
            menu.post(event.x_root, event.y_root)

    def odunc_ver_dialog(self):
        """Ödünç verme dialogunu gösterir"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ödünç Ver")
        dialog.geometry("500x400")
        dialog.configure(bg=self.renkler['ana_bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Başlık
        baslik = tk.Label(form_frame, text="Ödünç Verme İşlemi", 
                         font=("Arial", 16, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=(10, 20))
        
        # Üye seçimi
        tk.Label(form_frame, text="Üye *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.cursor.execute("SELECT id, ad_soyad FROM uyeler ORDER BY ad_soyad")
        uyeler = self.cursor.fetchall()
        
        uye_combo = ttk.Combobox(form_frame, font=("Arial", 11), state='readonly')
        uye_combo['values'] = [f"{u[1]} (ID: {u[0]})" for u in uyeler]
        uye_combo.pack(fill=tk.X, padx=20, ipady=5)
        if uyeler:
            uye_combo.current(0)
        
        # Kitap seçimi
        tk.Label(form_frame, text="Kitap *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.cursor.execute('''SELECT k.id, k.ad, k.yazar, k.stok
                             FROM kitaplar k
                             WHERE k.stok > 0
                             ORDER BY k.ad''')
        kitaplar = self.cursor.fetchall()
        
        kitap_combo = ttk.Combobox(form_frame, font=("Arial", 11), state='readonly')
        kitap_combo['values'] = [f"{k[1]} - {k[2]} (Stok: {k[3]})" for k in kitaplar]
        kitap_combo.pack(fill=tk.X, padx=20, ipady=5)
        if kitaplar:
            kitap_combo.current(0)
        
        # Ayarları al
        self.cursor.execute("SELECT teslim_suresi FROM ayarlar LIMIT 1")
        teslim_suresi = self.cursor.fetchone()[0]
        
        # Butonlar
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 10))
        
        def kaydet():
            uye_text = uye_combo.get()
            kitap_text = kitap_combo.get()
            
            if not uye_text or not kitap_text:
                messagebox.showerror("Hata", "Lütfen üye ve kitap seçin!")
                return
            
            # ID'leri çıkar
            uye_id = uyeler[uye_combo.current()][0]
            kitap_id = kitaplar[kitap_combo.current()][0]
            
            # Tarihleri ayarla
            alis_tarihi = datetime.now().date()
            son_teslim = alis_tarihi + timedelta(days=teslim_suresi)
            
            try:
                # Ödünç kaydı ekle
                self.cursor.execute('''INSERT INTO odunc_islemleri 
                                     (uye_id, kitap_id, alis_tarihi, son_teslim, durum)
                                     VALUES (?, ?, ?, ?, 'Aktif')''',
                                  (uye_id, kitap_id, alis_tarihi.strftime('%Y-%m-%d'), 
                                   son_teslim.strftime('%Y-%m-%d')))
                
                # Stok güncelle
                self.cursor.execute("UPDATE kitaplar SET stok = stok - 1 WHERE id=?", (kitap_id,))
                
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Kitap başarıyla ödünç verildi!")
                dialog.destroy()
                self.odunc_islemlerini_yukle()
            except Exception as e:
                messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")
        
        kaydet_btn = tk.Button(buton_frame, text="Ödünç Ver", 
                              font=("Arial", 10, "bold"), 
                              bg=self.renkler['success'], fg="white",
                              relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                              command=kaydet)
        kaydet_btn.pack(side=tk.LEFT, padx=5)
        
        iptal_btn = tk.Button(buton_frame, text="İptal", 
                             font=("Arial", 10), 
                             bg="#999999", fg="white",
                             relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                             command=dialog.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def iade_al(self):
        """Seçili ödünç işlemini iade alır"""
        secili = self.odunc_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen iade almak için bir işlem seçin!")
            return
        
        # Seçili işlemin ID'sini al
        tags = self.odunc_tree.item(secili[0], 'tags')
        islem_id = tags[1]
        
        # İşlem durumunu kontrol et
        self.cursor.execute("SELECT durum, kitap_id, son_teslim FROM odunc_islemleri WHERE id=?", (islem_id,))
        islem = self.cursor.fetchone()
        
        if islem[0] == 'İade Edildi':
            messagebox.showinfo("Bilgi", "Bu kitap zaten iade edilmiş!")
            return
        
        # Gecikme kontrolü
        son_teslim = datetime.strptime(islem[2], '%Y-%m-%d').date()
        bugun = datetime.now().date()
        gecikme_gun = (bugun - son_teslim).days
        
        if gecikme_gun > 0:
            # Ceza hesapla
            self.cursor.execute("SELECT gunluk_ceza FROM ayarlar LIMIT 1")
            gunluk_ceza = self.cursor.fetchone()[0]
            toplam_ceza = gecikme_gun * gunluk_ceza
            
            mesaj = f"Bu kitapta {gecikme_gun} gün gecikme var.\n"
            mesaj += f"Toplam ceza: ₺{toplam_ceza:.2f}\n\n"
            mesaj += "İade almak istiyor musunuz?"
            
            cevap = messagebox.askyesno("Gecikme Uyarısı", mesaj)
            if not cevap:
                return
            
            # Ceza kaydı oluştur
            self.cursor.execute('''INSERT INTO cezalar (odunc_id, tutar)
                                  VALUES (?, ?)''', (islem_id, toplam_ceza))
        
        # İade işlemi
        iade_tarihi = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # İade kaydını güncelle
            self.cursor.execute('''UPDATE odunc_islemleri 
                                 SET iade_tarihi=?, durum='İade Edildi'
                                 WHERE id=?''', (iade_tarihi, islem_id))
            
            # Stok güncelle
            self.cursor.execute("UPDATE kitaplar SET stok = stok + 1 WHERE id=?", (islem[1],))
            
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Kitap başarıyla iade alındı!")
            self.odunc_islemlerini_yukle()
        except Exception as e:
            messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")

    def odunc_sil(self):
        """Seçili ödünç işlemini siler"""
        secili = self.odunc_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir işlem seçin!")
            return
        
        # Seçili işlemin ID'sini al
        tags = self.odunc_tree.item(secili[0], 'tags')
        islem_id = tags[1]
        
        # Onay al
        cevap = messagebox.askyesno("Onay", "Bu ödünç işlemini silmek istediğinizden emin misiniz?")
        if cevap:
            try:
                # İşlemi sil
                self.cursor.execute("DELETE FROM odunc_islemleri WHERE id=?", (islem_id,))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "İşlem başarıyla silindi!")
                self.odunc_islemlerini_yukle()
            except Exception as e:
                messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")

    def kategoriler_goster(self):
        """Kategoriler sayfasını gösterir"""
        self.icerik_temizle()
        
        # Başlık
        baslik_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        baslik_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
         
        baslik = tk.Label(baslik_frame, text="🏷️ Kategori Yönetimi", 
                         font=("Arial", 20, "bold"), 
                         bg=self.renkler['ana_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(side=tk.LEFT)
        
        self.cursor.execute("SELECT COUNT(*) FROM kategoriler")
        kategori_sayisi = self.cursor.fetchone()[0]
        
        alt_baslik = tk.Label(baslik_frame, text=f"{kategori_sayisi} kategori", 
                             font=("Arial", 10), 
                             bg=self.renkler['ana_bg'], 
                             fg=self.renkler['text_light'])
        alt_baslik.pack(side=tk.LEFT, padx=(10, 0))
        
        # Butonlar (Ekle ve Sil)
        buton_frame = tk.Frame(baslik_frame, bg=self.renkler['ana_bg'])
        buton_frame.pack(side=tk.RIGHT)

        ekle_btn = tk.Button(buton_frame, text="+ Kategori Ekle", 
                           font=("Arial", 10, "bold"), 
                           bg=self.renkler['primary'], fg="white",
                           relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                           command=self.kategori_ekle_dialog)
        ekle_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Düzeltme 1: Kategori Silme Butonu Eklendi
        sil_btn = tk.Button(buton_frame, text="Seçili Kategoriyi Sil", 
                           font=("Arial", 10, "bold"), 
                           bg=self.renkler['danger'], fg="white",
                           relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                           command=self.kategori_sil)
        sil_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Tablo
        tablo_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        tablo_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tablo_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
         
        # Treeview
        kolonlar = ('Kategori Adı', 'Kitap Sayısı', 'İşlemler')
        self.kategoriler_tree = ttk.Treeview(tablo_frame, columns=kolonlar, 
                                             show='headings', yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.kategoriler_tree.yview)
        
        # Kolonları ayarla
        for kolon in kolonlar:
             self.kategoriler_tree.heading(kolon, text=kolon)
        
        self.kategoriler_tree.column('Kategori Adı', width=400)
        self.kategoriler_tree.column('Kitap Sayısı', width=200)
        self.kategoriler_tree.column('İşlemler', width=200)
        
        self.kategoriler_tree.pack(fill=tk.BOTH, expand=True)
        
        # Sağ tık menüsü
        self.kategoriler_tree.bind('<Button-3>', self.kategori_menu_goster)
        self.kategoriler_tree.bind('<Double-1>', lambda e: self.kategori_duzenle_dialog())
        
        # Verileri yükle
        self.kategorileri_yukle()

    def kategorileri_yukle(self):
        """Kategorileri tabloya yükler"""
        # Tabloyu temizle
        for item in self.kategoriler_tree.get_children():
            self.kategoriler_tree.delete(item)
        
        # Verileri çek
        self.cursor.execute('''SELECT k.id, k.ad, COUNT(kt.id) as kitap_sayisi
                             FROM kategoriler k
                             LEFT JOIN kitaplar kt ON k.id = kt.kategori_id
                              GROUP BY k.id
                             ORDER BY k.ad''')
        
        kategoriler = self.cursor.fetchall()
        
        for kategori in kategoriler:
            self.kategoriler_tree.insert('', tk.END, 
                                        values=(kategori[1], kategori[2], '✏️ 🗑️'), 
                                        tags=(kategori[0],))

    def kategori_menu_goster(self, event):
        """Sağ tık menüsünü gösterir"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Düzenle", command=self.kategori_duzenle_dialog)
        menu.add_command(label="Sil", command=self.kategori_sil)
        menu.post(event.x_root, event.y_root)

    def kategori_ekle_dialog(self):
        """Kategori ekleme dialogunu gösterir"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Yeni Kategori Ekle")
        dialog.geometry("400x250")
        dialog.configure(bg=self.renkler['ana_bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Başlık
        baslik = tk.Label(form_frame, text="Yeni Kategori", 
                         font=("Arial", 16, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=(10, 20))
        
        # Kategori Adı
        tk.Label(form_frame, text="Kategori Adı *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        ad_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        ad_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Butonlar
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 10))
        
        def kaydet():
            ad = ad_entry.get().strip()
            
            if not ad:
                messagebox.showerror("Hata", "Kategori adı zorunludur!")
                return
            
            try:
                self.cursor.execute("INSERT INTO kategoriler (ad) VALUES (?)", (ad,))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Kategori başarıyla eklendi!")
                dialog.destroy()
                self.kategorileri_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu kategori adı zaten mevcut!")
        
        kaydet_btn = tk.Button(buton_frame, text="Kaydet", 
                              font=("Arial", 10, "bold"), 
                              bg=self.renkler['success'], fg="white",
                              relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                              command=kaydet)
        kaydet_btn.pack(side=tk.LEFT, padx=5)
        
        iptal_btn = tk.Button(buton_frame, text="İptal", 
                             font=("Arial", 10), 
                             bg="#999999", fg="white",
                             relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                             command=dialog.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def kategori_duzenle_dialog(self):
        """Seçili kategoriyi düzenler"""
        secili = self.kategoriler_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir kategori seçin!")
            return
        
        # Seçili kategorinin ID'sini al
        tags = self.kategoriler_tree.item(secili[0], 'tags')
        kategori_id = tags[0]
        
        # Kategori bilgilerini çek
        self.cursor.execute("SELECT ad FROM kategoriler WHERE id=?", (kategori_id,))
        kategori = self.cursor.fetchone()
        
        # Dialog oluştur
        dialog = tk.Toplevel(self.root)
        dialog.title("Kategori Düzenle")
        dialog.geometry("400x250")
        dialog.configure(bg=self.renkler['ana_bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Başlık
        baslik = tk.Label(form_frame, text="Kategori Düzenle", 
                         font=("Arial", 16, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=(10, 20))
        
        # Kategori Adı
        tk.Label(form_frame, text="Kategori Adı *", font=("Arial", 10), 
                bg=self.renkler['kart_bg'], fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(10, 5))
        ad_entry = tk.Entry(form_frame, font=("Arial", 11), bg="white", relief=tk.FLAT, bd=2)
        ad_entry.insert(0, kategori[0])
        ad_entry.pack(fill=tk.X, padx=20, ipady=5)
        
        # Butonlar
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 10))
        
        def guncelle():
            ad = ad_entry.get().strip()
            
            if not ad:
                messagebox.showerror("Hata", "Kategori adı zorunludur!")
                return
            
            try:
                self.cursor.execute("UPDATE kategoriler SET ad=? WHERE id=?", (ad, kategori_id))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Kategori başarıyla güncellendi!")
                dialog.destroy()
                self.kategorileri_yukle()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu kategori adı zaten mevcut!")
        
        kaydet_btn = tk.Button(buton_frame, text="Güncelle", 
                              font=("Arial", 10, "bold"), 
                              bg=self.renkler['primary'], fg="white",
                              relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                              command=guncelle)
        kaydet_btn.pack(side=tk.LEFT, padx=5)
        
        iptal_btn = tk.Button(buton_frame, text="İptal", 
                             font=("Arial", 10), 
                             bg="#999999", fg="white",
                             relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                             command=dialog.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=5)

    def kategori_sil(self):
        """Seçili kategoriyi siler"""
        secili = self.kategoriler_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir kategori seçin!")
            return
        
        # Seçili kategorinin ID'sini al
        tags = self.kategoriler_tree.item(secili[0], 'tags')
        kategori_id = tags[0]
        
        # Kategoride kitap var mı kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM kitaplar WHERE kategori_id=?", (kategori_id,))
        kitap_sayisi = self.cursor.fetchone()[0]
        
        if kitap_sayisi > 0:
            messagebox.showerror("Hata", f"Bu kategoride {kitap_sayisi} kitap var! Önce kitapları silin veya başka kategoriye taşıyın.")
            return
        
        # Onay al
        cevap = messagebox.askyesno("Onay", "Bu kategoriyi silmek istediğinizden emin misiniz?")
        if cevap:
            try:
                self.cursor.execute("DELETE FROM kategoriler WHERE id=?", (kategori_id,))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Kategori başarıyla silindi!")
                self.kategorileri_yukle()
            except Exception as e:
                messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")

    def gecikme_ceza_goster(self):
        """Gecikme ve Ceza sayfasını gösterir"""
        self.icerik_temizle()
        
        # Başlık
        self.baslik_olustur("⏱️ Gecikme & Ceza Yönetimi", "Geciken kitaplar ve ceza takibi")
        
        # İstatistik kartları
        kartlar_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        kartlar_frame.pack(fill=tk.X, padx=20)
        
        # Verileri al
        self.cursor.execute("SELECT COUNT(*) FROM cezalar WHERE durum='Ödenmedi'")
        odenmemis_ceza = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT SUM(tutar) FROM cezalar WHERE durum='Ödenmedi'")
        toplam_borc = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT gunluk_ceza FROM ayarlar LIMIT 1")
        gunluk_ceza = self.cursor.fetchone()[0]
        
        # Kartları oluştur
        self.kart_olustur(kartlar_frame, "Ödenmemiş Ceza", 
                         f"{odenmemis_ceza} adet", "", "⚠️", "#d9534f")
        
        self.kart_olustur(kartlar_frame, "Toplam Borç", 
                         f"₺{toplam_borc:.2f}", "", "⏱️", "#f0ad4e")
        
        self.kart_olustur(kartlar_frame, "Günlük Ceza", 
                         f"₺{gunluk_ceza:.2f}", "Gecikme başına", "✓", "#5cb85c")
        
        # Ceza Listesi
        liste_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        liste_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        baslik = tk.Label(liste_frame, text="Ceza Listesi", 
                         font=("Arial", 14, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Tablo
        # Scrollbar
        scrollbar = ttk.Scrollbar(liste_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        kolonlar = ('Üye', 'Kitap', 'Gecikme (Gün)', 'Tutar', 'Durum', 'İşlem')
        self.cezalar_tree = ttk.Treeview(liste_frame, columns=kolonlar, 
                                        show='headings', yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.cezalar_tree.yview)
        
        # Kolonları ayarla
        for kolon in kolonlar:
            self.cezalar_tree.heading(kolon, text=kolon)
        
        self.cezalar_tree.column('Üye', width=150)
        self.cezalar_tree.column('Kitap', width=200)
        self.cezalar_tree.column('Gecikme (Gün)', width=120) 
        self.cezalar_tree.column('Tutar', width=100)
        self.cezalar_tree.column('Durum', width=100)
        self.cezalar_tree.column('İşlem', width=120)
        
        self.cezalar_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Sağ tık menüsü
        self.cezalar_tree.bind('<Button-3>', self.ceza_menu_goster)
        self.cezalar_tree.bind('<Double-1>', lambda e: self.ceza_ode())
        
        # Verileri yükle
        self.cezalari_yukle()

    def cezalari_yukle(self):
        """Cezaları tabloya yükler"""
        # Tabloyu temizle
        for item in self.cezalar_tree.get_children():
            self.cezalar_tree.delete(item)
        
        # Verileri çek
        self.cursor.execute('''SELECT c.id, u.ad_soyad, k.ad, 
                             julianday(COALESCE(o.iade_tarihi, date('now'))) - julianday(o.son_teslim) as gecikme,
                             c.tutar, c.durum
                              FROM cezalar c
                             JOIN odunc_islemleri o ON c.odunc_id = o.id
                             JOIN uyeler u ON o.uye_id = u.id
                              JOIN kitaplar k ON o.kitap_id = k.id
                             ORDER BY c.id DESC''')
        
        cezalar = self.cursor.fetchall()
        
        for ceza in cezalar:
            # Durum rengini ayarla
            if ceza[5] == 'Ödendi':
                tag = 'odendi'
                islem_text = ceza[5]
            else:
                tag = 'odenmedi'
                islem_text = 'Ödendi İşaretle'
            
            self.cezalar_tree.insert('', tk.END, 
                                    values=(ceza[1], ceza[2], int(ceza[3]), 
                                           f"₺{ceza[4]:.2f}", ceza[5], islem_text), 
                                    tags=(tag, ceza[0]))
        
        # Tag renklerini ayarla
        self.cezalar_tree.tag_configure('odendi', foreground='#5cb85c')
        self.cezalar_tree.tag_configure('odenmedi', foreground='#d9534f')

    def ceza_menu_goster(self, event):
        """Sağ tık menüsünü gösterir"""
        secili = self.cezalar_tree.selection()
        if secili:
            # Seçili cezanın durumunu kontrol et
            values = self.cezalar_tree.item(secili[0], 'values')
            durum = values[4]
            
            menu = tk.Menu(self.root, tearoff=0)
            if durum == 'Ödenmedi':
                menu.add_command(label="Ödendi İşaretle", command=self.ceza_ode)
            menu.post(event.x_root, event.y_root)

    def ceza_ode(self):
        """Seçili cezayı ödendi olarak işaretler"""
        secili = self.cezalar_tree.selection()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen işaretlemek için bir ceza seçin!")
            return
        
        # Seçili cezanın ID'sini al
        tags = self.cezalar_tree.item(secili[0], 'tags')
        ceza_id = tags[1]
        
        # Ceza durumunu kontrol et
        self.cursor.execute("SELECT durum FROM cezalar WHERE id=?", (ceza_id,))
        durum = self.cursor.fetchone()[0]
        
        if durum == 'Ödendi':
            messagebox.showinfo("Bilgi", "Bu ceza zaten ödenmiş!")
            return
        
        # Onay al
        cevap = messagebox.askyesno("Onay", "Bu ceza ödenmiş olarak işaretlensin mi?")
        if cevap:
            try:
                odeme_tarihi = datetime.now().strftime('%Y-%m-%d')
                self.cursor.execute('''UPDATE cezalar 
                                     SET durum='Ödendi', odeme_tarihi=?
                                     WHERE id=?''', (odeme_tarihi, ceza_id))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Ceza ödenmiş olarak işaretlendi!")
                self.cezalari_yukle()
                # Ana paneli güncelle
                if hasattr(self, 'ana_panel_goster'):
                    self.gecikme_ceza_goster()
            except Exception as e:
                messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")

    def raporlar_goster(self):
        """Raporlar sayfasını gösterir"""
        self.icerik_temizle()
        
        # Başlık
        self.baslik_olustur("📈 Raporlar", "Kütüphane istatistikleri ve analizleri")
        
        # Üst kısım: Grafikler
        grafikler_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        grafikler_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Sol : Aylık Ödünç/İade Grafiği
        sol_grafik = tk.Frame(grafikler_frame, bg=self.renkler['kart_bg'])
        sol_grafik.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        baslik = tk.Label(sol_grafik, text="📊 Aylık Ödünç / İade", 
                         font=("Arial", 12, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=10)
        
        # Grafik verileri
        fig = Figure(figsize=(6, 3), dpi=80)
        ax = fig.add_subplot(111)
        
        # Örnek veriler (son 12 ay)
        aylar = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
        odunc = [45, 50, 60, 48, 55, 68, 40, 38, 58, 62, 70, 50]
        iade = [38, 45, 55, 50, 50, 60, 45, 40, 52, 55, 65, 50]
        
        x = range(len(aylar))
        ax.bar([i - 0.2 for i in x], odunc, width=0.4, label='Ödünç', color='#3b5998')
        ax.bar([i + 0.2 for i in x], iade, width=0.4, label='İade', color='#f0ad4e')
        
        ax.set_xticks(x)
        ax.set_xticklabels(aylar)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, master=sol_grafik)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sağ: Kategoriler Grafiği
        sag_grafik = tk.Frame(grafikler_frame, bg=self.renkler['kart_bg'])
        sag_grafik.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        baslik = tk.Label(sag_grafik, text="📚 Kategoriler", 
                         font=("Arial", 12, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=10)
        
        # Kategori verileri
        self.cursor.execute('''SELECT k.ad, COUNT(kt.id) as sayi
                             FROM kategoriler k
                             LEFT JOIN kitaplar kt ON k.id = kt.kategori_id
                              GROUP BY k.id
                             ORDER BY sayi DESC
                             LIMIT 5''')
        
        kategori_verileri = self.cursor.fetchall()
        
        if kategori_verileri:
            fig2 = Figure(figsize=(4, 3), dpi=80)
            ax2 = fig2.add_subplot(111)
            
            etiketler = [k[0] for k in kategori_verileri]
            boyutlar = [k[1] for k in kategori_verileri]
            renkler_pie = ['#3b5998', '#8b9dc3', '#f0ad4e', '#5cb85c', '#999999']
            
            ax2.pie(boyutlar, labels=etiketler, autopct='%1.0f%%', 
                    colors=renkler_pie, startangle=90)
            ax2.axis('equal')
            
            canvas2 = FigureCanvasTkAgg(fig2, master=sag_grafik)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Alt kısım: Tablolar
        tablolar_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        tablolar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Sol: En Aktif Üyeler
        sol_tablo = tk.Frame(tablolar_frame, bg=self.renkler['kart_bg'])
        sol_tablo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        baslik = tk.Label(sol_tablo, text="👥 En Aktif Üyeler", 
                         font=("Arial", 12, "bold"), 
                         bg=self.renkler['kart_bg'], 
                         fg=self.renkler['text_dark'])
        baslik.pack(pady=10)
        
        # Tablo
        kolonlar = ('#', 'Üye', 'Okunan', 'Mevcut')
        aktif_tree = ttk.Treeview(sol_tablo, columns=kolonlar, show='headings', height=5)
        
        for kolon in kolonlar:
            aktif_tree.heading(kolon, text=kolon)
            aktif_tree.column(kolon, width=100)
        
        # En aktif üyeleri getir
        self.cursor.execute('''SELECT u.ad_soyad, COUNT(o.id) as okunan,
                             SUM(CASE WHEN o.durum='Aktif' THEN 1 ELSE 0 END) as mevcut
                             FROM uyeler u
                             LEFT JOIN odunc_islemleri o ON u.id = o.uye_id
                              GROUP BY u.id
                             ORDER BY okunan DESC
                             LIMIT 5''')
        
        aktif_uyeler = self.cursor.fetchall()
        
        for i, uye in enumerate(aktif_uyeler, 1):
            aktif_tree.insert('', tk.END, values=(i, uye[0], uye[1], uye[2]))
        
        aktif_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Sağ: Geciken Kitaplar
        sag_tablo = tk.Frame(tablolar_frame, bg=self.renkler['kart_bg'])
        sag_tablo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        baslik = tk.Label(sag_tablo, text="Geciken Kitaplar", 
                         font=("Arial", 12, "bold"), 
                         bg="#d9534f", 
                         fg="white")
        baslik.pack(fill=tk.X, pady=10)
        
        # Tablo
        kolonlar = ('Üye', 'Kitap', 'Gecikme')
        geciken_tree = ttk.Treeview(sag_tablo, columns=kolonlar, show='headings', height=5)
        
        for kolon in kolonlar:
            geciken_tree.heading(kolon, text=kolon)
        
        geciken_tree.column('Üye', width=150)
        geciken_tree.column('Kitap', width=200)
        geciken_tree.column('Gecikme', width=100)
        
        # Geciken kitapları getir
        self.cursor.execute('''SELECT u.ad_soyad, k.ad, 
                             CAST(julianday(date('now')) - julianday(o.son_teslim) AS INTEGER) as gecikme
                             FROM odunc_islemleri o
                             JOIN uyeler u ON o.uye_id = u.id
                              JOIN kitaplar k ON o.kitap_id = k.id
                             WHERE o.durum='Gecikmiş'
                             ORDER BY gecikme DESC
                             LIMIT 3''')
        
        geciken_kitaplar = self.cursor.fetchall()
        
        for kitap in geciken_kitaplar:
            geciken_tree.insert('', tk.END, values=(kitap[0], kitap[1], f"{kitap[2]} gün"))
        
        geciken_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def ayarlar_goster(self):
        """Ayarlar sayfasını gösterir"""
        self.icerik_temizle()
        
        # Başlık
        self.baslik_olustur("⚙️ Ayarlar", "Sistem yapılandırması")
        
        # Düzeltme 4: Ayarlar Sayfasına Scrollbar Eklendi
        # Canvas ve Scrollbar yapısı
        canvas_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg=self.renkler['ana_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=self.renkler['kart_bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel desteği
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mevcut ayarları al
        self.cursor.execute('''SELECT teslim_suresi, maksimum_kitap, gunluk_ceza,
                             otomatik_bildirim, eposta_bildirim,
                              kutuphane_adi, adres FROM ayarlar LIMIT 1''')
        ayarlar = self.cursor.fetchone()
        
        # Form (Artık scrollable_frame içinde)
        form_frame = tk.Frame(scrollable_frame, bg=self.renkler['kart_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Ödünç Alma Ayarları
        odunc_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        odunc_frame.pack(fill=tk.X, padx=20, pady=20)
        
        odunc_baslik = tk.Label(odunc_frame, text="📅 Ödünç Alma Ayarları", 
                               font=("Arial", 14, "bold"), 
                               bg=self.renkler['kart_bg'], 
                               fg=self.renkler['text_dark'])
        odunc_baslik.pack(anchor="w", pady=(0, 15))
        
        odunc_alt = tk.Label(odunc_frame, text="Kitap ödünç alma ile ilgili kurallar", 
                            font=("Arial", 9), 
                            bg=self.renkler['kart_bg'], 
                            fg=self.renkler['text_light'])
        odunc_alt.pack(anchor="w", pady=(0, 15))
        
        # Teslim Süresi
        teslim_frame = tk.Frame(odunc_frame, bg=self.renkler['kart_bg'])
        teslim_frame.pack(fill=tk.X, pady=10)
        
        teslim_sol = tk.Frame(teslim_frame, bg=self.renkler['kart_bg'])
        teslim_sol.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(teslim_sol, text="Teslim Süresi (Gün)", 
                font=("Arial", 11, "bold"), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w")
        
        tk.Label(teslim_sol, text="Varsayılan ödünç süresi", 
                font=("Arial", 9), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_light']).pack(anchor="w")
        
        teslim_entry = tk.Entry(teslim_frame, font=("Arial", 16, "bold"), 
                               bg="white", relief=tk.FLAT, bd=2, width=5,
                               justify=tk.CENTER)
        teslim_entry.insert(0, str(ayarlar[0]))
        teslim_entry.pack(side=tk.RIGHT, padx=20)
        
        # Maksimum Kitap
        maksimum_frame = tk.Frame(odunc_frame, bg=self.renkler['kart_bg'])
        maksimum_frame.pack(fill=tk.X, pady=10)
        
        maksimum_sol = tk.Frame(maksimum_frame, bg=self.renkler['kart_bg'])
        maksimum_sol.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(maksimum_sol, text="Maksimum Kitap", 
                font=("Arial", 11, "bold"), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w")
        
        tk.Label(maksimum_sol, text="Aynı anda alınabilir", 
                font=("Arial", 9), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_light']).pack(anchor="w")
        
        maksimum_entry = tk.Entry(maksimum_frame, font=("Arial", 16, "bold"), 
                                 bg="white", relief=tk.FLAT, bd=2, width=5,
                                 justify=tk.CENTER)
        maksimum_entry.insert(0, str(ayarlar[1]))
        maksimum_entry.pack(side=tk.RIGHT, padx=20)
         
        # Günlük Ceza
        ceza_frame = tk.Frame(odunc_frame, bg=self.renkler['kart_bg'])
        ceza_frame.pack(fill=tk.X, pady=10)
        
        ceza_sol = tk.Frame(ceza_frame, bg=self.renkler['kart_bg'])
        ceza_sol.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(ceza_sol, text="Günlük Ceza (₺)", 
                font=("Arial", 11, "bold"), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w")
        
        tk.Label(ceza_sol, text="Gecikme başına", 
                font=("Arial", 9), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_light']).pack(anchor="w")
        
        ceza_entry = tk.Entry(ceza_frame, font=("Arial", 16, "bold"), 
                             bg="white", relief=tk.FLAT, bd=2, width=5,
                             justify=tk.CENTER)
        ceza_entry.insert(0, str(ayarlar[2]))
        ceza_entry.pack(side=tk.RIGHT, padx=20)
        
        # Ayırıcı
        tk.Frame(form_frame, height=2, bg="#e0e0e0").pack(fill=tk.X, padx=20, pady=20)
        
        # Bildirim Ayarları
        bildirim_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        bildirim_frame.pack(fill=tk.X, padx=20, pady=20)
        
        bildirim_baslik = tk.Label(bildirim_frame, text="🔔 Bildirim Ayarları", 
                                  font=("Arial", 14, "bold"), 
                                  bg=self.renkler['kart_bg'], 
                                  fg=self.renkler['text_dark'])
        bildirim_baslik.pack(anchor="w", pady=(0, 15))
        
        bildirim_alt = tk.Label(bildirim_frame, text="Otomatik bildirim tercihleri", 
                               font=("Arial", 9), 
                               bg=self.renkler['kart_bg'], 
                               fg=self.renkler['text_light'])
        bildirim_alt.pack(anchor="w", pady=(0, 15))
        
        # Otomatik gecikme bildirimi
        otomatik_frame = tk.Frame(bildirim_frame, bg=self.renkler['kart_bg'])
        otomatik_frame.pack(fill=tk.X, pady=10)
        
        otomatik_sol = tk.Frame(otomatik_frame, bg=self.renkler['kart_bg'])
        otomatik_sol.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(otomatik_sol, text="Otomatik gecikme bildirimi", 
                font=("Arial", 11, "bold"), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w")
        
        tk.Label(otomatik_sol, text="Teslim tarihi geçince otomatik bildirim gönder", 
                font=("Arial", 9), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_light']).pack(anchor="w")
        
        otomatik_var = tk.BooleanVar(value=bool(ayarlar[3]))
        otomatik_check = tk.Checkbutton(otomatik_frame, variable=otomatik_var,
                                       bg=self.renkler['kart_bg'], 
                                       activebackground=self.renkler['kart_bg'])
        otomatik_check.pack(side=tk.RIGHT, padx=20)
        
        # E-posta bildirimleri 
        eposta_frame = tk.Frame(bildirim_frame, bg=self.renkler['kart_bg'])
        eposta_frame.pack(fill=tk.X, pady=10)
        
        eposta_sol = tk.Frame(eposta_frame, bg=self.renkler['kart_bg'])
        eposta_sol.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(eposta_sol, text="E-posta bildirimleri", 
                font=("Arial", 11, "bold"), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w")
        
        tk.Label(eposta_sol, text="Üyelere e-posta ile hatırlatma gönder", 
                font=("Arial", 9), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_light']).pack(anchor="w")
        
        eposta_var = tk.BooleanVar(value=bool(ayarlar[4]))
        eposta_check = tk.Checkbutton(eposta_frame, variable=eposta_var,
                                     bg=self.renkler['kart_bg'], 
                                     activebackground=self.renkler['kart_bg'])
        eposta_check.pack(side=tk.RIGHT, padx=20)
        
        # Ayırıcı
        tk.Frame(form_frame, height=2, bg="#e0e0e0").pack(fill=tk.X, padx=20, pady=20)
        
        # Kütüphane Bilgileri
        bilgi_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        bilgi_frame.pack(fill=tk.X, padx=20, pady=20)
        
        bilgi_baslik = tk.Label(bilgi_frame, text="📍 Kütüphane Bilgileri", 
                               font=("Arial", 14, "bold"), 
                               bg=self.renkler['kart_bg'], 
                               fg=self.renkler['text_dark'])
        bilgi_baslik.pack(anchor="w", pady=(0, 15))
        
        bilgi_alt = tk.Label(bilgi_frame, text="Genel bilgiler", 
                            font=("Arial", 9), 
                            bg=self.renkler['kart_bg'], 
                            fg=self.renkler['text_light'])
        bilgi_alt.pack(anchor="w", pady=(0, 15))
        
        # Kütüphane Adı
        tk.Label(bilgi_frame, text="Kütüphane Adı", 
                font=("Arial", 10), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w", pady=(10, 5))
        
        kutuphane_entry = tk.Entry(bilgi_frame, font=("Arial", 11), 
                                  bg="white", relief=tk.FLAT, bd=2)
        kutuphane_entry.insert(0, ayarlar[5])
        kutuphane_entry.pack(fill=tk.X, ipady=5)
        
        # Adres
        tk.Label(bilgi_frame, text="Adres", 
                font=("Arial", 10), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w", pady=(10, 5))
        
        adres_entry = tk.Entry(bilgi_frame, font=("Arial", 11), 
                              bg="white", relief=tk.FLAT, bd=2)
        adres_entry.insert(0, ayarlar[6])
        adres_entry.pack(fill=tk.X, ipady=5)
        
        # Kaydet Butonu
        buton_frame = tk.Frame(form_frame, bg=self.renkler['kart_bg'])
        buton_frame.pack(pady=(30, 20))
        
        def ayarlari_kaydet():
            teslim_suresi = teslim_entry.get()
            maksimum_kitap = maksimum_entry.get()
            gunluk_ceza = ceza_entry.get()
            kutuphane_adi = kutuphane_entry.get()
            adres = adres_entry.get()
            
            # Validasyon
            if not teslim_suresi.isdigit() or not maksimum_kitap.isdigit():
                messagebox.showerror("Hata", "Teslim süresi ve maksimum kitap sayısal olmalıdır!")
                return
            
            try:
                gunluk_ceza_float = float(gunluk_ceza)
            except ValueError:
                messagebox.showerror("Hata", "Günlük ceza geçerli bir sayı olmalıdır!")
                return
            
            # Kaydet
            try:
                self.cursor.execute('''UPDATE ayarlar 
                                     SET teslim_suresi=?, maksimum_kitap=?, gunluk_ceza=?,
                                         otomatik_bildirim=?, eposta_bildirim=?,
                                         kutuphane_adi=?, adres=?''',
                                   (int(teslim_suresi), int(maksimum_kitap), gunluk_ceza_float,
                                   int(otomatik_var.get()), int(eposta_var.get()),
                                    kutuphane_adi, adres))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Ayarlar başarıyla kaydedildi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")
        
        kaydet_btn = tk.Button(buton_frame, text="💾 Ayarları Kaydet", 
                              font=("Arial", 11, "bold"), 
                              bg=self.renkler['primary'], fg="white",
                              relief=tk.FLAT, padx=40, pady=12, cursor="hand2",
                              command=ayarlari_kaydet)
        kaydet_btn.pack()

    def kitap_ice_aktar(self):
        """Excel veya CSV dosyasından kitap içe aktarır"""
        self.icerik_temizle()
        
        # Başlık
        baslik_frame = tk.Frame(self.icerik_alani, bg=self.renkler['ana_bg'])
        baslik_frame.pack(fill=tk.X, padx=30, pady=(30, 20))
        
        tk.Label(baslik_frame, text="📥 Kitap İçe Aktarma", 
                font=("Arial", 24, "bold"), 
                bg=self.renkler['ana_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w")
        
        # Açıklama kartı
        aciklama_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        aciklama_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Label(aciklama_frame, text="📋 Dosya Formatı", 
                font=("Arial", 16, "bold"), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_dark']).pack(anchor="w", padx=20, pady=(20, 10))
        
        aciklama_text = """Excel (.xlsx) veya CSV (.csv) formatında kitap listesi yükleyebilirsiniz.

Dosyanızda şu sütunlar olmalıdır:
• Kitap Adı (zorunlu)
• Yazar (zorunlu)
• Yayın Evi (opsiyonel)
• ISBN (opsiyonel)
• Kategori (opsiyonel - yoksa otomatik oluşturulur)
• Raf (opsiyonel)
• Stok (opsiyonel - belirtilmezse 1 kabul edilir)

İpucu: İlk satır sütun başlıklarını içermelidir."""
        
        tk.Label(aciklama_frame, text=aciklama_text, 
                font=("Arial", 10), 
                bg=self.renkler['kart_bg'], 
                fg=self.renkler['text_light'],
                justify=tk.LEFT).pack(anchor="w", padx=20, pady=(0, 20))
        
        # Dosya seçme alanı
        dosya_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        dosya_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        dosya_label = tk.Label(dosya_frame, text="Seçilen Dosya: Henüz dosya seçilmedi", 
                             font=("Arial", 11), 
                             bg=self.renkler['kart_bg'], 
                             fg=self.renkler['text_light'])
        dosya_label.pack(padx=20, pady=20)
        
        dosya_yolu = {"yol": None}
        
        def dosya_sec():
            dosya = filedialog.askopenfilename(
                title="Kitap Listesi Seç",
                filetypes=[("Excel Dosyası", "*.xlsx"), ("CSV Dosyası", "*.csv"), ("Tüm Dosyalar", "*.*")]
            )
            if dosya:
                dosya_yolu["yol"] = dosya
                dosya_label.config(text=f"Seçilen Dosya: {os.path.basename(dosya)}")
                yukle_btn.config(state=tk.NORMAL)
        
        sec_btn = tk.Button(dosya_frame, text="📁 Dosya Seç", 
                          font=("Arial", 12, "bold"), 
                          bg=self.renkler['primary'], fg="white",
                          relief=tk.FLAT, padx=30, pady=15, cursor="hand2",
                          command=dosya_sec)
        sec_btn.pack(pady=(0, 20))
        
        # Sonuç alanı
        sonuc_frame = tk.Frame(self.icerik_alani, bg=self.renkler['kart_bg'])
        sonuc_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))
        
        sonuc_text = tk.Text(sonuc_frame, font=("Courier", 10), 
                           bg="white", fg=self.renkler['text_dark'],
                           relief=tk.FLAT, bd=2, wrap=tk.WORD)
        sonuc_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        def yukle():
            if not dosya_yolu["yol"]:
                messagebox.showerror("Hata", "Lütfen önce bir dosya seçin!")
                return
            
            sonuc_text.delete(1.0, tk.END)
            sonuc_text.insert(tk.END, "Dosya yükleniyor...\n\n")
            self.root.update()
            
            try:
                # Dosya uzantısına göre okuma
                dosya_adi = dosya_yolu["yol"]
                
                if dosya_adi.endswith('.csv'):
                    # CSV okuma
                    df = pd.read_csv(dosya_adi)
                elif dosya_adi.endswith('.xlsx'):
                    # Excel okuma
                    df = pd.read_excel(dosya_adi)
                else:
                    messagebox.showerror("Hata", "Desteklenmeyen dosya formatı!")
                    return
                
                # Sütun adlarını normalize et (küçük harf ve boşluk temizleme)
                df.columns = df.columns.str.lower().str.strip()
                
                # Sütun eşleştirmeleri
                sutun_esleme = {
                    'kitap adı': 'ad',
                    'kitap adi': 'ad',
                    'ad': 'ad',
                    'kitap': 'ad',
                    'yazar': 'yazar',
                    'yayin evi': 'yayin_evi',
                    'yayın evi': 'yayin_evi',
                    'yayinevi': 'yayin_evi',
                    'yayınevi': 'yayin_evi',
                    'isbn': 'isbn',
                    'kategori': 'kategori',
                    'raf': 'raf',
                    'stok': 'stok'
                }
                
                # Sütunları yeniden adlandır
                df = df.rename(columns=sutun_esleme)
                
                # Zorunlu sütunları kontrol et
                if 'ad' not in df.columns or 'yazar' not in df.columns:
                    messagebox.showerror("Hata", "Dosyada 'Kitap Adı' ve 'Yazar' sütunları zorunludur!")
                    return
                
                # Boş satırları temizle
                df = df.dropna(subset=['ad', 'yazar'])
                
                # İstatistikler
                basarili = 0
                hatali = 0
                toplam = len(df)
                
                sonuc_text.insert(tk.END, f"Toplam {toplam} kitap bulundu.\n")
                sonuc_text.insert(tk.END, "İşleniyor...\n\n")
                self.root.update()
                
                for index, row in df.iterrows():
                    try:
                        ad = str(row['ad']).strip()
                        yazar = str(row['yazar']).strip()
                        yayin_evi = str(row.get('yayin_evi', '')).strip() if pd.notna(row.get('yayin_evi')) else None
                        isbn = str(row.get('isbn', '')).strip() if pd.notna(row.get('isbn')) else None
                        kategori_adi = str(row.get('kategori', '')).strip() if pd.notna(row.get('kategori')) else None
                        raf = str(row.get('raf', '')).strip() if pd.notna(row.get('raf')) else None
                        stok = int(row.get('stok', 1)) if pd.notna(row.get('stok')) else 1
                        
                        # Kategori ID'sini bul veya oluştur
                        kategori_id = None
                        if kategori_adi:
                            self.cursor.execute("SELECT id FROM kategoriler WHERE ad=?", (kategori_adi,))
                            result = self.cursor.fetchone()
                            if result:
                                kategori_id = result[0]
                            else:
                                # Yeni kategori oluştur
                                self.cursor.execute("INSERT INTO kategoriler (ad) VALUES (?)", (kategori_adi,))
                                kategori_id = self.cursor.lastrowid
                        
                        # Kitabı ekle
                        self.cursor.execute("""INSERT INTO kitaplar 
                                             (ad, yazar, yayin_evi, isbn, kategori_id, raf, stok)
                                             VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                          (ad, yazar, yayin_evi, isbn, kategori_id, raf, stok))
                        
                        basarili += 1
                        sonuc_text.insert(tk.END, f"✓ {ad} - {yazar}\n")
                        
                    except sqlite3.IntegrityError as e:
                        hatali += 1
                        sonuc_text.insert(tk.END, f"✗ {ad} - HATA: ISBN zaten kayıtlı\n")
                    except Exception as e:
                        hatali += 1
                        sonuc_text.insert(tk.END, f"✗ {ad} - HATA: {str(e)}\n")
                    
                    # Her 10 kayıtta bir commit yap
                    if (index + 1) % 10 == 0:
                        self.conn.commit()
                        self.root.update()
                
                # Son commit
                self.conn.commit()
                
                # Özet
                sonuc_text.insert(tk.END, f"\n{'='*50}\n")
                sonuc_text.insert(tk.END, f"İŞLEM TAMAMLANDI\n")
                sonuc_text.insert(tk.END, f"{'='*50}\n")
                sonuc_text.insert(tk.END, f"Toplam: {toplam}\n")
                sonuc_text.insert(tk.END, f"Başarılı: {basarili}\n")
                sonuc_text.insert(tk.END, f"Hatalı: {hatali}\n")
                
                if basarili > 0:
                    messagebox.showinfo("Başarılı", 
                                      f"{basarili} kitap başarıyla içe aktarıldı!\n{hatali} kayıt hatalı.")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya okunurken hata oluştu:\n{str(e)}")
                sonuc_text.insert(tk.END, f"\nHATA: {str(e)}\n")
        
        yukle_btn = tk.Button(dosya_frame, text="⬆️ Dosyayı Yükle ve İçe Aktar", 
                            font=("Arial", 12, "bold"), 
                            bg=self.renkler['success'], fg="white",
                            relief=tk.FLAT, padx=30, pady=15, cursor="hand2",
                            state=tk.DISABLED,
                            command=yukle)
        yukle_btn.pack(pady=(0, 20))

    def __del__(self):
        """Veritabanı bağlantısını kapatır"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = KutuphaneYonetimSistemi(root)
    root.mainloop()