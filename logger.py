import logging
import asyncio
from aiogram import Bot
from aiogram.utils import executor
from config import CHAT_ID, API_TOKEN 

# Функция настройки логгера
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)  
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) 
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    telegram_handler = TelegramHandler()
    telegram_handler.setLevel(logging.ERROR)
    telegram_handler.setFormatter(formatter)
    logger.addHandler(telegram_handler)
    
    return logger

bot = Bot(token=API_TOKEN)

async def send_msg_to_telegram(error_message: str):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=f"{error_message}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

class TelegramHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        # asyncio.run_coroutine_threadsafe(send_msg_to_telegram(log_entry), asyncio.get_event_loop())

async def main():
    logger = setup_logger()  

    try:
        1 / 0  
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}") 
        await send_msg_to_telegram(f'Произошла ошибка: {e}')

if __name__ == "__main__":
    asyncio.run(main())
