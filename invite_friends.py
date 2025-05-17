import asyncio
import aiohttp
from faker import Faker
import time
import logging
from typing import List
import names
import os
from banner.banner import print_banner
from termcolor import colored

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            record.msg = colored(record.msg, 'green')
        elif record.levelno == logging.WARNING:
            record.msg = colored(record.msg, 'yellow')
        elif record.levelno == logging.ERROR:
            record.msg = colored(record.msg, 'red')
        return super().format(record)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.handlers = [handler]

URL = "https://api.opendesci.org/v1/referrals/"
BATCH_SIZE = 10
DELAY_SECONDS = 60
TIMEOUT = 10

def get_auth_token():
    try:
        with open('data.txt', 'r') as file:
            token = file.read().strip()
            return f"Bearer {token}"
    except FileNotFoundError:
        logger.error("ファイル 'data.txt' が見つかりません！")
        exit(1)
    except Exception as e:
        logger.error(f"トークンの読み込みに失敗しました: {str(e)}")
        exit(1)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": get_auth_token(),
    "content-type": "application/json",
    "origin": "https://app.opendesci.org",
    "referer": "https://app.opendesci.org/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
}

fake = Faker()

async def generate_random_email():
    name = names.get_first_name().lower()
    return f"{name}{fake.random_int(min=100, max=999)}@gmail.com"

async def send_request(session, email):
    payload = {"emails": [email]}
    try:
        async with session.post(URL, json=payload, headers=HEADERS, timeout=TIMEOUT) as response:
            if response.status == 200:
                logger.info(f"メール {email} のリクエストが成功しました！")
                return True
            else:
                logger.error(f"メール {email} のリクエストが失敗しました、ステータス: {response.status}")
                return False
    except Exception as e:
        logger.error(f"メール {email} のリクエスト中にエラー: {str(e)}")
        return False

async def send_batch_requests():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(BATCH_SIZE):
            email = await generate_random_email()
            tasks.append(send_request(session, email))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        return success_count

async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    print("\n" * 5)
    batch_count = 0
    while True:
        batch_count += 1
        os.system('cls' if os.name == 'nt' else 'clear')
        print_banner()
        print("\n" * 5)
        logger.info(f"バッチ {batch_count} を開始します")
        start_time = time.time()
        success_count = await send_batch_requests()
        elapsed_time = time.time() - start_time
        logger.info(f"バッチ {batch_count} 完了: {success_count}/{BATCH_SIZE} 成功、時間: {elapsed_time:.2f} 秒")
        logger.info(f"次のバッチまで {DELAY_SECONDS} 秒待機中...")
        await asyncio.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("プログラムがユーザーによって終了されました")
