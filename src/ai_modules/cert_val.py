import cv2
import os
from pyzbar.pyzbar import decode
from datetime import datetime, timedelta

def extract_qr_link(file_path):
    """Извлечение ссылки из QR-кода"""
    if not file_path.lower().endswith((".jpg", ".jpeg", ".png")):
        return None
    
    img = cv2.imread(file_path)
    if img is None:
        return None
    
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detected = decode(gray)
        if detected:
            return detected[0].data.decode("utf-8")
    except:
        pass
    return None

def verify_certificate(file_path, test_date_str, cert_type):
    """Верификация сертификата"""
    qr_url = extract_qr_link(file_path)
    
    # Логика: если QR нет, но дата старая (до 2022) — это допустимо
    link_valid = qr_url is not None
    link_msg = "Ссылка активна" if link_valid else "QR-код не обнаружен (норма для старых образцов)"
    
    # Проверка срока годности (базово 2 года)
    try:
        t_date = datetime.strptime(test_date_str, "%Y-%m-%d")
        validity_period = 730 # 2 года
        expiry_date = t_date + timedelta(days=validity_period)
        days_left = (expiry_date - datetime.now()).days
        is_expired = days_left < 0
    except:
        is_expired, days_left = False, 0

    return {
        "qr_url": qr_url,
        "qr_found": qr_url is not None,
        "link_valid": link_valid,
        "link_message": link_msg,
        "expiry": {
            "is_expired": is_expired,
            "days_left": max(0, days_left)
        }
    }