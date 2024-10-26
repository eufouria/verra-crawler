from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import sys
from config import config

# Function to download PDFs from a list of URLs
def download_pdf(pdf_url, folder_name):
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        
        # Extract the filename from the URL
        filename = os.path.basename(pdf_url)
        pdf_path = os.path.join(folder_name, filename)
        
        # Save the PDF file
        with open(pdf_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded PDF: {filename}")
        
    except Exception as e:
        print(f"Failed to download PDF from {pdf_url}: {e}")

# Function to extract and save article content
def extract_article_content(article_url, txt_folder, pdf_folder):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Set up WebDriver
    chrome_driver_path = config.CHROME_DRIVER_PATH
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)

    # Navigate to the article page
    driver.get(article_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Dismiss cookie banner if present
    try:
        driver.execute_script("""
            var allowAllButton = document.getElementById('CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll');
            if (allowAllButton) {
                allowAllButton.click();
            }
        """)
        print("Clicked the 'Allow all' button.")
    except Exception as e:
        print("Failed to dismiss cookie banner by clicking 'Allow all':", e)

    # Extract article content
    try:
        article_element = driver.find_element(By.TAG_NAME, "article")  # Ensure we're targeting the right element
        article_content = article_element.text  # Get the text of the article
        
        if not article_content.strip():  # Check if the content is empty
            print(f"No content found for {article_url}.")
            return

        # Create a unique filename based on the article URL or title
        article_title = article_element.find_element(By.TAG_NAME, "h1").text.strip()  # Assuming the title is in an <h1> tag
        safe_title = "".join(c for c in article_title if c.isalnum() or c in (' ', '-', '_')).rstrip()  # Sanitize filename
        file_name = f"{safe_title}.txt"  # Use sanitized title as filename

        # Save the article content to a .txt file
        os.makedirs(txt_folder, exist_ok=True)
        with open(os.path.join(txt_folder, file_name), 'w', encoding='utf-8') as f:
            f.write(article_content)

        print(f"Saved article content from {article_url} to {file_name}.")

    except Exception as e:
        print(f"Failed to extract content from {article_url}: {e}")

    # Look for PDF links in the article
    pdf_links = []
    for link in driver.find_elements(By.TAG_NAME, 'a'):
        href = link.get_attribute('href')
        if href and href.lower().endswith('.pdf'):
            pdf_links.append(href)

    # Download found PDF links
    os.makedirs(pdf_folder, exist_ok=True)
    for pdf_link in pdf_links:
        download_pdf(pdf_link, pdf_folder)

# Function to scrape articles from multiple pages
def download_articles(txt_folder, pdf_folder, base_url, page_count):
    # Set up WebDriver
    chrome_driver_path = config.CHROME_DRIVER_PATH
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)

    # Iterate over all pages
    for page_num in range(1, page_count + 1):
        page_url = f"{base_url}?sf_paged={page_num}"
        driver.get(page_url)

        # Wait until the articles section is visible
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "article")))

        # Find all article links on the current page
        article_links = driver.find_elements(By.XPATH, "//article/a")

        # Debugging: Print the number of articles found on this page
        print(f"Found {len(article_links)} articles on page {page_num}.")

        # Process each article link
        for index, link in enumerate(article_links):
            article_url = link.get_attribute('href')
            print(f"Processing: {article_url}")
            extract_article_content(article_url, txt_folder, pdf_folder)

    # Close the driver
    driver.quit()

# Download articles from all three pages
if __name__ == "__main__":
    #choice = input("Enter the page to scrape ('program_notices', 'verra_views', or 'verra_news'): ").strip()
    choice = sys.argv[1].lower()
    if choice == "program_notices":
        base_url = "https://verra.org/program-notices"
        txt_folder = "verra/program_notices/txt"
        pdf_folder = "verra/program_notices/pdf"
        page_count = 6  # pages to scrape
        # Create the folders and download resources
        os.makedirs(txt_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)
        download_articles(txt_folder, pdf_folder, base_url, page_count)
    elif choice == "verra_views":
        base_url = "https://verra.org/verra-views"
        txt_folder = "verra/verra_views/txt"
        pdf_folder = "verra/verra_views/pdf"
        page_count = 1  # pages to scrape
        os.makedirs(txt_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)
        download_articles(txt_folder, pdf_folder, base_url, page_count)
    elif choice == "verra_news":
        base_url = "https://verra.org/news"
        txt_folder = "verra/verra_news/txt"
        pdf_folder = "verra/verra_news/pdf"
        page_count = 110  # pages to scrape
        os.makedirs(txt_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)
        download_articles(txt_folder, pdf_folder, base_url, page_count)
    elif choice == "all":
        print("Downloading Verra News...")
        base_url = "https://verra.org/news"
        txt_folder = "verra/verra_news/txt"
        pdf_folder = "verra/verra_news/pdf"
        page_count = 110  # pages to scrape
        os.makedirs(txt_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)
        download_articles(txt_folder, pdf_folder, base_url, page_count)

        print("Downloading Verra Views...")
        base_url = "https://verra.org/verra-views"
        txt_folder = "verra/verra_views/txt"
        pdf_folder = "verra/verra_views/pdf"
        page_count = 1  # pages to scrape
        os.makedirs(txt_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)
        download_articles(txt_folder, pdf_folder, base_url, page_count)

        print("Downloading Verra Program Notices...")
        base_url = "https://verra.org/program-notices"
        txt_folder = "verra/program_notices/txt"
        pdf_folder = "verra/program_notices/pdf"
        page_count = 6  # pages to scrape
        os.makedirs(txt_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)
        download_articles(txt_folder, pdf_folder, base_url, page_count)
    else:
        print("Invalid choice. Please choose 'program_notices', 'verra_views', or 'verra_news'.")
        exit()