#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import Fore, Style, init
import time

# Inisialisasi colorama untuk warna pada terminal
init(autoreset=True)

# Fungsi untuk autocorrect URL
def autocorrect_url(user_input):
    if not user_input.startswith(('http://', 'https://')):
        print(Fore.YELLOW + "URL tidak dimulai dengan http:// atau https://. Menambahkan https:// secara otomatis.")
        return f"https://{user_input}"
    return user_input

# Fungsi untuk membersihkan nama file (mengganti spasi dengan tanda hubung)
def clean_filename(file_name):
    return file_name.replace(' ', '-')

# Fungsi untuk mendownload file dengan resume dan progress bar
def download_file(file_url, file_name):
    # Membersihkan nama file
    cleaned_file_name = clean_filename(file_name)
    file_path = os.path.join(download_dir, cleaned_file_name)
    
    # Cek apakah file sudah ada
    if os.path.exists(file_path):
        print(Fore.YELLOW + f"File {cleaned_file_name} sudah ada. Melewati pengunduhan.")
        return
    
    # Header untuk melanjutkan unduhan yang terputus
    headers = {}
    if os.path.exists(file_path):
        headers['Range'] = f'bytes={os.path.getsize(file_path)}-'
    
    try:
        response = requests.get(file_url, headers=headers, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"Gagal terhubung ke server: {e}")
        return
    
    total_size = int(response.headers.get('content-length', 0))
    mode = 'ab' if headers else 'wb'
    
    with open(file_path, mode) as file:
        with tqdm(total=total_size, unit='iB', unit_scale=True, desc=cleaned_file_name, initial=os.path.getsize(file_path)) as progress_bar:
            while True:
                try:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            progress_bar.update(len(chunk))
                    break
                except requests.exceptions.ConnectionError:
                    print(Fore.RED + "Koneksi terputus. Menunggu untuk mencoba kembali...")
                    time.sleep(5)
                    response = requests.get(file_url, headers={'Range': f'bytes={os.path.getsize(file_path)}-'}, stream=True)
                    continue
    
    if total_size != 0 and progress_bar.n != total_size:
        print(Fore.RED + "Error: Gagal mengunduh file secara lengkap.")
    else:
        print(Fore.GREEN + f"Berhasil mengunduh {cleaned_file_name}")

# Meminta pengguna untuk memasukkan URL
user_input = input(Fore.CYAN + "Masukkan URL indeks file: ").strip()
url = autocorrect_url(user_input)

# Direktori tempat menyimpan file yang diunduh
download_dir = 'downloaded_videos'
os.makedirs(download_dir, exist_ok=True)

# Mengambil konten HTML dari URL
try:
    response = requests.get(url)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(Fore.RED + f"Gagal mengambil halaman: {e}")
    exit()

soup = BeautifulSoup(response.text, 'html.parser')

# Mencari semua link yang mengarah ke file video
video_links = [link.get('href') for link in soup.find_all('a') if link.get('href') and link.get('href').endswith('.mp4')]

if not video_links:
    print(Fore.YELLOW + "Tidak ditemukan file video (.mp4) pada halaman ini.")
    exit()

print(Fore.BLUE + f"Menemukan {len(video_links)} file video.")

# Mengunduh setiap file video
for video_link in video_links:
    file_url = f"{url}/{video_link}" if not url.endswith('/') else f"{url}{video_link}"
    file_name = video_link.split('/')[-1]
    print(Fore.MAGENTA + f"Mengunduh {file_name}...")
    download_file(file_url, file_name)

print(Fore.GREEN + "Proses pengunduhan selesai.")
