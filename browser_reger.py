import json
import time
import traceback
import requests
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import os
from random import choice, randint
import zipfile
import shutil
from datetime import datetime
import configparser
import pickle
from bs4 import BeautifulSoup
import telebot


os.makedirs('cookies', exist_ok=True)


def get_settings(key, value):
    config = configparser.ConfigParser()
    config.read('settings.ini', encoding='utf-8')
    return config.get(key, value)


bot = telebot.TeleBot(get_settings('SETTINGS', 'token'))


api_key_captcha = get_settings('SETTINGS', 'api_key_captcha')
api_key_sms_activate = get_settings('SETTINGS', 'api_key_sms_activate')


if not 'user_agents.json' in os.listdir():
    json.dump({}, open('user_agents.json', 'w', encoding='utf-8'))


if not 'words.txt' in os.listdir():
    open('words.txt', 'w', encoding='utf-8')


def get_user_agent():
    user_agents = []
    with open('user_agents.txt', 'r', encoding='utf-8') as file:
        for line in file.readlines():
            if line.strip():
                user_agents.append(line.strip())
    return choice(user_agents)


def get_address(type_='random'):
    address = []
    with open('address.txt', encoding='utf-8') as file:
        for line in file.readlines():
            if line.strip():
                address.append(line.strip())
    if type_ == 'random':
        return choice(address)
    else:
        return address


def get_proxy():
    response = requests.get(
        'https://goldproxy.net/ruip.txt'
    )
    login = 'irp3020620'
    password = 'osYyd4UlDJ'
    port = '7951'
    proxies = []
    for line in response.text.split('\n'):
        if line.strip() and len(line.strip().split('.')) == 4:
            proxies.append([login, password, port, line.strip()])
    return proxies[:-1]


proxies = get_proxy()


def get_word():
    words = []
    with open('words.txt', 'r', encoding='utf-8') as file:
        for line in file.readlines():
            if line.strip():
                words.append(line.strip())
    if len(words) == 0:
        return None
    return choice(words)


def get_word_from_txt():
    words = []
    with open('orders.txt', 'r', encoding='utf-8') as file:
        for line in file.readlines():
            if line.strip() and len(line.strip().split(':')) == 2:
                words.append([line.strip().split(':')[0], line.strip().split(':')[1]])
    if len(words) == 0:
        return None
    return choice(words)


def get_number():
    rent_type = get_settings('SETTINGS', 'rent_type')
    print(api_key_sms_activate)
    if rent_type == '1':
        url = 'https://api.sms-activate.org/stubs/handler_api.php'
        response = requests.get(
            url,
            params={
                'api_key': api_key_sms_activate,
                'service': 'uu',
                'country': 0,
                'action': 'getRentNumber',
                'rent_time': int(get_settings('SETTINGS', 'rent_time'))
            },
            timeout=20
        ).json()
        if 'status' in response and response['status'] == 'success':
            number_id = response['phone']['id']
            phone_number = response['phone']['number'][1:]
            return number_id, phone_number
    else:
        url = 'https://api.sms-activate.org/stubs/handler_api.php'
        response = requests.get(
            url,
            params={
                'api_key': api_key_sms_activate,
                'service': 'uu',
                'country': 0,
                'action': 'getNumber'
            },
            timeout=20
        ).text
        if 'ACCESS_NUMBER' in response:
            number_id = response.split(':')[1]
            phone_number = response.split(':')[2][1:]
            return number_id, phone_number
    return None, None


def cancel_number(number_id):
    rent_type = get_settings('SETTINGS', 'rent_type')
    if rent_type == '1':
        url = 'https://api.sms-activate.org/stubs/handler_api.php'
        response = requests.get(
            url,
            params={
                'api_key': api_key_sms_activate,
                'id': number_id,
                'status': '2',
                'action': 'setRentStatus'
            }
        )
        print(f'Отменил активацию номера: {response.text}')
    else:
        url = 'https://api.sms-activate.org/stubs/handler_api.php'
        response = requests.get(
            url,
            params={
                'api_key': api_key_sms_activate,
                'id': number_id,
                'status': '8',
                'action': 'setStatus'
            }
        )
        print(f'Отменил активацию номера: {response.text}')


