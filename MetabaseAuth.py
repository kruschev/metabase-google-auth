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


def get_cookie(domain):
    driver = login(domain)

    token = ''
    for cookie in driver.get_cookies():
        if cookie['name'] == 'metabase.SESSION':
            token = cookie['value']
    
    driver.close()

    return token


def get_params(domain, question_id):
    driver = login(domain)
    query_url = 'https://{}/question/{}'.format(domain, question_id)

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
                            driver.close()
                            return params
                except:
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