from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

#https://stackoverflow.com/questions/60296873/sessionnotcreatedexception-message-session-not-created-this-version-of-chrome
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import requests
import json

import config


def login(domain):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    url = 'https://{}/auth/login?redirect=%2F'.format(domain)
    driver.get(url)

    window_before = driver.window_handles[0]

    driver.find_elements_by_xpath("//*[contains(text(), 'Sign in with Google')]")[0].click()

    window_after = driver.window_handles[1]
    driver.switch_to.window(window_after)

    driver.find_elements_by_class_name("whsOnd")[0].send_keys(config.email)
    driver.find_elements_by_class_name("VfPpkd-RLmnJb")[0].click()

    time.sleep(3)

    driver.find_elements_by_class_name("whsOnd")[0].send_keys(config.password)
    driver.find_elements_by_class_name("VfPpkd-RLmnJb")[0].click()

    driver.switch_to.window(window_before)

    timeout = 300
    element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sc-bwzfXH"))
    )

    return driver


def load_cookie():
    with open('token.txt') as f:
        token = json.load(f)
        if time.time() < token['expiry']:
            return token['value']
        else:
            print('Token has expired! Run MetabaseAuth.get_cookie() for new token!')
            return


def get_cookie(domain):
    driver = login(domain)

    token = {'value': '', 'expiry': ''}
    for cookie in driver.get_cookies():
        if cookie['name'] == 'metabase.SESSION':
            token['value'] = cookie['value']
            token['expiry'] = cookie['expiry']

            with open('token.txt', 'w') as f:
                json.dump(token, f)
    
    driver.close()

    return token['value']


def load_params(question_id):
    with open('params.txt') as f:
        params_dict = json.load(f)
        return params_dict[str(question_id)]


def get_params(domain, question_id):
    driver = login(domain)
    query_url = 'https://{}/question/{}'.format(domain, question_id)
    
    time.sleep(3)
    driver.get(query_url)

    while True:
        time.sleep(3)
        for request in driver.requests:
            if request.method == 'POST':
                try:
                    request_payload = request.body.decode('utf-8')
                    if 'parameters' in request_payload:
                        params = json.loads(request_payload)['parameters']
                        if len(params) != 0:
                            with open('params.txt', 'r', encoding='utf-8') as fr:
                                params_dict = json.load(fr)
                            with open('params.txt', 'w', encoding='utf-8') as fw:    
                                params_dict[question_id] = params
                                json.dump(params_dict, fw)

                            driver.close()
                            return params
                except Exception as e:
                    #print(e)
                    continue


def query(domain, token, question_id, params='[]', export=False):
    params = str(params).replace("'",'"')
    res = requests.post('https://{}/api/card/{}/query/json?parameters={}'.format(domain, question_id, params),
                        headers = {'Content-Type': 'application/json',
                                   'X-Metabase-Session': token
                                  }
                        )
    if export:
        pd.DataFrame(res.json()).to_csv('{}.csv'.format(question_id), index=False)

    return pd.DataFrame(res.json())


def params_formatting(params):
    return str(params).replace("'",'"')


