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

print(f"{Fore.CYAN}")
print("╔══════════════════════════════════════════════╗")
print("║       🌟 OpenDesci Auto-Register Bot         ║")
print("║   Automate your OpenDesci account tasks!     ║")
print("║   Developed by: https://t.me/sentineldiscus  ║")
print("╚══════════════════════════════════════════════╝")
print(f"{Style.RESET_ALL}")

def get_temp_email():
    """Get a temporary email address from Guerrilla Mail"""
    params = {"f": "get_email_address"}
    response = requests.get(GUERRILLA_API, params=params)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal mengambil email: Status {response.status_code}{Style.RESET_ALL}")
        return None, None
    data = response.json()
    return data["email_addr"], data["sid_token"]

def fetch_email_body(sid_token, mail_id):
    """Fetch email body using mail_id"""
    params = {
        "f": "fetch_email",
        "email_id": mail_id,
        "sid_token": sid_token
    }
    response = requests.get(GUERRILLA_API, params=params)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal mengambil body email: Status {response.status_code}{Style.RESET_ALL}")
        return None
    data = response.json()
    return data.get("mail_body", "")

def check_inbox(sid_token):
    """Check inbox for verification code by parsing HTML"""
    params = {
        "f": "check_email",
        "seq": 0,
        "sid_token": sid_token
    }
    response = requests.get(GUERRILLA_API, params=params)
    if response.status_code != 200:
        print(f"{Fore.RED}Gagal memeriksa inbox: Status {response.status_code}{Style.RESET_ALL}")
        return None
    
    data = response.json()
    for email in data.get("list", []):
        subject = email.get("mail_subject", "").lower()
        if "verify" in subject or "opendesci" in subject:
            mail_id = email.get("mail_id")
            body = fetch_email_body(sid_token, mail_id)
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
    """Generate random password using faker plus 3 random digits"""
    password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    digits = ''.join(random.choices(string.digits, k=3))
    return password + digits

def censor_sensitive(text, visible_chars=3):
    """Censor sensitive information, showing only first few characters"""
    if len(text) <= visible_chars:
        return text
    return text[:visible_chars] + "****"

def save_credentials(credentials):
    """Save credentials to accounts.json"""
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
    """Send verification email request"""
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
    """Verify email with code"""
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
    """Register new account"""
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
            try:
                request_count = int(input("Masukkan jumlah reff diinginkan : "))
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
            
            email, sid_token = get_temp_email()
            if not email or not sid_token:
                print(f"{Fore.RED}Gagal mendapatkan email sementara dari Guerrilla Mail{Style.RESET_ALL}")
                continue
            print(f"{Fore.GREEN}Email dibuat: {email}{Style.RESET_ALL}")

            if not send_verification_request(email):
                continue

            max_attempts = 20
            for attempt in range(max_attempts):
                code = check_inbox(sid_token)
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
