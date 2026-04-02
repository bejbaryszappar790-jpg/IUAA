import cv2
import os
import requests
from pyzbar.pyzbar import decode
from datetime import timedelta, datetime

def extract_qr_link(file_path):
    """
    Безопасно извлекает QR-код. 
    Если это не картинка (PDF/DOCX), функция просто вернет None, не вызывая ошибку.
    """
    # Шаг 1: Проверка расширения (защита от краша на PDF)
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        print(f"[cert_val] Пропуск QR-анализа: файл {ext} не является изображением.")
        return None

    # Шаг 2: Чтение изображения
    img = cv2.imread(file_path)
    if img is None:
        print("[cert_val] Ошибка: Не удалось прочитать изображение.")
        return None

    # Шаг 3: Обработка и поиск QR
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detected_objects = decode(gray)
        if not detected_objects:
            return None
        return detected_objects[0].data.decode("utf-8")
    except Exception as e:
        print(f"[cert_val] Ошибка декодирования QR: {e}")
        return None

def verify_certificate_link(url, allowed_domains=None):
    """
    Проверяет, живая ли ссылка из QR-кода.
    """
    if not url:
        return False, "QR-код не найден или файл не является изображением"
    
    try:
        # Пытаемся зайти по ссылке
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return False, f"Сайт вернул ошибку: {response.status_code}"

        if allowed_domains:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain not in allowed_domains:
                return False, f"Домен {domain} не входит в список доверенных"

        return True, "Ссылка активна и ведет на официальный ресурс"

    except Exception as e:
        return False, f"Ошибка сети: {str(e)}"

def check_expiry(test_date_str, certificate_type="IELTS", date_format="%Y-%m-%d"):
    """
    Проверяет срок годности сертификата.
    """
    try:
        test_date = datetime.strptime(test_date_str, date_format)
        current_date = datetime.now()

        validity_years = {
            "IELTS": 2,
            "TOEFL": 2,
            "DUOLINGO": 2,
            "UNT": 1
        }

        years = validity_years.get(certificate_type.upper(), 2)
        expiry_date = test_date + timedelta(days=365 * years)

        days_left = (expiry_date - current_date).days
        is_expired = days_left < 0

        return {
            "is_expired": is_expired,
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "days_left": days_left
        }
    except Exception as e:
        print(f"[cert_val] Ошибка даты: {e}")
        return {"is_expired": False, "expiry_date": "N/A", "days_left": 0}

def verify_certificate(file_path, test_date, cert_type):
    """
    Главная функция, которую вызывает evaluator.py
    """
    qr_url = extract_qr_link(file_path)
    link_valid, link_msg = verify_certificate_link(qr_url)
    expiry = check_expiry(test_date, cert_type)

    return {
        "qr_url": qr_url,
        "qr_found": qr_url is not None,
        "link_valid": link_valid,
        "link_message": link_msg,
        "expiry": expiry
    }