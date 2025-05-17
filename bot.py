import requests
import time
import random
import string
import json
import os
from faker import Faker
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

init()

fake = Faker()

GUERRILLA_API = "https://api.guerrillamail.com/ajax.php"
MAILTM_API = "https://api.mail.tm"

print(f"{Fore.CYAN}")
print("╔══════════════════════════════════════════════╗")
print("║       🌟 OpenDesci Auto-Register Bot         ║")
print("║   Automate your OpenDesci account tasks!     ║")
print("║   Developed by: https://t.me/sentineldiscus  ║")
print("╚══════════════════════════════════════════════╝")
print(f"{Style.RESET_ALL}")

def get_temp_email_guerrilla():
    params = {"f": "get_email_address"}
    response = requests.get(GUERRILLA_API, params=params)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal mengambil email dari Guerrilla Mail: Status {response.status_code}{Style.RESET_ALL}")
        return None, None
    data = response.json()
    return data["email_addr"], data["sid_token"]

def fetch_email_body_guerrilla(sid_token, mail_id):
    params = {
        "f": "fetch_email",
        "email_id": mail_id,
        "sid_token": sid_token
    }
    response = requests.get(GUERRILLA_API, params=params)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal mengambil body email dari Guerrilla Mail: Status {response.status_code}{Style.RESET_ALL}")
        return None
    data = response.json()
    return data.get("mail_body", "")

def check_inbox_guerrilla(sid_token):
    params = {
        "f": "check_email",
        "seq": 0,
        "sid_token": sid_token
    }
    response = requests.get(GUERRILLA_API, params=params)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal memeriksa inbox Guerrilla Mail: Status {response.status_code}{Style.RESET_ALL}")
        return None
    
    data = response.json()
    for email in data.get("list", []):
        subject = email.get("mail_subject", "").lower()
        if "verify" in subject or "opendesci" in subject:
            mail_id = email.get("mail_id")
            body = fetch_email_body_guerrilla(sid_token, mail_id)
            if not body:
                continue
            soup = BeautifulSoup(body, 'html.parser')
            text = soup.get_text().lower()
            digits = ''.join(filter(str.isdigit, text))
            for i in range(len(digits) - 5):
                potential_code = digits[i:i+6]
                if len(potential_code) == 6:
                    return potential_code
    return None

def get_temp_email_mailtm():
    response = requests.get(f"{MAILTM_API}/domains")
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal mengambil domain dari Mail.tm: Status {response.status_code}{Style.RESET_ALL}")
        return None, None
    domains = response.json().get("hydra:member", [])
    if not domains:
        print(f"{Fore.RED}Tidak ada domain tersedia di Mail.tm{Style.RESET_ALL}")
        return None, None
    domain = domains[0]["domain"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    email = f"{username}@{domain}"
    password = generate_random_password()
    payload = {"address": email, "password": password}
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{MAILTM_API}/accounts", json=payload, headers=headers)
    if response.status_code != 201:
        print(f"{Fore.RED}Gagal membuat akun di Mail.tm: Status {response.status_code}{Style.RESET_ALL}")
        return None, None
    response = requests.post(f"{MAILTM_API}/token", json=payload, headers=headers)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal mendapatkan token dari Mail.tm: Status {response.status_code}{Style.RESET_ALL}")
        return None, None
    token = response.json().get("token")
    return email, token

def fetch_email_body_mailtm(token, mail_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{MAILTM_API}/messages/{mail_id}", headers=headers)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal mengambil body email dari Mail.tm: Status {response.status_code}{Style.RESET_ALL}")
        return None
    data = response.json()
    return data.get("text", "") or data.get("html", "")

def check_inbox_mailtm(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{MAILTM_API}/messages", headers=headers)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal memeriksa inbox Mail.tm: Status {response.status_code}{Style.RESET_ALL}")
        return None
    data = response.json()
    for email in data.get("hydra:member", []):
        subject = email.get("subject", "").lower()
        if "verify" in subject or "opendesci" in subject:
            mail_id = email.get("id")
            body = fetch_email_body_mailtm(token, mail_id)
            if not body:
                continue
            soup = BeautifulSoup(body, 'html.parser')
            text = soup.get_text().lower()
            digits = ''.join(filter(str.isdigit, text))
            for i in range(len(digits) - 5):
                potential_code = digits[i:i+6]
                if len(potential_code) == 6:
                    return potential_code
    return None

def generate_random_password():
    password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    digits = ''.join(random.choices(string.digits, k=3))
    return password + digits

def censor_sensitive(text, visible_chars=3):
    if len(text) <= visible_chars:
        return text
    return text[:visible_chars] + "****"

def save_credentials(credentials):
    filename = "accounts.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    data.append(credentials)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def send_verification_request(email):
    url = "https://api.opendesci.org/v1/auth/email/send-verification"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": "Bearer null",
        "content-type": "application/json",
    }
    payload = {"email": email}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"{Fore.GREEN}Permintaan verifikasi email berhasil dikirim ke {email}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Gagal mengirim permintaan verifikasi: Status {response.status_code} - {response.text}{Style.RESET_ALL}")
    return response.status_code == 200

