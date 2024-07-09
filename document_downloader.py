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
    """
    A class to download and manage legal documents using Selenium and Chroma vector database.

    Attributes:
        topics (dict): A dictionary with topics as keys and number of documents to download as values.
        database_name (str): The name of the database.
        download_dir (str): The directory to save downloaded documents.
        utils_db (UtilsDB): An instance of UtilsDB to interact with the vector database.
    """

    def __init__(self, topics):
        """
        Initializes the DocumentDownloader with topics and sets up environment variables and database.

        Args:
            topics (dict): A dictionary with topics as keys and number of documents to download as values.
        """
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.topics = topics
        self.database_name = "abogacia_data"
        self.download_dir = os.path.abspath("./downloads")
        self.utils_db = self.initialize_utils_db()

    def initialize_utils_db(self):
        """
        Initializes the UtilsDB with Chroma vector database.

        Returns:
            UtilsDB: An instance of UtilsDB.
        """
        ef = OpenAIEmbeddings()
        vectordb = Chroma(persist_directory=f"./{self.database_name}", embedding_function=ef)
        return UtilsDB(vectordb)

    def create_download_directory(self, topic):
        """
        Creates a directory for a specific topic if it doesn't already exist.

        Args:
            topic (str): The topic for which the directory is created.

        Returns:
            str: The absolute path of the created directory.
        """
        topic_dir = os.path.join(self.download_dir, topic)
        if not os.path.exists(topic_dir):
            os.makedirs(topic_dir)
        return os.path.abspath(topic_dir)

    def sanitize_topic(self, topic):
        """
        Sanitizes the topic by replacing spaces with underscores and converting to lowercase.

        Args:
            topic (str): The topic to sanitize.

        Returns:
            str: The sanitized topic.
        """
        return topic.replace(" ", "_").lower()

    def move_downloaded_file(self, file_path, topic):
        """
        Moves the downloaded file to the appropriate directory based on the topic.

        Args:
            file_path (str): The path of the downloaded file.
            topic (str): The topic associated with the file.

        Returns:
            str: The new path of the moved file.
        """
        topic_sanitized = self.sanitize_topic(topic)
        topic_dir = self.create_download_directory(topic_sanitized)
        new_path = os.path.join(topic_dir, os.path.basename(file_path))
        shutil.move(file_path, new_path)
        return new_path

    def initialize_driver(self):
        """
        Initializes the Selenium WebDriver with Firefox profile settings.

        Returns:
            WebDriver: The initialized Selenium WebDriver.
        """
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
        """
        Loads the already downloaded files for a specific topic.

        Args:
            topic (str, optional): The topic to load files for. Defaults to None.

        Returns:
            set: A set of filenames of the already downloaded files.
        """
        existing_files = set()
        topic_sanitized = self.sanitize_topic(topic) if topic else None
        topic_dirs = [os.path.join(self.download_dir, self.sanitize_topic(t)) for t in self.topics.keys() if (topic_sanitized is None or self.sanitize_topic(t) == topic_sanitized)]
        for topic_dir in topic_dirs:
            if os.path.exists(topic_dir):
                for foldername, subfolders, filenames in os.walk(topic_dir):
                    for filename in filenames:
                        if filename.endswith(".pdf"):
                            existing_files.add(filename)
        print(f"Existing files for topic '{topic}': {len(existing_files)}")
        return existing_files

    def get_current_page_number(self, driver):
        """
        Retrieves the current page number from the search results.

        Args:
            driver (WebDriver): The Selenium WebDriver.

        Returns:
            int: The current page number, or None if it cannot be retrieved.
        """
        try:
            print("Getting page number")
            page_number_element = driver.find_element(By.XPATH, '//*[@id="resultForm:pagText2"]')
            page_text = page_number_element.text.strip()
            if "Resultado:" in page_text:
                parts = page_text.split()
                return int(parts[1])
            return None
        except:
            return None

    def download_documents(self, driver, topic, num_documents):
        """
        Downloads the specified number of documents for a topic.

        Args:
            driver (WebDriver): The Selenium WebDriver.
            topic (str): The topic for which documents are to be downloaded.
            num_documents (int): The number of documents to download.
        """
        downloaded_files = self.load_downloaded_files(topic)
        print("Downloaded files", downloaded_files)
        current_page = None
        consecutive_page_count = 0
        time.sleep(5)
        self.ensure_sidebar_visible(driver)
        self.perform_search(driver, topic)

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
                if self.click_download_button(driver):
                    if self.click_pdf_option(driver):
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
                self.click_next_button(driver)
                time.sleep(10)

    def ensure_sidebar_visible(self, driver):
        """
        Ensures the sidebar is visible.

        Args:
            driver (WebDriver): The Selenium WebDriver.
        """
        sidebar_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="resultForm:hidebutton"]/span[1]'))
        )
        driver.execute_script("arguments[0].click();", sidebar_button)

    def perform_search(self, driver, topic):
        """
        Performs the search for a given topic.

        Args:
            driver (WebDriver): The Selenium WebDriver.
            topic (str): The topic to search for.
        """
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchForm:temaInput"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", search_bar)
        search_bar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "searchForm:temaInput"))
        )
        driver.execute_script("arguments[0].click();", search_bar)
        search_bar.clear()
        search_bar.send_keys(topic)
        search_button = driver.find_element(By.XPATH, "//span[text()='Buscar']/parent::button")
        driver.execute_script("arguments[0].click();", search_button)
        time.sleep(10)

    def click_download_button(self, driver):
        """
        Clicks the download button.

        Args:
            driver (WebDriver): The Selenium WebDriver.

        Returns:
            bool: True if the button was clicked, False otherwise.
        """
        try:
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "resultForm:j_idt265_menuButton"))
            )
            driver.execute_script("arguments[0].click();", download_button)
            return True
        except:
            return False

    def click_pdf_option(self, driver):
        """
        Clicks the PDF option from the download menu.

        Args:
            driver (WebDriver): The Selenium WebDriver.

        Returns:
            bool: True if the option was clicked, False otherwise.
        """
        try:
            pdf_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "resultForm:j_idt268"))
            )
            driver.execute_script("arguments[0].click();", pdf_option)
            return True
        except:
            return False

    def click_next_button(self, driver):
        """
        Clicks the next button to navigate to the next page of results.

        Args:
            driver (WebDriver): The Selenium WebDriver.
        """
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@id='resultForm:j_idt248' and @name='resultForm:j_idt248' and @class='ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only pageButton']"))
            )
            driver.execute_script("arguments[0].click();", next_button)
        except:
            pass

    def run(self):
        """
        Runs the document downloading process.
        """
        driver = self.initialize_driver()
        driver.get("http://consultajurisprudencial.ramajudicial.gov.co:8080/WebRelatoria/csj/index.xhtml")

        for topic, num_documents in self.topics.items():
            self.download_documents(driver, topic, num_documents)

        driver.quit()

if __name__ == "__main__":
    temas_legales = {"Divorcio": 10, "PQR": 10, "Abandono de bienes": 10, "Abandono de menores": 10}

    downloader = DocumentDownloader(temas_legales)
    downloader.run()
