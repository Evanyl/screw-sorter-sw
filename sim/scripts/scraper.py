import json
import getpass
import logging
import os
import shutil
import time

from pathlib import Path

import click
import undetected_chromedriver as uc

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from utils import convert_step_to_stl, McmasterSearcher, URL
from typing import Optional

gauge_to_inch = {
    '1': '1/16"',
    '2': '5/64"',
    '3': '3/32"',
    '4': '7/64"',
    '5': '1/8"',
    '6': '9/64"',
    '8': '5/32"',
    '9': '11/64"',
    '10': '3/16"',
    '11': '13/64"',
    '12': '7/32"',
    '13': '15/64"',
    '14': '1/4"',
    '16': '17/64"',
    '18': '19/64"',
    '20': '5/16"',
    '24': '3/8"',
}


properties = {
    "Length": 'length', 
    "Thread Size": 'thread_size',
    "Thread Pitch": 'pitch',
    "_diameter": "diameter",
    "System of Measurement": "system_of_measurement",
    "Head Type": "head",
    "Drive Style": "drive",
    "Head Diameter": "head_diameter",
    "Material": "finish",
    "Thread Direction": "direction",
}

def create_browser(delay: int, version_main: Optional[int] = None, download_folder_path: Optional[Path] = None):
    backoff_times = [2, 4, 8, 16, 32]
    driver = None
    logging.getLogger().setLevel(logging.WARNING)
    for backoff_time in backoff_times:
        try:
            options = uc.ChromeOptions()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')

            if download_folder_path is not None:
                prefs = {'download.default_directory' : str(download_folder_path)}
                options.add_experimental_option('prefs', prefs)

            if version_main:
                driver = uc.Chrome(
                    version_main = version_main,
                    options = options,
                )
            else:
                driver = uc.Chrome(
                    options = options,
                )
            driver.implicitly_wait(delay)
            break
        except Exception as e:
            logging.error(e)
            time.sleep(backoff_time)

    logging.getLogger().setLevel(logging.INFO)
    assert driver, "Failed to open browser"
    return driver

def click_element(driver, element):
    """ 
        Selenium won't click an element if it's not in view, so we want
        to scroll
    """
    driver.execute_script("arguments[0].scrollIntoView();", element)
    element.click()

def download_STEP(driver):
    dropdown_wrapper = driver.find_element(By.CSS_SELECTOR, 'div.DownloadComponentIdentifier')
    dropdown_list = dropdown_wrapper.find_element(By.TAG_NAME, 'button')
    click_element(driver, dropdown_list)
    dropdown = dropdown_wrapper.find_element(By.TAG_NAME, 'ul')
    options = dropdown.find_elements(By.TAG_NAME, 'li')
    for option in options:
        if option.get_attribute('innerText') == "3-D STEP":
            click_element(driver, option)
            break

    download = driver.find_element(By.XPATH, "//div/a/button/span")
    click_element(driver, download)

def convert_cad(download_folder_path: Path, mcmaster_id: str):
    """ 
        This functionality is actually a little jank. Selenium doesn't provide a nice way to 
        get back the downloaded file, so it's hard to determine which file in the folder is the one we want.
        We just assume the folder only contains the one STEP file we want. It'll then convert and delete, 
        to be ready for the next download. So the idea is you run this after every singular download
    """
    to_convert = [file for file in os.listdir(download_folder_path) if file.endswith(".STEP")]
    assert len(to_convert) == 1, "Found multiple STEP files in folder, read function doc for why this is wack"
    for step_file in to_convert:
        file_name = step_file.split(".")[-2]
        # Skip already completed
        stl_file = download_folder_path / f"{mcmaster_id}.stl"
        if stl_file.exists(): continue

        convert_step_to_stl(download_folder_path / step_file, stl_file)
        os.remove(download_folder_path / step_file)

def generate_label(driver, label_path: Path):
    table = driver.find_element(By.TAG_NAME, 'tbody')
    rows = table.find_elements(By.TAG_NAME, 'tr')
    label = {}

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        property = cols[0].get_attribute('innerText')
        value = cols[1].get_attribute('innerText').replace(" ", "")

        if property in properties:
            label[properties[property]] = value
        elif property == "Diameter " or property == "Diameter":
            label["head_diameter"] = value

    # Correct thread_pitch for imperial
    if label["system_of_measurement"] == "Metric":
        label["diameter"] = label["thread_size"].replace("M", "")
    else:
        imperial_thread = label["thread_size"].split("-")

        label["diameter"] = gauge_to_inch[imperial_thread[0]]

        threads_per_inch = imperial_thread[1]
        label["thread_pitch"] = f"1/{threads_per_inch}\""

    #logging.info(f"Creating label at: {label_path}")
    if len(label) != len(properties):
        logging.warning(f"Label at: {label_path} does not have all properties...")
    with open(label_path, "w") as f:
        json.dump(label, f)