def get_sms_code(number_id):
    rent_type = get_settings('SETTINGS', 'rent_type')
    if rent_type == '1':
        url = 'https://api.sms-activate.org/stubs/handler_api.php'
        for _ in range(10):
            time.sleep(10)
            try:
                response = requests.get(
                    url,
                    params={
                        'action': 'getRentStatus',
                        'id': number_id,
                        'api_key': api_key_sms_activate
                    },
                    timeout=10
                ).json()
                print(f'Ответ от СМС сервиса: {response}')
                if 'status' in response and response['status'] == 'success' and response['quantity'] > 0:
                    text = response['values']['0']['text']
                    for word in text.split():
                        if len(word.strip()) == 7 and word.strip().endswith('.'):
                            if len(word.strip().replace('.', '')) == 6 and word.strip().replace('.', '').isdigit():
                                return word.strip().replace('.', '')
            except:
                pass
    else:
        url = 'https://api.sms-activate.org/stubs/handler_api.php'
        for _ in range(10):
            time.sleep(10)
            try:
                response = requests.get(
                    url,
                    params={
                        'action': 'getStatus',
                        'id': number_id,
                        'api_key': api_key_sms_activate
                    },
                    timeout=10
                )
                print(f'Ответ от СМС сервиса: {response.text}')
                if response.text.startswith('STATUS_OK'):
                    return response.text.split(':')[1]
            except:
                pass
    return False


def get_balance_sms():
    url = 'https://api.sms-activate.org/stubs/handler_api.php'
    response = requests.get(
        url,
        params={
            'api_key': api_key_sms_activate,
            'action': 'getBalance'
        }
    )
    if 'ACCESS_BALANCE' in response.text:
        return response.text.split(':')[1]
    return None


