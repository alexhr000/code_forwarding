from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException
import time
import requests  # Импортируем библиотеку для работы с HTTP-запросами

load_dotenv()

LOG = os.getenv("LOG")
PASSWORD = os.getenv("PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Настройка WebDriver
options = webdriver.ChromeOptions()
user_agent = UserAgent()
random_user_agent = user_agent.random

options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument(f"user-agent={random_user_agent}")
options.add_argument("--enable-logging")
options.add_argument("--disable-gpu") 
options.add_argument("--disable-software-rasterizer") 
options.add_argument("--no-user-data-dir")

driver = webdriver.Chrome(options=options)
driver.get("https://mail.google.com")

def send_to_telegram(user_name, subject, message):
    text = f"Новое сообщение от: {user_name}\nТема: {subject}\nСообщение: {message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'  # Опционально, чтобы использовать HTML-разметку
    }
    response = requests.post(url, json=payload)
    return response

def login():
    try:
        # Ввод логина
        email_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.NAME, "identifier"))
        )
        email_input.send_keys(LOG)
        email_input.send_keys(Keys.RETURN)

        # Проверка на наличие кнопки "Повторить попытку"
        try:
            repeat_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Повторить попытку']"))
            )
            repeat_button.click()
            print("Нажата кнопка 'Повторить попытку'")
            repeat_attempted = True  # Установить флаг, что кнопка нажата
        except TimeoutException:
            print("Кнопка 'Повторить попытку' не найдена")
            repeat_attempted = False  # Установить флаг, что кнопка не нажата

        # Проверка кнопки "Войти" только если "Повторить попытку" была нажата
        if repeat_attempted:
            try:
                sign_in_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Войти']"))
                )
                sign_in_button.click()
                print("Нажата кнопка 'Войти'")
            except TimeoutException:
                print("Кнопка 'Войти' не найдена")

        # Явное ожидание для поля пароля
        password_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.NAME, "Passwd"))
        )
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)

        time.sleep(5)
        noAccessPage = False
        # Ожидание кнопки "Не интересно" и клик по ней, если она доступна
        try:
            not_interested_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Не интересно']"))
            )
            not_interested_button.click()
            print("Нажата кнопка 'Не интересно'")
        except TimeoutException:
            noAccessPage = True
            print("Кнопка 'Не интересно' не найдена или недоступна")
        if noAccessPage:
            try:
                not_interested_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[text()='Открыть веб-версию']"))
                )
                not_interested_button.click()
                print("Нажата кнопка 'Открыть веб-версию'")
            except TimeoutException:
                print("Кнопка 'Открыть веб-версию' не найдена или недоступна")

        # Ожидание загрузки главной страницы Gmail
        # WebDriverWait(driver, 20).until(
        #     EC.visibility_of_element_located((By.XPATH, "//div[@role='list']"))
        # )

        # Запуск проверки новых сообщений
        check_new_messages()

    except TimeoutException as te:
        print("Время ожидания истекло:", te)
    except Exception as e:
        print(f"Произошла ошибка: {e}")

seen_messages = set()  # Глобальная переменная для хранения уже обработанных сообщений

def initialize_seen_messages():
    global seen_messages
    # Инициализация списка уже существующих сообщений
    try:
        list_container = driver.find_element(By.XPATH, "//div[@role='list']")
        list_items = list_container.find_elements(By.XPATH, "//div[@role='listitem']")
        for item in list_items:
            message_id = item.get_attribute("id")
            seen_messages.add(message_id)
    except Exception as e:
        print(f"Ошибка при инициализации сообщений: {e}")

def check_new_messages():
    global seen_messages  # Объявляем, что используем глобальную переменную
    while True:
        try:
            driver.refresh()  # Обновляем страницу
            time.sleep(5)  # Ждем 5 секунд для полной загрузки

            # Проверка новых сообщений
            list_container = driver.find_element(By.XPATH, "//div[@role='list']")
            if list_container:
                list_items = list_container.find_elements(By.XPATH, "//div[@role='listitem']")
                new_messages_found = False  # Флаг для отслеживания новых сообщений

                for item in list_items:
                    message_id = item.get_attribute("id")

                    # Пропускаем уже обработанные сообщения
                    if message_id in seen_messages:
                        continue
                    
                    # Добавляем сообщение в отслеживаемые
                    seen_messages.add(message_id)

                    # Извлечение данных из сообщения
                    try:
                        user_name = item.find_element(By.XPATH, ".//span[contains(@class, 'sender')]").text
                        subject = item.find_element(By.XPATH, ".//div[contains(@class, 'subject')]").text
                        message_body = item.find_element(By.XPATH, ".//div[contains(@class, 'message')]").text
                    except Exception as e:
                        user_name = "Неизвестный отправитель"
                        subject = "Без темы"
                        message_body = "Нет сообщения"

                    # Выводим информацию о новом сообщении
                    print(f"Отправитель: {user_name}, Тема: {subject}, Сообщение: {message_body}")
                    
                    # Отправка сообщения в Telegram
                    send_to_telegram(user_name, subject, message_body)
                    new_messages_found = True  # Устанавливаем флаг, что новые сообщения найдены

                if not new_messages_found:
                    print("Новых сообщений не найдено.")

            time.sleep(60)  # Ждем 60 секунд перед следующей проверкой

        except Exception as e:
            print(f"Произошла ошибка при проверке новых сообщений: {e}")
            time.sleep(60)  # Если произошла ошибка, ждем перед следующей попыткой

