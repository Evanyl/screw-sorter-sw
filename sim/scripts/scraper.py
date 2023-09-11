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

from utils import convert_step_to_stl, McmasterSearcher, URL
from typing import Optional


properties = {
    "Length": 'length', 
    "Thread Size": 'thread_size',
    "Thread Pitch": 'thread_pitch'
}

def create_browser(delay: int, download_folder_path: Optional[Path] = None):
    options = uc.ChromeOptions()

    if download_folder_path is not None:
        prefs = {'download.default_directory' : str(download_folder_path)}
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
        convert_step_to_stl(download_folder_path / step_file, download_folder_path / f"{file_name}.stl")
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

def fetch_cads(output_path, url, cads=[], delay=20):
    for cad in cads:
        mcmaster_id = cad["mcmaster_id"]
        category = cad["category"]
        download_folder_path = output_path / category

        driver = create_browser(delay, download_folder_path=download_folder_path)
        driver.get(url + mcmaster_id)

        download_STEP(driver)
        generate_label(driver, output_path / category / f"{mcmaster_id}.json")

        time.sleep(1)
        convert_cad(download_folder_path, mcmaster_id)
        driver.close()
        driver.quit

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
            example_href = url.split("/")[-2] + "/"
            filter_param = driver.find_element(By.XPATH, '//a[@href="'+example_href+'"]')
            filter_param.click()
            time.sleep(0.5)
            filter_param = driver.find_element(By.XPATH, '//a[@href="'+example_href+'"]')
            filter_param.click()

            links = driver.find_elements(By.CSS_SELECTOR, "a.PartNbrLnk")
            cad_ids = [{"mcmaster_id": link.text, "category": link.text} for link in links if link.text]

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
@click.option("--output_path", "output_path", required=True, help="Output folder to download cad models to")
def main(cads_json, search_params, search_limit, output_path):
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

    fetch_cads(output_path, f"{URL}/", cads=cads)

if __name__ == "__main__":
    main()