def get_browser(profile_name, change_ip=True):
    if change_ip is True:
        try:
            print(requests.get(get_settings('SETTINGS', 'proxy_change_url'),
                               headers={
                                   'User-Agent': get_user_agent()
                               }).text)
        except Exception as error:
            print('Прокси:', error)
    PROXY_HOST = get_settings('SETTINGS', 'PROXY_HOST')
    PROXY_PORT = int(get_settings('SETTINGS', 'PROXY_PORT'))
    PROXY_USER = get_settings('SETTINGS', 'PROXY_USER')
    PROXY_PASS = get_settings('SETTINGS', 'PROXY_PASS')

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
            }
        };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

    options = webdriver.ChromeOptions()
    pluginfile = 'proxy_auth_plugin.zip'

    with zipfile.ZipFile(pluginfile, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    options.add_extension(pluginfile)
    data = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
    if not profile_name in data:
        user_agent = get_user_agent()
    else:
        user_agent = data[profile_name]
    options.add_argument('--allow-profiles-outside-user-dir')
    options.add_argument('--enable-profile-shortcut-manager')
    options.add_argument(rf'user-data-dir={os.getcwd()}\Users')
    options.add_argument(f'--profile-directory=Profile_{profile_name}')
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument('ignore-certificate-errors')
    options.add_argument('--enable-aggressive-domstorage-flushing')
    browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    browser.maximize_window()
    if not profile_name in data:
        return browser, user_agent
    else:
        return browser


def get_balance_captcha():
    url = 'http://rucaptcha.com/res.php'
    response = requests.get(
        url,
        params={
            'key': api_key_captcha,
            'action': 'getbalance',
            'json': 1
        }
    ).json()
    if 'request' in response:
        return response['request']
    return None


def get_captcha_code(request):
    url = 'http://rucaptcha.com/res.php'
    for _ in range(12):
        time.sleep(5)
        response = requests.get(
            url,
            params={
                'key': api_key_captcha,
                'action': 'get',
                'id': request,
                'json': 1
            },
            timeout=10
        )
        if response.json()['status'] == 1:
            return response.json()['request']
    return False


def send_captcha_image(image):
    url = 'http://rucaptcha.com/in.php'
    for _ in range(5):
        try:
            response = requests.post(
                url,
                data={
                    'key': api_key_captcha,
                    'method': 'base64',
                    'body': image,
                    'phrase': 0,
                    'regsense': 0,
                    'min_len': 5,
                    'max_len': 5,
                    'language': 2,
                    'json': 1
                },
                timeout=10
            )
            response = response.json()
            break
        except Exception as error:
            print(f'Ошибка при отправке капчи {error}')
    else:
        return False
    if response['status'] == 1:
        return get_captcha_code(response['request'])
    return False


def register_account(phone_number, number_id):
    browser, user_agent = get_browser(phone_number)
    browser.get('https://www.wildberries.ru/security/login')
    time.sleep(5)
    try:
        element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'input-item'))
        )
        element.send_keys(phone_number)
    except Exception as error:
        browser.quit()
        return [False, f'Ошибка при регистрации аккаунта: {traceback.format_exc()}']
    try:
        element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, 'requestCode'))
        )
        time.sleep(2)
        element.click()
    except Exception as error:
        browser.quit()
        return [False, f'Ошибка при регистрации аккаунта: {error}']
    try:
        time.sleep(5)
        element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'form-block__captcha-img'))
        )
        code = send_captcha_image(element.screenshot_as_base64)
    except Exception as error:
        browser.quit()
        return [False, f'Ошибка при регистрации аккаунта: {error}']
    if code is False:
        browser.quit()
        return [False, f'Не удалось разгадать капчу!']
    browser.find_element(By.ID, 'smsCaptchaCode').send_keys(code)
    sms_code = get_sms_code(number_id)
    if sms_code is False:
        browser.quit()
        return [False, 'Не пришел код с СМС.']
    for i in range(2):
        try:
            element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'j-b-charinput'))
            )
            element.send_keys(sms_code)
        except Exception as error:
            browser.quit()
            return [False, f'Ошибка при регистрации аккаунта: {error}']
        time.sleep(5)
        if browser.current_url == 'https://www.wildberries.ru/lk/basket':
            data = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
            data[phone_number] = user_agent
            json.dump(data, open('user_agents.json', 'w', encoding='utf-8'))
            try:
                browser.find_element(By.ID, 'searchInput').send_keys(get_word())
                browser.find_element(By.ID, 'applySearchBtn').click()
                time.sleep(3)
                break
            except:
                pass
        else:
            browser.refresh()
            time.sleep(5)
    else:
        browser.quit()
        return [False, 'Ошибка при регистрации аккаунта.']
    time.sleep(2)
    if get_settings('SETTINGS', 'add_pvz') != '1':
        pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
        browser.quit()
        return [True, 'Зарегистрировал аккаунт.', 'Выбор ПВЗ не требуется']
    try:
        browser.find_element(By.CLASS_NAME, 'simple-menu__link--address').click()
        time.sleep(10)
    except Exception as error:
        print(error)
        pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
        browser.quit()
        return [True, 'Зарегистрировал аккаунт.', 'Ошибка при выборе пункта выдачи']
    try:
        address = get_address()
        print(f'Выбрал адрес: {address}')
        browser.find_element(By.CLASS_NAME, 'ymaps-2-1-79-searchbox-input__input').send_keys(address)
        time.sleep(5)
    except Exception as error:
        print(error)
        pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
        browser.quit()
        return [True, 'Зарегистрировал аккаунт.', 'Ошибка при выборе пункта выдачи']
    try:
        browser.find_element(By.CLASS_NAME, 'ymaps-2-1-79-suggest-item').click()
        time.sleep(5)
    except Exception as error:
        print(error)
        pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
        browser.quit()
        return [True, 'Зарегистрировал аккаунт.', 'Ошибка при выборе пункта выдачи']
    try:
        browser.find_element(By.CLASS_NAME, 'ymaps-2-1-79-islets_serp-item').click()
        time.sleep(5)
    except Exception as error:
        pass
        #pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
        #browser.quit()
        #return [True, 'Зарегистрировал аккаунт.', 'Ошибка при выборе пункта выдачи']
    try:
        for name in browser.find_elements(By.CLASS_NAME, 'address-item__name'):
            if address.strip() == name.text.strip():
                name.click()
                name = name.text.strip()
                break
        else:
            pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
            browser.quit()
            return [True, 'Зарегистрировал аккаунт.', 'Не нашел адреса в списке адресов']
        time.sleep(5)
    except Exception as error:
        print(error)
        pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
        browser.quit()
        return [True, 'Зарегистрировал аккаунт.', 'Ошибка при выборе пункта выдачи']
    try:
        browser.find_element(By.CLASS_NAME, 'details-self__btn').click()
        time.sleep(5)
    except Exception as error:
        print(error)
        pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
        browser.quit()
        return [True, 'Зарегистрировал аккаунт.', 'Ошибка при выборе пункта выдачи']
    pickle.dump(browser.get_cookies(), open(f'cookies/cookies_{phone_number}.pkl', "wb"))
    if get_settings('SETTINGS', 'account_work') == '1':
        work_with_one_account(browser, int(get_settings('SETTINGS', 'account_step')))
    browser.quit()
    return [True, 'Зарегистрировал аккаунт.', f'Выбрал пункт: {name}']