# Начало процесса входа
login()

# Инициализация уже существующих сообщений
initialize_seen_messages()

# Запуск проверки новых сообщений
check_new_messages()




        # <a class="WpHeLc VfPpkd-mRLv6 VfPpkd-RLmnJb" href="/restart?btmpl=mobile&amp;continue=https%3A%2F%2Fmail.google.com%2Fmail%2F%3Fview&amp;ddm=1&amp;dsh=S-952336870%3A1736774494457397&amp;emr=1&amp;flowEntry=ServiceLogin&amp;flowName=GlifWebSignIn&amp;ifkv=AVdkyDmJs-nOB7W_Z_iumy8EXJv487MBsm_6fUXMhBw-vUrrUAX1GjM7Z773hIOB3wm3E5-M9xL3VQ&amp;ltmpl=ecobh&amp;osid=1&amp;scc=1&amp;service=mail" aria-label="Повторить попытку" data-navigation="server" jsname="hSRGPd"></a>

        
        # <div class="acXkhd pNR6wf iBAHzf"></div>
        # <div class="acXkhd pNR6wf iBAHzf"></div>

        # <a class="button button--medium header__aside__button button--desktop button--tablet button--mobile" href="https://accounts.google.com/AccountChooser/signinchooser?service=mail&amp;continue=https://mail.google.com/mail/&amp;flowName=GlifWebSignIn&amp;flowEntry=AccountChooser&amp;ec=asw-gmail-globalnav-signin" aria-label="Войти в Gmail" data-g-event="gmail: global nav" data-g-action="sign in" data-g-label="https://accounts.google.com/AccountChooser/signinchooser?service=mail&amp;continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&amp;flowName=GlifWebSignIn&amp;flowEntry=AccountChooser&amp;ec=asw-gmail-globalnav-signin">
        #         <span class="button__label">Войти</span>
        # </a>

        # <a class="button button--medium header__aside__button button--desktop button--tablet button--mobile" href="https://accounts.google.com/AccountChooser/signinchooser?service=mail&amp;continue=https://mail.google.com/mail/&amp;flowName=GlifWebSignIn&amp;flowEntry=AccountChooser&amp;ec=asw-gmail-globalnav-signin" aria-label="Войти в Gmail" data-g-event="gmail: global nav" data-g-action="sign in" data-g-label="https://accounts.google.com/AccountChooser/signinchooser?service=mail&amp;continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&amp;flowName=GlifWebSignIn&amp;flowEntry=AccountChooser&amp;ec=asw-gmail-globalnav-signin">
        #         <span class="button__label">Войти</span>
        # </a>

        # <a data-onclick="xpag-decline+240">Открыть веб-версию</a>
        # <button data-onclick="np-d-cta+230" class="sx9SGc">Не интересно</button>


        # 1. если нажата кнопка 'Не интересно', должен начинать выполняться блок кнопка 'Не интересно' не найдена или недоступна






                # message_id = item.get_attribute("data-id")  # Получаем уникальный идентификатор сообщения
                # if message_id not in seen_messages:
                #     seen_messages.add(message_id)  # Добавляем идентификатор в множество
                    
                #     # Извлечение информации с проверкой на None
                #     user_name = item.find_element(By.XPATH, ".//span[@id='ti_f_" + message_id + "']/b")
                #     print(f"user_name - {user_name}")
                #     subject = item.find_element(By.XPATH, ".//div[@id='ti_s_" + message_id + "']/span")
                #     print(f"subject - {subject}")
                #     message = item.find_element(By.XPATH, ".//div[@id='ti_b_" + message_id + "']")
                #     print(f"message - {message}")
                    
                #     user_name_text = user_name.text if user_name else "Неизвестный отправитель"
                #     subject_text = subject.text if subject else "Без темы"
                #     message_text = message.text if message else "Нет сообщения"
                    
                #     print(f"Отправитель: {user_name_text}, Тема: {subject_text}, Сообщение: {message_text}")