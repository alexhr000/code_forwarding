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

import re

async def check_new_emails(last_email_id, service, query):
    request_body = {
       'removeLabelIds': ['UNREAD'],  # Удаляем метку "непрочитанное"
    }

    async def matchCode(storeName: str, code: str, message):
        await send_msg_to_telegram(f"🏄‍♂️ Код подтверждения <b>{storeName}</b>: {code}")
        last_email_id = message['id'] 

        # Изменение меток письма
        response = service.users().messages().modify(userId='me', id=last_email_id, body=request_body).execute()
        print(f"Message with ID: {last_email_id} marked as read.")

    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    if not messages:
        logger.info("Нет новых писем.")
    else:
        for message in messages:
            if message['id'] != last_email_id:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()

                # Получаем тело сообщения
                if 'data' in msg['payload']['body']:
                    message_body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
                else:
                    parts = msg['payload'].get('parts', [])
                    message_body = ""
                    for part in parts:
                        if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                            message_body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')


                # Ищем код подтверждения
                matchUnity = re.search(r"Verification code for your Unity ID is (\d+)", message_body)
                matchEpic = re.search(r"Your two-factor sign in code\s*(\d+)", message_body)
            
                if matchEpic is not None:
                    verification_code = matchEpic.group(1)
                    await matchCode('Epic Store', verification_code,message)
                if matchUnity is not None:
                    verification_code = matchUnity.group(1)
                    await matchCode('Unity', verification_code,message)


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
        # await check_new_emails(last_email_id, service,query)
    except Exception as e:
        await send_msg_to_telegram(f'Произошла ошибка: {e}')
        logger.error(f"Произошла ошибка: {e}") 
        
if __name__ == '__main__':
    asyncio.run(main())
