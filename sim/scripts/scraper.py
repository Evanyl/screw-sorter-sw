import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

url = "https://www.mcmaster.com/products/screws/hex-drive-rounded-head-screws/18-8-stainless-steel-button-head-hex-drive-screws-9/"
download_path = "/Users/evliu/evan/eng/ENPH459/cads/"
properties = ["Length", "Thread Size"]

def create_browser(id, delay):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option("useAutomationExtension", False) 
    prefs = {'download.default_directory' : download_path + str(id)}
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(options=options) 
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.implicitly_wait(delay)

    return driver

def download_STEP(driver):
    dropdown_wrapper = driver.find_element(By.CSS_SELECTOR, 'div.Dropdown_divDropdownWrapper__3tOMl')
    dropdown_wrapper.find_element(By.TAG_NAME, 'button').click()
    dropdown = dropdown_wrapper.find_element(By.TAG_NAME, 'ul')
    options = dropdown.find_elements(By.TAG_NAME, 'li')
    for option in options:
        if option.get_attribute('innerText') == "3-D STEP":
            option.click()
            break

    download = driver.find_element(By.XPATH, "//div/a/button/span")
    download.click()

def generate_label(driver, id):
    driver.find_element(By.CSS_SELECTOR, 'a.SecondaryLnk').click()
    table = driver.find_element(By.TAG_NAME, 'tbody')
    rows = table.find_elements(By.TAG_NAME, 'tr')
    label = {}

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        property = cols[0].get_attribute('innerText')
        value = cols[1].get_attribute('innerText')

        if property in properties:
            label[property] = value

    with open(os.path.join(download_path, str(id), "label.json"), "w") as outfile:
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

fetch_model(url, num_to_fetch=10)
