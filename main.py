import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import email
import time
import asyncio
from logger import send_msg_to_telegram, setup_logger
 
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
logger = setup_logger()  

async def check_new_emails(last_email_id,service, query):
    # query = 'is:unread'  # Фильтр для непрочитанных сообщений

    request_body = {
       'removeLabelIds': ['UNREAD'],  # Удаляем метку "непрочитанное"
    }

    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    if not messages:
        # print("Нет новых писем.")
        logger.info("Нет новых писем.")
    else:
        for message in messages:
            if message['id'] != last_email_id:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                print(f"Новое письмо: {msg['snippet']}")
                await send_msg_to_telegram(msg['snippet'])
                last_email_id = message['id']  # Обновляем ID последнего письма
       

                # Изменение меток письма
                response = service.users().messages().modify(userId='me', id=last_email_id, body=request_body).execute()

                print(f"Message with ID: {last_email_id} marked as read.")
            else:
                print("Новое письмо не найдено.")
    return last_email_id

async def main():
    try:
        last_email_id = None
        creds = None
        # Файл token.json хранит токены доступа, если они есть.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Если токенов нет, то проходим OAuth 2.0 авторизацию
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Сохраняем токен для будущего использования
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        # Создаем сервис для работы с Gmail API
        service = build('gmail', 'v1', credentials=creds)

        query = 'from:fawesomeblockchaingames@gmail.com OR from:fawesomegames11@gmail.com OR from:madkust2@gmail.com OR from:alexhrmessage@gmail.com is:unread' 

        while True:
            last_email_id = await check_new_emails(last_email_id, service,query)
            await asyncio.sleep(30) 
    except Exception as e:
        await send_msg_to_telegram(f'Произошла ошибка: {e}')
        logger.error(f"Произошла ошибка: {e}") 
        
if __name__ == '__main__':
    asyncio.run(main())