def work_with_one_account(browser, words_count):
    for i in range(words_count):
        browser.get('https://www.wildberries.ru/lk')
        try:
            print(f'Обход {i + 1}')
            element = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.ID, 'searchInput'))
            )
            time.sleep(2)
            word = get_word()
            if word is None:
                print('Заполните файл words.txt ключевыми словами!')
                break
            element.send_keys(word)
            element = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.ID, 'applySearchBtn'))
            )
            element.click()
            try:
                element = WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'search-tags__list'))
                )
                elements = element.find_elements(By.CLASS_NAME, 'search-tags__item')
                choice(elements).click()
                elements = WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'j-card-item'))
                )
            except:
                pass
            for _ in range(10):
                browser.execute_script("arguments[0].scrollIntoView();",
                                       browser.find_elements(By.CLASS_NAME, 'j-card-item')[-1])
                if len(browser.find_elements(By.CLASS_NAME, 'j-card-item')) > 100:
                    break
                time.sleep(3)
            product = choice(browser.find_elements(By.CLASS_NAME, 'product-card__wrapper'))
            browser.execute_script("arguments[0].scrollIntoView();", product)
            browser.execute_script("window.scrollBy(0,-100)")
            time.sleep(1)
            href = product.find_element(By.CLASS_NAME, 'product-card__link').get_attribute('href')
            browser.get(href)
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'btn-main'))
            )
            browser.execute_script("window.scrollBy(0,1000)")
            try:
                WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'comments__btn-all'))
                )
                browser.get(browser.find_element(By.CLASS_NAME, 'comments__btn-all').get_attribute('href'))
                WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'feedback__text'))
                )
                for feedback in browser.find_elements(By.CLASS_NAME, 'feedback__text'):
                    browser.execute_script("arguments[0].scrollIntoView();", feedback)
                browser.execute_script("window.scrollBy(0,-1000)")
                browser.find_element(By.CLASS_NAME, 'btn-main').click()
            except:
                browser.execute_script("window.scrollBy(0,-1000)")
                browser.find_element(By.CLASS_NAME, 'product-page__aside-container').find_element(By.CLASS_NAME, 'btn-main').click()
            try:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'sizes-list__item'))
                )
                elements = browser.find_elements(By.CLASS_NAME, 'sizes-list__item')
                choice(elements).click()
                time.sleep(1)
            except Exception as error:
                print(f'Ошибка {error}')
            time.sleep(4)
        except Exception as error:
            print(traceback.format_exc())


def work_with_accounts(accounts, words_count):
    for account in accounts:
        browser = get_browser(account[0])
        browser.get('https://www.wildberries.ru/lk')
        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'lk-item__container'))
            )
        except Exception as error:
            print(f'Аккаунт {account} не авторизован!.')
            browser.quit()
            continue
        for i in range(words_count):
            try:
                print(f'Обход {i+1}')
                element = WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.ID, 'searchInput'))
                )
                time.sleep(2)
                word = get_word()
                if word is None:
                    print('Заполните файл words.txt ключевыми словами!')
                    browser.quit()
                    break
                element.send_keys(word)
                element = WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.ID, 'applySearchBtn'))
                )
                element.click()
                try:
                    element = WebDriverWait(browser, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'search-tags__list'))
                    )
                    elements = element.find_elements(By.CLASS_NAME, 'search-tags__item')
                    choice(elements).click()
                    elements = WebDriverWait(browser, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'j-card-item'))
                    )
                except:
                    pass
                for _ in range(10):
                    browser.execute_script("arguments[0].scrollIntoView();", browser.find_elements(By.CLASS_NAME, 'j-card-item')[-1])
                    if len(browser.find_elements(By.CLASS_NAME, 'j-card-item')) > 100:
                        break
                    time.sleep(3)
                product = choice(browser.find_elements(By.CLASS_NAME, 'product-card__wrapper'))
                browser.execute_script("arguments[0].scrollIntoView();", product)
                browser.execute_script("window.scrollBy(0,-100)")
                time.sleep(1)
                href = product.find_element(By.CLASS_NAME, 'product-card__link').get_attribute('href')
                browser.get(href)
                WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'btn-main'))
                )
                browser.execute_script("window.scrollBy(0,1000)")
                WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'comments__btn-all'))
                )
                browser.get(browser.find_element(By.CLASS_NAME, 'comments__btn-all').get_attribute('href'))
                WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'feedback__text'))
                )
                for feedback in browser.find_elements(By.CLASS_NAME, 'feedback__text'):
                    browser.execute_script("arguments[0].scrollIntoView();", feedback)
                browser.find_element(By.CLASS_NAME, 'btn-main').click()
                try:
                    WebDriverWait(browser, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'sizes-list__item'))
                    )
                    elements = browser.find_elements(By.CLASS_NAME, 'sizes-list__item')
                    choice(elements).click()
                    time.sleep(1)
                except Exception as error:
                    print(f'Ошибка {error}')
                time.sleep(4)
            except Exception as error:
                print(traceback.format_exc())
                print(f'Аккаунт {account} не найдено меню поиска.')
        browser.quit()


