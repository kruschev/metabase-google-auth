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

import os, inspect
path = os.path.dirname(inspect.getfile(config))

def login(domain):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    url = 'https://{}'.format(domain)
    driver.get(url)

    window_before = driver.window_handles[0]

    time.sleep(3)
    driver.find_elements_by_xpath("//*[contains(text(), 'Sign in with Google')]")[0].click()

    window_after = driver.window_handles[1]
    driver.switch_to.window(window_after)

    driver.find_elements_by_class_name("whsOnd")[0].send_keys(config.email)
    driver.find_elements_by_class_name("VfPpkd-RLmnJb")[0].click()

    time.sleep(3)

    driver.find_elements_by_class_name("whsOnd")[0].send_keys(config.password)
    driver.find_elements_by_class_name("VfPpkd-RLmnJb")[0].click()

    driver.switch_to.window(window_before)
    
    current_url = driver.current_url
    timeout = 300
    element = WebDriverWait(driver, timeout).until(
                    EC.url_changes(current_url))

    return driver


def load_cookie():
    path_token = path + '\\token.txt'
    try:
        with open(path_token) as f:
            token = json.load(f)
            if time.time() < token['expiry']:
                return token['value']
            else:
                print('Token has expired! Run MetabaseAuth.get_cookie() for new token!')
                return
    except:
        print('token.txt does not exist or is empty')
        return


def get_cookie(domain):
    driver = login(domain)

    token = {'value': '', 'expiry': ''}
    for cookie in driver.get_cookies():
        print(cookie)
        if cookie['name'] == 'metabase.SESSION':
            token['value'] = cookie['value']
            token['expiry'] = cookie['expiry']
            
            path_token = path + '\\token.txt'
            with open(path_token, 'w') as f:
                json.dump(token, f)
    
    driver.close()

    return token['value']


def load_params(question_id):
    path_params = path + '\\params.txt'
    try:
        with open(path_params) as f:
            params_dict = json.load(f)
            return params_dict[str(question_id)]
    except:
        print('params.txt does not exist or does not contain question {}'.format(question_id))
        return

def get_params(domain, cookie, question_id):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    url = 'https://{}'.format(domain)
    driver.get(url)

    driver.add_cookie({'name': 'metabase.SESSION', 'value': cookie, 'domain': domain})
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
                            path_params = path + '\\params.txt'
                            with open(path_params, 'r', encoding='utf-8') as fr:
                                params_dict = json.load(fr)
                            with open(path_params, 'w', encoding='utf-8') as fw:    
                                params_dict[question_id] = params
                                json.dump(params_dict, fw)

                            driver.close()
                            return params
                except Exception as e:
                    #print(e)
                    continue


def params_formatting(params):
    return str(params).replace("'",'"')


def get_colnames(domain, cookie, question_id):
    cols = requests.get('https://{}/api/card/{}'.format(domain, question_id),
                        headers = {'Content-Type': 'application/json',
                                   'X-Metabase-Session': cookie
                                   }
                        )
    return [col['name'] for col in cols.json()['result_metadata']]
    

def query(domain, cookie, question_id, params='[]', ignore_cache=False, export=False):
    #ignore_cache = str(ignore_cache).lower()
    params = str(params).replace("'",'"')
    res = requests.post('https://{}/api/card/{}/query/json?ignore_cache={}&parameters={}'.format(domain, question_id, ignore_cache, params),
                        headers = {'Content-Type': 'application/json',
                                   'X-Metabase-Session': cookie
                                   }
                        )
    
    df = pd.DataFrame(res.json())
    
    if export:
        df.to_csv('{}.csv'.format(question_id), index=False)

    return df