from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import shutil

# List of legal topics (limited for development purposes)
temas_legales = [
    "Divorcio", "PQR", "Abandono de bienes", "Abandono de menores"
]

# Global variable for number of documents to download per topic
NUM_DOCUMENTS = 10

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

def read_downloaded_ids(topic):
    topic_dir = create_download_directory(topic)
    downloaded_ids_file = os.path.join(topic_dir, "downloaded_ids.txt")
    if not os.path.exists(downloaded_ids_file):
        return set()
    
    with open(downloaded_ids_file, "r") as file:
        return set(file.read().splitlines())

def save_downloaded_id(topic, doc_id):
    topic_dir = create_download_directory(topic)
    downloaded_ids_file = os.path.join(topic_dir, "downloaded_ids.txt")
    with open(downloaded_ids_file, "a") as file:
        file.write(f"{doc_id}\n")

def get_current_page_number(driver):
    try:
        page_number_element = driver.find_element(By.XPATH, '//*[@id="resultForm:pagText2"]')
        page_text = page_number_element.text.strip()
        if "Resultado:" in page_text:
            parts = page_text.split()
            return int(parts[1])
        return None
    except:
        return None

def get_document_ids_on_page(driver, page_number):
    document_id = ""
    i = page_number - 1
    
    for font_index in [2, 3, 4]:
        try:
            id_label_xpath = f'//*[@id="resultForm:jurisTable:{i}:descrip"]/div/div/font[{font_index}]'
            id_label = driver.find_element(By.XPATH, id_label_xpath)
            if id_label.text == "ID:":
                id_value_xpath = f'//*[@id="resultForm:jurisTable:{i}:descrip"]/div/div/font[{font_index + 1}]'
                id_value = driver.find_element(By.XPATH, id_value_xpath).text
                document_id = id_value
                break  # Stop searching further once ID is found
        except:
            continue
    return document_id

def download_documents(driver, topic, num_documents):
    try:
        downloaded_ids = read_downloaded_ids(topic)
        current_page = None
        consecutive_page_count = 0

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

        downloaded_count = len(downloaded_ids)
        print(f"Number of documents already downloaded for topic '{topic}': {downloaded_count}")
        if downloaded_count >= num_documents:
            print(f"Already have {num_documents} or more documents for topic '{topic}'. Skipping download.")
            return

        while downloaded_count < num_documents:
            new_page = get_current_page_number(driver)
            if new_page is not None:
                if new_page == current_page:
                    consecutive_page_count += 1
                    if consecutive_page_count >= 3:
                        print(f"Stopped searching for topic '{topic}' as the page did not change for 3 consecutive attempts.")
                        break
                else:
                    consecutive_page_count = 0
                    current_page = new_page

                document_id_on_page = get_document_ids_on_page(driver, current_page)
                if document_id_on_page and document_id_on_page not in downloaded_ids:
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
                        save_downloaded_id(topic, document_id_on_page)
                    else:
                        print(f"PDF file download failed for topic '{topic}'.")

                    if downloaded_count >= num_documents:
                        break
                else:
                    print(f"Document ID {document_id_on_page} already downloaded for topic '{topic}'.")

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
        download_documents(driver, topic, NUM_DOCUMENTS)
        move_downloaded_files(topic)

    driver.quit()
