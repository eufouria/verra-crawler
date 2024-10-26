import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import pickle
import sys

STATE_FILE = 'crawler_state.pkl'

def save_state(to_visit, visited):
    with open(STATE_FILE, 'wb') as f:
        pickle.dump((to_visit, visited), f)
    print("State saved.")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'rb') as f:
            to_visit, visited = pickle.load(f)
        print("State loaded.")
    else:
        to_visit = []
        visited = set()
    return to_visit, visited

def ensure_directory_exists(folder_name):
    """Creates the folder if it doesn't exist."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def download_pdf(url, headers, pdf_folder):
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Check if the content is a PDF
        if 'application/pdf' in response.headers.get('Content-Type', '').lower():
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            pdf_path = os.path.join(pdf_folder, filename)
            
            # Ensure the directory exists before saving the file
            ensure_directory_exists(pdf_folder)
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded PDF: {filename} in folder: {pdf_folder}")
            return True  # Indicate that a PDF was downloaded
        else:
            print(f"URL is not a PDF: {url}")
    
    except requests.RequestException as e:
        print(f"Failed to download PDF from {url}: {e}")
    
    return False  # Indicate that no PDF was downloaded

def extract_and_save_text(soup, url, text_folder):
    """
    Extracts text from the soup and saves it to a .txt file in the specified folder.
    The file name is based on the URL path.
    """
    text_content = soup.get_text(separator='\n', strip=True)
    if text_content:
        parsed_url = urlparse(url)
        # Create a filename based on the path of the URL
        filename = parsed_url.path.strip('/').replace('/', '_') + '.txt'
        text_path = os.path.join(text_folder, filename)
        
        # Ensure the directory exists before saving the file
        ensure_directory_exists(text_folder)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(f"Text from {url}:\n{text_content}\n")
        print(f"Saved text from {url} in folder: {text_folder}")
        return True  # Indicate that text was saved
    return False  # Indicate that no text was saved

def scrape_and_download(start_url, section):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
    }
    
    # Parse the start URL to get the domain and the base path for scraping
    parsed_start_url = urlparse(start_url)
    base_dir = f"verra/{section}"#parsed_start_url.netloc
    base_path = parsed_start_url.path.rstrip('/')  # e.g., /methodologies, /validation
    
    # Define separate directories for PDFs and text files
    pdf_folder = os.path.join(base_dir, "pdf")
    text_folder = os.path.join(base_dir, "text")
    
    # Load the previous state if available
    to_visit, visited = load_state()
    if not to_visit:
        to_visit.append(start_url)
    
    while to_visit:
        current_url = to_visit.pop()
        if current_url in visited:
            continue
        
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Mark this URL as visited
            visited.add(current_url)
            print(f"Visiting: {current_url}")

            files_saved = False

            # Check links on the page for PDFs to download, otherwise save text
            for anchor in soup.find_all('a', href=True):
                link = urljoin(current_url, anchor['href'])
                parsed_link = urlparse(link)
                
                # Only follow links on the same domain and within the specified base path
                if (
                    parsed_link.netloc == parsed_start_url.netloc and 
                    base_path in parsed_link.path
                ):
                    # If the link ends with .pdf, download it, otherwise save the page text.
                    if link.lower().endswith('.pdf'):
                        if download_pdf(link, headers, pdf_folder):
                            files_saved = True
                    else:
                        # If it's not a PDF link, save the text of the page itself.
                        if extract_and_save_text(soup, current_url, text_folder):
                            files_saved = True
                    # Add the link to the stack if not already visited
                    if link not in visited:
                        to_visit.append(link)
            # Log if no files were saved from this page
            if not files_saved:
                print(f"No files to save from {current_url}.")
        except requests.RequestException as e:
            print(f"Failed to retrieve {current_url}: {e}")
        # Save the state after each URL visit
        save_state(to_visit, visited)
        
        # Optional: Add a small delay to avoid overloading the server
        time.sleep(1)

# Usage Example

if __name__ == "__main__":
    urls = {
        "methodology": "https://verra.org/methodologies/",
        "validation": "https://verra.org/validation-verification/"
    }

    program_arg = sys.argv[1].lower()
    if program_arg in urls:
        scrape_and_download(urls[program_arg], program_arg)
    elif program_arg == "all":
        for key, url in urls.items():
            scrape_and_download(url, key)
    else:
        print("Invalid argument. Please choose 'methodology', 'validation', or 'all'.")
        sys.exit()
