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


properties = {
    "Length": 'length', 
    "Thread Size": 'thread_size',
    "Thread Pitch": 'thread_pitch'
}

def create_browser(delay: int, download_folder_path: Optional[Path] = None):
    backoff_times = [2, 4, 8, 16, 32]
    driver = None
    for backoff_time in backoff_times:
        try:
            options = uc.ChromeOptions()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')

            if download_folder_path is not None:
                prefs = {'download.default_directory' : str(download_folder_path)}
                options.add_experimental_option('prefs', prefs)

            driver = uc.Chrome(
                options = options,
            )
            driver.implicitly_wait(delay)
            break
        except Exception:
            time.sleep(backoff_time)

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
        value = cols[1].get_attribute('innerText')

        if property in properties:
            label[properties[property]] = value.replace(" ", "")

    logging.info(f"Creating label at: {label_path}")
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

def fetch_cads(output_path, url, cads=[], delay=20, auth=None):
    failed = []
    for i, cad in enumerate(cads):
        logging.info(f"Downloading {i}/{len(cads)}")
        try:
            mcmaster_id = cad
            download_folder_path = output_path / mcmaster_id
            if download_folder_path.exists():
                shutil.rmtree(download_folder_path)
            driver = create_browser(delay, download_folder_path=download_folder_path)
            driver.get(url + mcmaster_id)

            if auth:
                login(driver, auth)
                time.sleep(1)

            download_STEP(driver)
            generate_label(driver, output_path / mcmaster_id / f"{mcmaster_id}.json")

            time.sleep(1)
            convert_cad(download_folder_path, mcmaster_id)

            driver.close()
            driver.quit()
        except Exception as e:
            logging.error(e)
            failed.append(mcmaster_id)

    with open(output_path / "failed.json", "w") as f:
        json.dump(failed, f)

def search_for(search_params_file_path: Path, search_limit: int, output_path: Path, delay=20):
    with open(search_params_file_path) as f:
        search_params = json.load(f)

    searcher = McmasterSearcher(search_params) 
    all_cad_ids = []
    while not searcher.is_done():
        for i in range(search_limit):
            url = searcher.next()
            driver = create_browser(delay)
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
def main(cads_json, search_params, search_limit, output_path, login):
    logging.basicConfig(level=logging.INFO)
    assert not (search_params and cads_json), f"'search_params' and 'cads_json' flags can't both be specified, as they are different methods of pulling models."

    output_path = Path(output_path)
    assert output_path.exists(), f"{output_path} does not exist"

    if search_params:
        search_params_file_path = Path(search_params)
        assert search_params_file_path.exists(), f"{search_params_file_path} does not exist"
        cads_json = search_for(search_params_file_path, search_limit, output_path)
    
    cads_json_path = Path(cads_json)
    assert cads_json_path.exists(), f"{cads_json_path} does not exist"

    with open(cads_json_path) as f:
        cads = json.load(f)

    auth = None
    if login:
        email = input("McMaster Login Email: ")
        password = getpass.getpass("McMaster Login Password: ")
        auth = (email, password)

    fetch_cads(output_path, f"{URL}/", cads=cads, auth=auth)

    # Convert cads functionality

if __name__ == "__main__":
    main()
