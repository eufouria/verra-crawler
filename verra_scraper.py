from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
import os
import requests

def download_pdf(pdf_url, file_name, folder_name, proj_id):
    try:
        response = requests.get(pdf_url, timeout=10)  
        valid_file_name = "".join([c if c.isalnum() or c in (' ', '.', '_', '-') else '_' for c in file_name])
        file_path = os.path.join(proj_id, folder_name, valid_file_name)
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {file_name} to folder: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {file_name}: {e}")

def download_projects(proj_ids, parent_folder):
    # Set up WebDriver
    chrome_driver_path = '/Users/khoa/Downloads/chromedriver-mac-arm64/chromedriver'
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)

    # Process each project
    for proj_id in proj_ids:
        driver.get(f'https://registry.verra.org/app/projectDetail/VCS/{proj_id}')
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "card-header")))

        # Verra documentation sections
        sections = {
            "VCS PIPELINE DOCUMENTS": "pipeline",
            "VCS REGISTRATION DOCUMENTS": "registration",
            "VCS ISSUANCE DOCUMENTS": "issuance",
            "VCS OTHER DOCUMENTS": "other"
        }

        # Create directories for each section
        proj_path = os.path.join(parent_folder, proj_id)
        os.makedirs(proj_path, exist_ok=True)
        for folder in sections.values():
            os.makedirs(os.path.join(proj_path, folder), exist_ok=True)

        # Find section headers and process each section
        section_headers = driver.find_elements(By.XPATH, "//div[@class='card-header bg-primary']")
        for header in section_headers:
            section_title = header.text.strip()
            folder_name = sections.get(section_title, "other")
            
            try:
                card_body = header.find_element(By.XPATH, "./following-sibling::div[contains(@class,'card-body')]")
                pdf_links = card_body.find_elements(By.XPATH, ".//tbody//tr//td//a")
                
                # Use ThreadPoolExecutor to download PDFs concurrently
                with ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(download_pdf, 
                                        link.get_attribute('href'), 
                                        link.text.strip(), 
                                        folder_name, 
                                        proj_path)
                        for link in pdf_links
                    ]
                
            except Exception as e:
                print(f"Error processing section '{section_title}': {e}")
    
    driver.quit()

# Run the script with project IDs
if __name__ == "__main__":
    parent_folder = "verra"
    os.makedirs(parent_folder, exist_ok=True)
    import pandas as pd
    df = pd.read_csv('allprojects.csv')
    proj_ids = list(df['ID'].astype(str))
    download_projects(proj_ids, parent_folder)
