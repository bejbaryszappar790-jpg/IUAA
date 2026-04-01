import cv2
from pyzbar.pyzbar import decode
import requests
from datetime import timedelta, datetime

def extract_qr_link(image_path):
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not found or invalid path")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    detected_objects = decode(gray)

    if not detected_objects:
        return None

    return detected_objects[0].data.decode("utf-8")

def verify_certificate_link(url, allowed_domains=None):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return False, f"Bad status: {response.status_code}"

        if allowed_domains:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc

            if domain not in allowed_domains:
                return False, "Domain not trusted"

        return True, "Link is reachable and valid"

    except requests.exceptions.RequestException as e:
        return False, str(e)
    
def check_expiry(test_date_str, certificate_type="IELTS", date_format="%Y-%m-%d"):
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
        "expiry_date": expiry_date,
        "days_left": days_left
    }

def verify_certificate(file_path, test_date, cert_type):
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