def verify_email(email, code):
    url = "https://api.opendesci.org/v1/auth/email/verify-email"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": "Bearer null",
        "content-type": "application/json",
    }
    payload = {"email": email, "code": code}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    print(f"{Fore.RED}Gagal memverifikasi email: Status {response.status_code} - {response.text}{Style.RESET_ALL}")
    return None

def register_account(email, token, referral_code):
    url = "https://api.opendesci.org/v1/auth/register"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    payload = {
        "email": email,
        "password": generate_random_password(),
        "name": fake.user_name(),
        "social_url": f"https://twitter.com/{fake.user_name()}",
        "referral_code_used": referral_code
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 200, payload

def main():
    try:
        referral_code = input("Masukkan kode referral: ").strip()
        if not referral_code:
            print(f"{Fore.RED}Kode referral tidak boleh kosong!{Style.RESET_ALL}")
            return
        while True:
            print("Pilih layanan email sementara:")
            print("1. Guerrilla Mail")
            print("2. Mail.tm")
            email_service = input().strip()
            if email_service in ["1", "2"]:
                break
            print(f"{Fore.YELLOW}Masukkan 1 atau 2!{Style.RESET_ALL}")
        while True:
            try:
                request_count = int(input("Masukkan jumlah reff diinginkan: "))
                if request_count >= 0:
                    break
                print(f"{Fore.YELLOW}Masukkan angka yang valid (0 atau lebih)!{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.YELLOW}Masukkan angka yang valid!{Style.RESET_ALL}")
        if request_count == 0:
            print(f"{Fore.YELLOW}Keluar dari program.{Style.RESET_ALL}")
            return
        for i in range(request_count):
            print(f"\n{Fore.YELLOW}Memulai pendaftaran ke-{i+1}/{request_count}{Style.RESET_ALL}")
            if email_service == "1":
                email, sid_token = get_temp_email_guerrilla()
                check_inbox_func = check_inbox_guerrilla
            else:
                email, sid_token = get_temp_email_mailtm()
                check_inbox_func = check_inbox_mailtm
            if not email or not sid_token:
                print(f"{Fore.RED}Gagal mendapatkan email sementara{Style.RESET_ALL}")
                continue
            print(f"{Fore.GREEN}Email dibuat: {email}{Style.RESET_ALL}")
            if not send_verification_request(email):
                continue
            max_attempts = 20
            for attempt in range(max_attempts):
                code = check_inbox_func(sid_token)
                if code:
                    print(f"{Fore.GREEN}Kode verifikasi ditemukan: {code}{Style.RESET_ALL}")
                    break
                time.sleep(10)
            else:
                print(f"{Fore.RED}Tidak menerima kode verifikasi setelah maksimum percobaan{Style.RESET_ALL}")
                continue
            token = verify_email(email, code)
            if not token:
                continue
            print(f"{Fore.GREEN}Email berhasil diverifikasi{Style.RESET_ALL}")
            success, credentials = register_account(email, token, referral_code)
            if success:
                save_credentials(credentials)
                censored_email = censor_sensitive(credentials["email"])
                censored_password = censor_sensitive(credentials["password"])
                print(f"{Fore.GREEN}Akun berhasil dibuat: Nama: {credentials['name']}, Email: {censored_email}, Password: {censored_password}, Social URL: {credentials['social_url']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Pendaftaran gagal{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Terjadi kesalahan: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
    
