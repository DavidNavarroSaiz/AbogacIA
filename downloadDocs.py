from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Set up the download directory
download_dir = "./downloads"

# Set Chrome options to automatically download files to the specified directory
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Add arguments to disable safe browsing and security checks
chrome_options.add_argument("--allow-running-insecure-content")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-site-isolation-trials")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
chrome_options.add_argument("--no-sandbox")

# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Open the web page
    url = "http://consultajurisprudencial.ramajudicial.gov.co:8080/WebRelatoria/csj/index.xhtml"
    driver.get(url)

    # Perform the search (this part assumes you've already implemented it as described earlier)
    search_bar = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "searchForm:temaInput"))
    )
    search_text = "divorcio"
    search_bar.send_keys(search_text)
    
    search_button = driver.find_element(By.XPATH, "//span[text()='Buscar']/parent::button")
    search_button.click()
    
    time.sleep(10)  # Wait for search results to load

    # Locate and click the download button to open the menu
    download_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "resultForm:j_idt259_menuButton"))
    )
    download_button.click()
    # Wait for the menu to appear and click the PDF option
    pdf_option = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "resultForm:j_idt262"))
    )
    pdf_option.click()

    # Wait for the file to download
    time.sleep(10)  # Adjust the waiting time as needed

    # Verify if the file has been downloaded
    files = os.listdir(download_dir)
    if any(file.endswith(".pdf") for file in files):
        print("PDF file has been downloaded successfully.")
    else:
        print("PDF file download failed.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the WebDriver
    driver.quit()