def send_notif(text, image=None):
    for user in [int(value.strip()) for value in get_settings('SETTINGS', 'users').split(',')]:
        if image is None:
            bot.send_message(
                user,
                text,
                parse_mode='html'
            )
        else:
            bot.send_photo(
                user,
                photo=open(image, 'rb'),
                caption=text,
                parse_mode='html'
            )


def get_delivery(profile_name, text):
    browser = get_browser(profile_name)
    browser.get('https://www.wildberries.ru/lk/myorders/delivery')
    time.sleep(5)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    for block in soup.find_all('div', {'class': 'delivery-block__content'}):
        address, code = None, None
        if block.find('p', {'class': 'delivery-address__info'}):
            address = block.find('p', {'class': 'delivery-address__info'}).text.strip()
        if block.find('span', {'class': 'delivery-code__value'}):
            code = block.find('span', {'class': 'delivery-code__value'}).text.strip().replace(' ', '')
        count_good, count = 0, 0
        for product in block.find_all('li', {'class': 'delivery-block__item'}):
            count += 1
            if product.find('span', {'class': 'product__tracking'}):
                if product.find('span', {'class': 'product__tracking'}).text.strip() == 'Готов к получению':
                    count_good += 1
        if address is not None and code is not None and count > 0:
            text += f'<code>{profile_name}</code> Код: <code>{code}</code>\n' \
                    f'Доставлено: {count_good} | В пути: {count}\n' \
                    f'<code>{address}</code>'
    browser.quit()
    return text


def get_reviews_with_browser(profile_name, text):
    browser = get_browser(profile_name)
    browser.get('https://www.wildberries.ru/lk/discussion/feedback?type=Comments')
    time.sleep(5)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    used_reviews = []
    for product in soup.find_all('a', {'class': 'feedback__img-wrap'}):
        used_reviews.append(
            product.get('href').split('/')[-2]
        )
    browser.get('https://www.wildberries.ru/lk/myorders/archive')
    time.sleep(5)
    text = f'<code>7{profile_name}</code> Артикулы:\n\n'
    soup = BeautifulSoup(browser.page_source, 'lxml')
    for product in soup.find_all('div', {'class': 'archive-item__content'}):
        if product.find('div', {'class': 'archive-item__img-wrap'}):
            if product.find('div', {'class': 'archive-item__img-wrap'}).get('data-popup-nm-id') in used_reviews:
                continue
            product_id = product.find('div', {'class': 'archive-item__img-wrap'}).get('data-popup-nm-id')
            if product.find('button', {'class': 'archive-item__btn'}):
                if product.find('button', {'class': 'archive-item__btn'}).text.strip() == 'Написать отзыв':
                    text += f"<code>{product_id}</code>\n"
    browser.quit()
    return text


def get_reviews(profile_name, text):
    cookies = {}
    for cookie in pickle.load(open(f"cookies/cookies_{profile_name}.pkl", "rb")):
        cookies[cookie['name']] = cookie['value']
    response = requests.post(
        'https://www.wildberries.ru/webapi/lk/myorders/archive/get',
        data={
            'limit': 150,
            'type': 'all',
            'status': '544'
        },
        cookies=cookies
    )
    print(response.json())
    return text


def get_money(profile_name, text):
    browser = get_browser(profile_name)
    browser.get('https://www.wildberries.ru/lk/mywallet/purchases')
    time.sleep(5)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    balance = None
    if soup.find('p', {'class': 'balance__quantity'}):
        balance = int(soup.find('p', {'class': 'balance__quantity'}).text.replace('₽', '').replace('\xa0', '').replace(' ', '').strip())
    if balance is None or balance == 0:
        print(f'{profile_name} Вывод денег | Ошибка. Баланс: {balance}')
        browser.quit()
        return text
    try:
        browser.find_element(By.CLASS_NAME, 'withdraw__btn').click()
        time.sleep(5)
    except Exception as error:
        print(f'{profile_name} Вывод денег | Не нашел кнопку "Вывести" на странице {error}')
        browser.quit()
        return text
    try:
        for method in browser.find_elements(By.CLASS_NAME, 'choosing-method__item'):
            if method.text == 'На карту':
                method.click()
                break
        else:
            raise ''
    except Exception as error:
        print(f'{profile_name} Вывод денег | Не нашел кнопку "Вывести" на странице {error}')
        browser.quit()
        return text
    try:
        browser.find_element(By.CLASS_NAME, 'val-msg').send_keys(str(balance))
        time.sleep(3)
    except Exception as error:
        print(f'{profile_name} Вывод денег | Не нашел поле ввода суммы на странице {error}')
        browser.quit()
        return text
    try:
        browser.find_element(By.CLASS_NAME, 'withdraw-funds__btn-main').click()
        time.sleep(5)
    except Exception as error:
        print(f'{profile_name} Вывод денег | Ошибка при клике по кнопке "Вывести" {error}')
        browser.quit()
        return text

    for _ in range(10):
        soup = BeautifulSoup(browser.page_source, 'lxml')
        if soup.find('h2', {'class': 'popup__header'}):
            if soup.find('h2', {'class': 'popup__header'}).text.strip() == 'Заявка создана':
                text = f'{profile_name} создал заявку на вывод: {balance} руб.'
                break
        time.sleep(1)
    browser.quit()
    return text


