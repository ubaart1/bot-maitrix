# MAITRIX Bot

Bot otomatis untuk operasi mint → swap → stake di testnet MAITRIX (Arbitrum Sepolia).

## Fitur

- Otomatis mint token ketika saldo rendah
- Swap token antar pasangan yang didukung
- Stake token di pool staking yang tersedia
- Cek saldo token
- Jalankan operasi individual atau siklus otomatis penuh
- Jalankan urutan transaksi spesifik seperti yang telah dilakukan sebelumnya

## Token yang Didukung

- ATH (aUTH)
- USDe (Ethena USD)
- LVLUSD (Level USD)
- VANA
- AUSD
- VUSD (Virtual USD)
- VANAUSD

## Prasyarat

- Python 3.8+
- pip (Python package manager)

## Instalasi

1. Clone repository:
   ```
   git clone https://github.com/yourusername/maitrix-bot.git
   cd maitrix-bot
   ```

2. Buat virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # atau
   venv\Scripts\activate  # Windows
   ```

3. Install dependensi:
   ```
   pip install -r requirements.txt
   ```

4. Konfigurasi private key:
   - Copy `.env.example` ke `.env`
   - Edit `.env` dan tambahkan private key Anda:
     ```
     PRIVATE_KEY=your_private_key_here
     ```
     Catatan: Private key harus tanpa awalan 0x

## Penggunaan

### Jalankan urutan transaksi MAITRIX

Ini akan menjalankan urutan transaksi spesifik seperti yang telah dilakukan sebelumnya:

```
python main.py maitrix
```

### Jalankan siklus otomatis penuh

Ini akan otomatis mint token ketika saldo rendah, swap token, dan stake token:

```
python main.py auto
```

### Cek saldo token

```
python main.py balance
```

### Mint token spesifik

```
python main.py mint ATH 10
```

### Swap token spesifik

```
python main.py swap ATH 5
```

### Stake token spesifik

```
python main.py stake AUSD 2
```

## Konfigurasi

Anda dapat mengkonfigurasi bot dengan mengedit file berikut:

- `.env`: Hanya berisi private key
- `config.py`: Alamat kontrak, ABI, RPC URL, gas settings, dan konfigurasi lainnya

## Keamanan

- Jangan pernah membagikan private key Anda
- Simpan private key Anda di file `.env`, yang diabaikan oleh git
- Gunakan wallet khusus untuk testing, bukan wallet utama Anda

## Contoh Penggunaan

1. Setup private key:
   ```
   echo "PRIVATE_KEY=your_private_key_here" > .env
   ```

2. Jalankan bot untuk melihat saldo:
   ```
   python main.py balance
   ```

3. Jalankan urutan transaksi MAITRIX:
   ```
   python main.py maitrix
   ```

## Lisensi

MIT

## Disclaimer

Bot ini hanya untuk tujuan pendidikan. Gunakan dengan risiko Anda sendiri. Penulis tidak bertanggung jawab atas kerugian yang timbul akibat penggunaan software ini.
