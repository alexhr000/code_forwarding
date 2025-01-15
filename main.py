from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Настройка WebDriver
driver = webdriver.Chrome()  # или другой WebDriver
driver.get("https://mail.google.com")

# Вход в Gmail
email_input = driver.find_element(By.NAME, "identifier")
email_input.send_keys()  # Введите ваш email
email_input.send_keys(Keys.RETURN)

time.sleep(2)  # Ожидание загрузки страницы

password_input = driver.find_element(By.NAME, "password")
password_input.send_keys("your_password")  # Введите ваш пароль
password_input.send_keys(Keys.RETURN)

time.sleep(5)  # Ожидание загрузки почты

# Получение заголовков писем
emails = driver.find_elements(By.XPATH, "//h2[@class='zF']")  # Замените на актуальный XPATH
for email in emails:
    print(email.text)

# Закрытие браузера
driver.quit()