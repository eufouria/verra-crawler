from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

import os
import requests
import sys
from config import config


def get_project_ids(program, data_folder):
    program_data_files = {
        'CCB': ['ccbvcus.csv', 'allprojects.csv'],
        'PWRP': ['plasticcredits.csv', 'allprojects.csv'],
        'VCS': ['vcus.csv', 'allprojects.csv'],
        'SDVISTA': ['sdvistavcus.csv', 'allprojects.csv'],
        'CA_OPR': ['complianceprojects.csv']
    }
    proj_ids = []
    for file in program_data_files.get(program):
        df_00 = pd.read_csv(os.path.join(data_folder, program, file))
        proj_ids += list(df_00['ID'].astype(str))
    return list(set(proj_ids))


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

def download_projects(parent_folder, program, proj_ids):
    # Set up WebDriver
    chrome_driver_path = config.CHROME_DRIVER_PATH
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)

    # Process each project
    for proj_id in proj_ids:
        driver.get(f'https://registry.verra.org/app/projectDetail/{program}/{proj_id}')
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "card-header")))

        # Verra documentation sections
        program_sections = {
                "VCS" : {
                    "VCS PIPELINE DOCUMENTS": "pipeline",
                    "VCS REGISTRATION DOCUMENTS": "registration",
                    "VCS ISSUANCE DOCUMENTS": "issuance",
                    "VCS OTHER DOCUMENTS": "other"
                },
                
                "PWRP" : {
                    "PWRP PIPELINE DOCUMENTS": "pipeline",
                    "PWRP REGISTRATION DOCUMENTS": "registration",
                    "PWRP VERIFICATION DOCUMENTS": "verification",
                    "PWRP OTHER DOCUMENTS": "other"
                },
                
                "CCB" : {
                    "CCB VALIDATION DOCUMENTS": "validation",
                    "CCB VERIFICATION DOCUMENTS": "verification",
                    "CCB OTHER DOCUMENTS": "other"
                },

                "SDVISTA" : {
                    "SD VISTA OTHER DOCUMENTS": "other",
                    "SD VISTA VERIFICATION DOCUMENTS": "verification",
                    "SD VISTA REGISTRATION DOCUMENTS": "registration",
                    "SD VISTA PIPELINE LISTING DOCUMENTS": "pipeline"
                },

                "CA_OPR" : {
                    "COMPLIANCE LISTING DOCUMENTS": "listing",
                    "COMPLIANCE ISSUANCE DOCUMENTS": "issuance",
                    "COMPLIANCE OTHER DOCUMENTS": "other",
                    "COMPLIANCE REGISTRATION DOCUMENTS": "registration"
                }
        }
        

        # Create directories for each section
        proj_path = os.path.join(parent_folder, program.upper(), proj_id)
        os.makedirs(proj_path, exist_ok=True)
        for folder in program_sections.get(program).values():
            os.makedirs(os.path.join(proj_path, folder), exist_ok=True)

        # Find section headers and process each section
        section_headers = driver.find_elements(By.XPATH, "//div[@class='card-header bg-primary']")
        for header in section_headers:
            section_title = header.text.strip()
            if section_title not in program_sections.get(program):
                print(f"Skipping section '{section_title}'")
                continue
            folder_name = program_sections.get(program).get(section_title, "other")
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
    parent_folder = "verra/projects"
    os.makedirs(parent_folder, exist_ok=True)
    all_programs = ["VCS", "PWRP", "CCB", "SDVISTA", "CA_OPR"]
    program_arg = sys.argv[1].upper()
    if program_arg in all_programs:
        proj_ids = get_project_ids(program_arg, 'program_data')
        download_projects(parent_folder, program_arg, proj_ids)
    elif program_arg == "ALL":
        print("DOWNLOADING ALL PROJECTS...")
        for program in all_programs:
            print(f"Downloading projects of {program}...")
            proj_ids = get_project_ids(program, 'program_data')
            download_projects(parent_folder, program, proj_ids)
    else:
        print("Invalid argument. Please choose from 'VCS', 'PWRP', 'CCB', 'SDVISTA', 'CA_OPR', or 'ALL'.")
        sys.exit()
