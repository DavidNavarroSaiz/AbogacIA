from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import shutil

# List of legal topics (limited for development purposes)
temas_legales = [
    "Divorcio", "PQR", "Abandono de bienes", "Abandono de menores"
]

def create_download_directory(topic):
    topic_dir = os.path.join("./downloads", topic)
    if not os.path.exists(topic_dir):
        os.makedirs(topic_dir)
    return os.path.abspath(topic_dir)

def move_downloaded_files(topic):
    download_dir = os.path.abspath("./downloads")
    topic_dir = create_download_directory(topic)
    for file_name in os.listdir(download_dir):
        if file_name.endswith(".pdf"):
            shutil.move(os.path.join(download_dir, file_name), os.path.join(topic_dir, file_name))

def initialize_driver(download_dir):
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("browser.download.folderList", 2)
    firefox_profile.set_preference("browser.download.dir", download_dir)
    firefox_profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    firefox_profile.set_preference("pdfjs.disabled", True)
    firefox_profile.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_profile.set_preference("browser.download.manager.focusWhenStarting", False)
    firefox_profile.set_preference("browser.download.useDownloadDir", True)
    firefox_profile.set_preference("browser.helperApps.alwaysAsk.force", False)
    firefox_profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
    firefox_profile.set_preference("browser.download.manager.closeWhenDone", True)
    firefox_profile.set_preference("browser.download.manager.showAlertOnComplete", False)
    firefox_profile.set_preference("browser.download.manager.useWindow", False)
    firefox_profile.set_preference("services.sync.prefs.sync.browser.download.manager.showWhenStarting", False)

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.profile = firefox_profile

    driver = webdriver.Firefox(options=firefox_options)
    return driver

def download_documents(driver, topic, num_documents=10):
    try:
        # Ensure the sidebar is visible
        sidebar_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="resultForm:hidebutton"]/span[1]'))
        )
        driver.execute_script("arguments[0].click();", sidebar_button)

        # Ensure the search bar is interactable
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchForm:temaInput"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", search_bar)
        
        # Clear and send new search term
        search_bar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "searchForm:temaInput"))
        )
        driver.execute_script("arguments[0].click();", search_bar)
        search_bar.clear()
        search_bar.send_keys(topic)
        
        # Click the search button
        search_button = driver.find_element(By.XPATH, "//span[text()='Buscar']/parent::button")
        driver.execute_script("arguments[0].click();", search_button)
        
        time.sleep(10)

        downloaded_count = 0

        while downloaded_count < num_documents:
            download_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "resultForm:j_idt259_menuButton"))
            )
            driver.execute_script("arguments[0].click();", download_button)
            
            pdf_option = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "resultForm:j_idt262"))
            )
            driver.execute_script("arguments[0].click();", pdf_option)

            time.sleep(10)

            files = os.listdir("./downloads")
            if any(file.endswith(".pdf") for file in files):
                print(f"PDF file {downloaded_count + 1} has been downloaded successfully for topic '{topic}'.")
                downloaded_count += 1
            else:
                print(f"PDF file download failed for topic '{topic}'.")

            if downloaded_count < num_documents:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='resultForm:j_idt242']/span[1]"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(10)

    except Exception as e:
        print(f"An error occurred for topic '{topic}': {e}")

if __name__ == "__main__":
    download_dir = os.path.abspath("./downloads")
    driver = initialize_driver(download_dir)
    driver.get("http://consultajurisprudencial.ramajudicial.gov.co:8080/WebRelatoria/csj/index.xhtml")

    for topic in temas_legales:
        download_documents(driver, topic, num_documents=2)
        move_downloaded_files(topic)

    driver.quit()