def get_buy(profile_name, text, word, article):
    browser = get_browser(profile_name)
    browser.get(f'https://www.wildberries.ru/catalog/0/search.aspx?search={word}')
    time.sleep(10)
    key = False
    for _ in range(10):
        browser.execute_script("arguments[0].scrollIntoView();",
                               browser.find_element(By.CLASS_NAME, 'product-card-list').find_elements(By.CLASS_NAME, 'product-card')[-1])
        time.sleep(3)
        for element in browser.find_element(By.CLASS_NAME, 'product-card-list').find_elements(By.CLASS_NAME, 'product-card'):
            if str(element.get_attribute('data-nm-id')) == str(article):
                browser.get(f'https://www.wildberries.ru/catalog/{article}/detail.aspx')
                key = True
                break
        if key:
            break
    else:
        browser.get(f'https://www.wildberries.ru/catalog/{article}/detail.aspx')
    time.sleep(5)
    try:
        browser.execute_script('arguments[0].click()', browser.find_element(By.CLASS_NAME, 'order__btn-buy'))
        time.sleep(5)
    except Exception as error:
        print(f'{profile_name} Выкуп товара | Ошибка при клике по кнопке "Купить сейчас" {error}')
        browser.quit()
        return text
    try:
        url = browser.current_url
        address = browser.find_element(By.CLASS_NAME, 'simple-menu__link--address').text.strip()
        if address not in get_address(type_='all'):
            browser.execute_script("arguments[0].scrollIntoView();", browser.find_element(By.CLASS_NAME, 'btn-edit'))
            browser.find_element(By.CLASS_NAME, 'btn-edit').click()
            time.sleep(5)
            browser.execute_script("arguments[0].scrollIntoView();", browser.find_element(By.CLASS_NAME, 'list-address__btn--link'))
            browser.find_element(By.CLASS_NAME, 'list-address__btn--link').click()
            time.sleep(10)
            try:
                address = get_address()
                print(f'Выбрал адрес: {address}')
                browser.find_element(By.CLASS_NAME, 'ymaps-2-1-79-searchbox-input__input').send_keys(address)
                time.sleep(5)
            except Exception as error:
                browser.quit()
                raise error
            try:
                browser.find_element(By.CLASS_NAME, 'ymaps-2-1-79-suggest-item').click()
                time.sleep(5)
            except Exception as error:
                browser.quit()
                raise error
            try:
                browser.find_element(By.CLASS_NAME, 'ymaps-2-1-79-islets_serp-item').click()
                time.sleep(5)
            except Exception as error:
                pass
            try:
                for name in browser.find_elements(By.CLASS_NAME, 'address-item__name'):
                    if address.strip() == name.text.strip():
                        name.click()
                        name = name.text.strip()
                        break
                else:
                    raise error
                time.sleep(5)
            except Exception as error:
                raise error
            try:
                browser.execute_script("arguments[0].scrollIntoView();", browser.find_element(By.CLASS_NAME, 'details-self__btn'))
                browser.find_element(By.CLASS_NAME, 'details-self__btn').click()
                time.sleep(5)
            except Exception as error:
                raise error
            browser.get(url)
            time.sleep(10)
        if browser.find_element(By.CLASS_NAME, 'pay__text').text.strip() != 'QR-код':
            browser.execute_script("arguments[0].scrollIntoView();", browser.find_element(By.CLASS_NAME, 'basket-pay__choose-pay'))
            time.sleep(1)
            browser.find_element(By.CLASS_NAME, 'basket-pay__choose-pay').click()
            time.sleep(5)
            for pay_method in browser.find_elements(By.CLASS_NAME, 'methods-pay__text'):
                if pay_method.text.strip() == 'QR-код':
                    pay_method.click()
                    break
            else:
                raise 'Не нашел кнопку QR-Код'
            time.sleep(5)
    except Exception as error:
        print(f'{profile_name} Выкуп товара | Ошибка при клике по кнопке "Выбрать способ оплаты" {error}')
    #try:
    #    browser.find_element(By.CLASS_NAME, 'popup__btn-main').click()
    #    time.sleep(5)
    #except Exception as error:
    #    print(f'{profile_name} Выкуп товара | Ошибка при клике по кнопке "Купить сейчас" {error}')
    #    browser.quit()
    #    return text
    try:
        browser.find_element(By.CLASS_NAME, 'basket-form__sidebar').find_element(By.CLASS_NAME, 'b-btn-do-order').click()
        time.sleep(10)
    except Exception as error:
        print(f'{profile_name} Выкуп товара | Ошибка при клике по кнопке "Оплатить заказ" {error}')
        browser.quit()
        return text
    try:
        sum_text = browser.find_element(By.CLASS_NAME, 'popup-qrc__sum').text.strip()
        text += sum_text
        browser.execute_script("window.scrollBy(0,-1000)")
        browser.save_screenshot('qr_code.png')
        browser.quit()
        return text
    except Exception as error:
        print(f'{profile_name} Выкуп товара | Ошибка при клике по кнопке "Оплатить заказ" {error}')
        browser.quit()
        return text


