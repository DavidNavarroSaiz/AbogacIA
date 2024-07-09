from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import shutil
from utils_db import UtilsDB
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import openai
from dotenv import load_dotenv

class DocumentDownloader:
    def __init__(self, topics):
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.topics = topics
        self.database_name = "abogacia_data"
        self.download_dir = os.path.abspath("./downloads")
        self.utils_db = self.initialize_utils_db()

    def initialize_utils_db(self):
        ef = OpenAIEmbeddings()
        vectordb = Chroma(persist_directory=f"./{self.database_name}", embedding_function=ef)
        return UtilsDB(vectordb)

    def create_download_directory(self, topic):
        topic_dir = os.path.join(self.download_dir, topic)
        if not os.path.exists(topic_dir):
            os.makedirs(topic_dir)
        return os.path.abspath(topic_dir)

    def move_downloaded_file(self, file_path, topic):
        topic_sanitized = topic.replace(" ", "_").lower()
        topic_dir = self.create_download_directory(topic_sanitized)
        new_path = os.path.join(topic_dir, os.path.basename(file_path))
        shutil.move(file_path, new_path)
        return new_path

    def initialize_driver(self):
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("browser.download.folderList", 2)
        firefox_profile.set_preference("browser.download.dir", self.download_dir)
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

    def load_downloaded_files(self, topic=None):
        existing_files = set()
        topic_sanitized = topic.replace(" ", "_").lower() if topic else None
        topic_dirs = [os.path.join(self.download_dir, t.replace(" ", "_").lower()) for t in self.topics if (topic_sanitized is None or t.replace(" ", "_").lower() == topic_sanitized)]
        for topic_dir in topic_dirs:
            if os.path.exists(topic_dir):
                for foldername, subfolders, filenames in os.walk(topic_dir):
                    for filename in filenames:
                        if filename.endswith(".pdf"):
                            existing_files.add(filename)
        print(f"Existing files for topic '{topic}': {len(existing_files)}")
        return existing_files

    def get_current_page_number(self, driver):
        try:
            print("getting page number")
            page_number_element = driver.find_element(By.XPATH, '//*[@id="resultForm:pagText2"]')
            page_text = page_number_element.text.strip()
            if "Resultado:" in page_text:
                parts = page_text.split()
                return int(parts[1])
            return None
        except:
            return None

    def get_document_ids_on_page(self, driver, page_number):
        document_id = ""
        i = page_number - 1
        print("getting Document Id")

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

    def download_documents(self, driver, topic, num_documents):
        downloaded_files = self.load_downloaded_files(topic)
        print("downloaded_files", downloaded_files)
        current_page = None
        consecutive_page_count = 0
        time.sleep(5)
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

        downloaded_count = len(downloaded_files)
        if downloaded_count >= num_documents:
            print(f"Already have {num_documents} or more documents for topic '{topic}'. Skipping download.")
            return

        while downloaded_count < num_documents:
            new_page = self.get_current_page_number(driver)
            if new_page is not None:
                if new_page == current_page:
                    consecutive_page_count += 1
                    if consecutive_page_count >= 3:
                        print(f"Stopped searching for topic '{topic}' as the page did not change for 3 consecutive attempts.")
                        break
                else:
                    consecutive_page_count = 0
                    current_page = new_page

                print("Trying to download document")
                download_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "resultForm:j_idt265_menuButton"))
                )
                driver.execute_script("arguments[0].click();", download_button)

                pdf_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "resultForm:j_idt268"))
                )
                driver.execute_script("arguments[0].click();", pdf_option)

                time.sleep(10)

                files = os.listdir(self.download_dir)
                for file in files:
                    if file.endswith(".pdf"):
                        file_path = os.path.join(self.download_dir, file)
                        
                        if file not in downloaded_files:
                            print("File is new, moving and adding to Chroma DB")
                            new_file_path = self.move_downloaded_file(file_path, topic)
                            self.utils_db.add_db_doc(new_file_path)
                            downloaded_files.add(file)
                            downloaded_count += 1
                            time.sleep(2)
                            break
                        else:
                            print(f"PDF file already exists, removing file \n'{file_path}'")
                            os.remove(file_path)
                            time.sleep(2)
                            
                if downloaded_count >= num_documents:
                    break

            if downloaded_count < num_documents:
                print("attempting pressing next button")
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@id='resultForm:j_idt248' and @name='resultForm:j_idt248' and @class='ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only pageButton']"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(10)

    def run(self):
        driver = self.initialize_driver()
        driver.get("http://consultajurisprudencial.ramajudicial.gov.co:8080/WebRelatoria/csj/index.xhtml")

        for topic, num_documents in self.topics.items():
            self.download_documents(driver, topic, num_documents)

        driver.quit()

if __name__ == "__main__":
    temas_legales = {"Divorcio": 10, "PQR": 10, "Abandono de bienes": 10, "Abandono de menores": 10}

    downloader = DocumentDownloader(temas_legales)
    downloader.run()
