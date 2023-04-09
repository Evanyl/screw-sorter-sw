import json
import os
from selenium import webdriver
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

#url = "https://www.mcmaster.com/products/screws/hex-drive-rounded-head-screws/18-8-stainless-steel-button-head-hex-drive-screws-9/"
url = "https://www.mcmaster.com/"
download_path = "/home/evanyl/ewa/school/screw-sorter-sw/sim/cads/"
properties = {
    "Length": 'length', 
    "Thread Size": 'thread_size',
    "Thread Pitch": 'thread_pitch'
}

def create_browser(id, delay):
    '''options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option("useAutomationExtension", False) '''

    options = uc.ChromeOptions()

    options.user_data_dir = "/home/evanyl"

    prefs = {'download.default_directory' : download_path + str(id)}
    options.add_experimental_option('prefs', prefs)
    #driver = webdriver.Chrome(ChromeDriverManager().install(), options=options) 
    #driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver = uc.Chrome(
        options = options,
        version_main = 111
    )
    driver.implicitly_wait(delay)

    return driver

def download_STEP(driver):
    #dropdown_wrapper = driver.find_element(By.CSS_SELECTOR, 'div.Dropdown_divDropdownWrapper__3tOMl')
    dropdown_wrapper = driver.find_element(By.CSS_SELECTOR, 'div.Dropdown_divDropdownWrapper__3h06Q')
    dropdown_wrapper.find_element(By.TAG_NAME, 'button').click()
    dropdown = dropdown_wrapper.find_element(By.TAG_NAME, 'ul')
    options = dropdown.find_elements(By.TAG_NAME, 'li')
    for option in options:
        if option.get_attribute('innerText') == "3-D STEP":
            option.click()
            break

    download = driver.find_element(By.XPATH, "//div/a/button/span")
    download.click()

def generate_label(driver, id, model):
    #driver.find_element(By.CSS_SELECTOR, 'a.SecondaryLnk').click()
    table = driver.find_element(By.TAG_NAME, 'tbody')
    rows = table.find_elements(By.TAG_NAME, 'tr')
    label = {}

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        property = cols[0].get_attribute('innerText')
        value = cols[1].get_attribute('innerText')

        if property in properties:
            label[properties[property]] = value.replace(" ", "")

    path = os.path.join(download_path, str(id), f"{model}.json")
    print(path)
    with open(path, "w") as outfile:
        json.dump(label, outfile)

def fetch_model(url, num_to_fetch=None, delay=20):
    count = 0
    while count < num_to_fetch:
        driver = create_browser(count, delay)
    
        driver.get(url)
        parts = driver.find_elements(By.CSS_SELECTOR, 'a.PartNbrLnk')
        part = parts[count]
        part.click()

        download_STEP(driver)
        generate_label(driver, count)

        driver.close()
        driver.quit
        count += 1

def fetch_models(url, models=[], delay=20):
    for model in models:
        driver = create_browser(model[1], delay)
    
        driver.get(url + model[0])
        #parts = driver.find_elements(By.CSS_SELECTOR, 'a.PartNbrLnk')
        #part = parts[count]
        #part.click()

        download_STEP(driver)
        generate_label(driver, model[1], model[0])

        
        time.sleep(1)
        driver.close()
        driver.quit



models_to_fetch = [
    #('92095A179', 'M3x0_5mm'),
    #('92949A327', 'I4x48'),
    #('92095A182', 'M3x0_5mm'),
    #('92949A328', 'I4x48'),
    #('92095A183', 'M3x0_5mm'),
    #('92949A329', 'I4x48'),
    #('92095A159', 'M3_5x0_6mm'),
    #('92095A161', 'M3_5x0_6mm'),
    #('92095A124', 'M3_5x0_6mm'),
    #('92949A337', 'I6x40'),
    ('92949A338', 'I6x40'),
    ('92949A419', 'I6x40'),
    ('92095A188', 'M4x0_7mm'),
    ('92095A192', 'M4x0_7mm'),
    ('92095A196', 'M4x0_7mm'),
    ('92949A424', 'I8x36'),
    ('92949A426', 'I8x36'),
    ('91255A837', 'I8x36'),
]

fetch_models(url, models=models_to_fetch)