def login(driver, auth):
    email_field = driver.find_element(By.ID, "Email")
    password_field = driver.find_element(By.ID, "Password")
    email_field.send_keys(auth[0])
    password_field.send_keys(auth[1])
    submit_login = driver.find_element(By.XPATH, "//input[@value='Log in']")
    click_element(driver, submit_login)
    time.sleep(1)
    driver.refresh()

def fetch_cads(output_path, url, version_main=None, cads=[], delay=20, auth=None):
    failed = []
    for i, cad in enumerate(cads):
        logging.info(f"Downloading {i}/{len(cads)}")
        driver = None
        try:
            mcmaster_id = cad
            download_folder_path = output_path / mcmaster_id
            if download_folder_path.exists():
                shutil.rmtree(download_folder_path)
            driver = create_browser(delay, download_folder_path=download_folder_path, version_main=version_main)
            driver.get(url + mcmaster_id)

            if auth:
                login(driver, auth)
                time.sleep(1)

            download_STEP(driver)
            generate_label(driver, output_path / mcmaster_id / f"{mcmaster_id}.json")

            time.sleep(1)
            convert_cad(download_folder_path, mcmaster_id)

            driver.quit()
        except Exception as e:
            logging.exception("Failed")
            failed.append(mcmaster_id)
            if driver:
                driver.quit()

    with open(output_path / "failed.json", "w") as f:
        json.dump(failed, f)

def search_for(search_params_file_path: Path, search_limit: int, output_path: Path, delay=20, version_main=None):
    with open(search_params_file_path) as f:
        search_params = json.load(f)

    searcher = McmasterSearcher(search_params) 
    all_cad_ids = []
    while not searcher.is_done():
        for i in range(search_limit):
            url = searcher.next()
            driver = create_browser(delay, version_main=version_main)
            driver.get(url)

            # Pretty dumb, mcmaster carr search query params are kinda bugged, so actually 
            # click one of the filter params twice(for no-op) so things actually filter
            search_params = url.split("/")[5:]
            example_href = search_params[-1] + "/"
            driver.find_element(By.XPATH, '//a[@href="'+example_href+'"]').click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//a[@href="'+example_href+'"]').click()

            links = driver.find_elements(By.CSS_SELECTOR, "a.PartNbrLnk")
            cad_ids = [link.text for link in links if link.text]

            if not cad_ids:
                logging.error(f"Could not find any fasteners under {url}")
            else:
                logging.info(f"Found {len(cad_ids)} under {url}")

            if len(cad_ids) > search_limit:
                logging.info(f"Pruning to {search_limit=} fasteners")
                cad_ids = cad_ids[:search_limit]

            all_cad_ids += cad_ids

            driver.close()
            driver.quit
    
    output_cads_json = output_path / "cads_json_from_search.json"
    logging.info(f"Saving cads_json file scraped from searching to {output_cads_json}. So if downloading " + \
                 "fails you can pass this file in to continue.")
    with open(output_cads_json, "w") as f:
        json.dump(all_cad_ids, f)
    return output_cads_json

@click.command(help="Scrape McMaster Carr for CAD models")
@click.option("--cads_json", "cads_json", default=None, help="Input json containing cad models to pull")
@click.option("--search_params", "search_params", default=None, help="Input json containing search params for cad models to pull")
@click.option("--search_limit", default=1, help="Limit of cad models to pull for each category")
@click.option("--login", is_flag=True, help="Choose to login")
@click.option("--output_path", "output_path", required=True, help="Output folder to download cad models to")
@click.option("--version_main", default=None, help="Your version of chromedriver, if default is not compatible")
def main(cads_json, search_params, search_limit, output_path, version_main, login):
    logging.basicConfig(level=logging.INFO)
    assert not (search_params and cads_json), f"'search_params' and 'cads_json' flags can't both be specified, as they are different methods of pulling models."

    output_path = Path(output_path)
    assert output_path.exists(), f"{output_path} does not exist"

    version_main = int(version_main)
    if search_params:
        search_params_file_path = Path(search_params)
        assert search_params_file_path.exists(), f"{search_params_file_path} does not exist"
        cads_json = search_for(search_params_file_path, search_limit, output_path, version_main=version_main)
    
    cads_json_path = Path(cads_json)
    assert cads_json_path.exists(), f"{cads_json_path} does not exist"

    with open(cads_json_path) as f:
        cads = json.load(f)

    auth = None
    if login:
        email = input("McMaster Login Email: ")
        password = getpass.getpass("McMaster Login Password: ")
        auth = (email, password)

    fetch_cads(output_path, f"{URL}/", cads=cads, auth=auth, version_main=version_main)

    # Convert cads functionality

if __name__ == "__main__":
    main()