def main():
    a = input('Выберите режим работы:\n\n'
              '1 - зарегистрировать аккаунты\n'
              '2 - прогонять аккаунты по ключевым словам\n'
              '3 - открыть существующий аккаунт\n'
              '4 - получить артикулы в доставке\n'
              '5 - получить артикулы, на которые можно оставить отзыв\n'
              '6 - вывести деньги на карту\n'
              '7 - выкуп из txt файла\n'
              '99 - узнать баланс сервиса СМС и капчи\n'
              '\nОтвет: ')
    # Регистрация одного аккаунта
    #if a.strip() == '1':
    #    number_id, phone_number = get_number()
    #    if number_id is not None:
    #        print(f'Регистрирую аккаунт с номером {phone_number}...')
    #        try:
    #            result = register_account(phone_number, number_id)
    #        except Exception as error:
    #            result = [False, traceback.format_exc()]
    #        if result[0]:
    #            print(f'Успешно | {result[1]}. {phone_number} | {result[2]}')
    #        else:
    #            print(f'Ошибка | {result[1]}. {phone_number}')
    #            cancel_number(number_id)
    #            shutil.rmtree(f'Users/Profile_{phone_number}')
    if a.strip() == '1':
        account_count = input('Введите количество аккаунтов: ')
        for i in range(1, int(account_count)+1):
            number_id, phone_number = get_number()
            if number_id is not None:
                print(f'Регистрирую аккаунт {i} с номером {phone_number}...')
                try:
                    result = register_account(phone_number, number_id)
                except Exception as error:
                    result = [False, traceback.format_exc()]
                if result[0]:
                    print(f'Успешно {i} | {result[1]}. {phone_number}')
                else:
                    cancel_number(number_id)
                    print(f'Ошибка {i} | {result[1]}. {phone_number}')
                    shutil.rmtree(f'Users/Profile_{phone_number}')
    elif a.strip() == '3':
        accounts = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
        if not 'Users' in os.listdir():
            print('На данный момент нет зарегестрированных аккаунтов.')
            return 
        accounts_list_ = []
        for file in os.listdir('Users'):
            if file.startswith('Profile_') and file.split('_')[1] in accounts:
                accounts_list_.append([file.split('_')[1], os.path.getctime(f'Users/{file}')])
        accounts_list_ = sorted(accounts_list_, key=lambda x: x[1])
        index, accounts_list = 1, {}
        for account in accounts_list_:
            accounts_list[index] = account[0]
            print(index, account[0], datetime.utcfromtimestamp(int(account[1])).strftime('%Y-%m-%d %H:%M:%S'), sep=' * ')
            index += 1

        profile_number = input('Выберите профиль для открытия: ')
        if int(profile_number.strip()) in accounts_list:
            browser = get_browser(accounts_list[int(profile_number.strip())])
            browser.get('https://www.wildberries.ru/lk')
            input('По завершению работы с браузером нажмите Enter.')
            browser.quit()
        else:
            print(f'Аккаунта с номером {profile_number.strip()} нет в списке!')
    elif a.strip() == '99':
        print(f'Баланс сервиса СМС Активейт: {get_balance_sms()}')
        print(f'Баланс сервиса разгадки капчи: {get_balance_captcha()}')
    elif a.strip() == '2':
        a = int(input('Введите число обходов: '))
        accounts = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
        accounts_ = []
        for account in accounts:
            if f'Profile_{account}' in os.listdir('Users'):
                accounts_.append([account, accounts[account], int(os.path.getctime(f'Users/Profile_{account}'))])
        accounts_ = sorted(accounts_, key=lambda x: x[2])
        index = 1
        for account in accounts_:
            print(index, account[0], datetime.utcfromtimestamp(account[2]).strftime(
                '%Y-%m-%d %H:%M:%S'), sep=' * ')
            index += 1
        for_ = int(input('С какого аккаунта начать: '))
        to_ = int(input('До какого аккаунта (не включительно): '))
        accounts = accounts_[for_-1:to_-1]
        work_with_accounts(accounts, a)
    elif a.strip() == '4':
        accounts = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
        accounts_ = []
        for account in accounts:
            if f'Profile_{account}' in os.listdir('Users'):
                accounts_.append([account, int(os.path.getctime(f'Users/Profile_{account}'))])
        accounts_ = sorted(accounts_, key=lambda x: x[1])
        index = 1
        for account in accounts_:
            print(index, account[0], datetime.utcfromtimestamp(account[1]).strftime(
                '%Y-%m-%d %H:%M:%S'), sep=' * ')
            index += 1
        for_ = int(input('С какого аккаунта начать: '))
        to_ = int(input('До какого аккаунта (не включительно): '))
        accounts = accounts_[for_-1:to_-1]
        for account in accounts:
            text = get_delivery(account[0], '')
            if len(text) > 0:
                send_notif(text)
    elif a.strip() == '5':
        accounts = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
        accounts_ = []
        index = 1
        for account in accounts:
            if f'Profile_{account}' in os.listdir('Users'):
                accounts_.append([account, int(os.path.getctime(f'Users/Profile_{account}')), index])
                index += 1
        accounts_ = sorted(accounts_, key=lambda x: x[1])
        for account in accounts_:
            print(account[2], account[0], datetime.utcfromtimestamp(account[1]).strftime(
                '%Y-%m-%d %H:%M:%S'), sep=' * ')
        for_ = int(input('С какого аккаунта начать: '))
        to_ = int(input('До какого аккаунта (не включительно): '))
        accounts = accounts_[for_ - 1:to_ - 1]
        for account in accounts:
            text = get_reviews(account[0], '')
            if len(text) > 0:
                send_notif(str(account[2]) + ' * ' + text)
    elif a.strip() == '6':
        accounts = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
        accounts_ = []
        index = 1
        for account in accounts:
            if f'Profile_{account}' in os.listdir('Users'):
                accounts_.append([account, int(os.path.getctime(f'Users/Profile_{account}')), index])
                index += 1
        accounts_ = sorted(accounts_, key=lambda x: x[1])
        for account in accounts_:
            print(account[2], account[0], datetime.utcfromtimestamp(account[1]).strftime(
                '%Y-%m-%d %H:%M:%S'), sep=' * ')
        for_ = int(input('С какого аккаунта начать: '))
        to_ = int(input('До какого аккаунта (не включительно): '))
        accounts = accounts_[for_ - 1:to_ - 1]
        for account in accounts:
            text = get_money(account[0], '')
            if len(text) > 0:
                send_notif(str(account[2]) + ' * ' + text)
    elif a.strip() == '7':
        accounts = json.loads(open('user_agents.json', 'r', encoding='utf-8').read())
        accounts_ = []
        index = 1
        for account in accounts:
            if f'Profile_{account}' in os.listdir('Users'):
                accounts_.append([account, int(os.path.getctime(f'Users/Profile_{account}')), index])
                index += 1
        accounts_ = sorted(accounts_, key=lambda x: x[1])
        for account in accounts_:
            print(account[2], account[0], datetime.utcfromtimestamp(account[1]).strftime(
                '%Y-%m-%d %H:%M:%S'), sep=' * ')
        for_ = int(input('С какого аккаунта начать: '))
        to_ = int(input('До какого аккаунта (не включительно): '))
        accounts = accounts_[for_ - 1:to_ - 1]
        for account in accounts:
            word = get_word_from_txt()
            if word is None:
                print('Файл orders.txt пустой!')
                return
            print(f'Выбрал артикул {word[0]} и слово {word[1]}')
            text = get_buy(account[0], '', word[1], word[0])
            if len(text) > 0:
                send_notif(f'{account[2]} * {account[0]}\n{text}', 'qr_code.png')


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as error:
            print(f'Ошибка при работе скрипта: {traceback.format_exc()}')