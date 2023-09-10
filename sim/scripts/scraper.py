import json
import logging
import os
import time

from pathlib import Path

import click
import undetected_chromedriver as uc

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from utils import convert_step_to_stl


URL = "https://www.mcmaster.com/"
properties = {
    "Length": 'length', 
    "Thread Size": 'thread_size',
    "Thread Pitch": 'thread_pitch'
}

def create_browser(download_path: Path, delay):
    options = uc.ChromeOptions()

    prefs = {'download.default_directory' : str(download_path)}
    options.add_experimental_option('prefs', prefs)

    driver = uc.Chrome(
        options = options,
    )
    driver.implicitly_wait(delay)

    return driver

def download_STEP(driver):
    dropdown_wrapper = driver.find_element(By.CSS_SELECTOR, 'div.DownloadComponentIdentifier')
    dropdown_wrapper.find_element(By.TAG_NAME, 'button').click()
    dropdown = dropdown_wrapper.find_element(By.TAG_NAME, 'ul')
    options = dropdown.find_elements(By.TAG_NAME, 'li')
    for option in options:
        if option.get_attribute('innerText') == "3-D STEP":
            option.click()
            break

    download = driver.find_element(By.XPATH, "//div/a/button/span")
    download.click()

def convert_cad(download_folder_path: Path):
    to_convert = [file for file in os.listdir(download_folder_path) if file.endswith(".STEP")]
    for step_file in to_convert:
        file_name = step_file.split(".")[-2]
        convert_step_to_stl(download_folder_path / step_file, download_folder_path / f"{file_name}.STL")
        os.remove(download_folder_path / step_file)

def generate_label(driver, label_path: Path):
    table = driver.find_element(By.TAG_NAME, 'tbody')
    rows = table.find_elements(By.TAG_NAME, 'tr')
    label = {}

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        property = cols[0].get_attribute('innerText')
        value = cols[1].get_attribute('innerText')

        if property in properties:
            label[properties[property]] = value.replace(" ", "")

    logging.info(f"Creating label at: {label_path}")
    with open(label_path, "w") as outfile:
        json.dump(label, outfile)

def fetch_cads(output_path, url=URL, cads=[], delay=20):
    for cad in cads:
        mcmaster_id = cad["mcmaster_id"]
        category = cad["category"]
        download_folder_path = output_path / category

        driver = create_browser(download_folder_path, delay)
        driver.get(url + mcmaster_id)

        download_STEP(driver)
        generate_label(driver, output_path / category / f"{mcmaster_id}.json")

        time.sleep(1)
        convert_cad(download_folder_path)
        driver.close()
        driver.quit


@click.command(help="Scrape McMaster Carr for CAD models")
@click.option("--cads_json", "cads_json", default=None, help="Input json containing cad models to pull")
@click.option("--output_path", "output_path", required=True, help="Output folder to download cad models to")
def main(cads_json, output_path):
    logging.basicConfig(level=logging.INFO)
    cads_json_path = Path(cads_json)
    assert cads_json_path.exists(), f"{cads_json_path} does not exist"

    output_path = Path(output_path)
    assert output_path.exists(), f"{output_path} does not exist"
        
    with open(cads_json_path) as f:
        cads = json.load(f)

    fetch_cads(output_path, cads=cads)

if __name__ == "__main__":
    main()
