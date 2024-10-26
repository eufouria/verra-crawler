# verra-crawler
Crawl Documentation of projects on [Verra](https://verra.org/) website

## Requirements

- Google Chrome browser
- [Chrome WebDriver](https://www.chromedriverdownload.com/en/downloads/chromedriver-129-download) (compatible with your version of Chrome) 

## Requirement Installation
```
pip install -r requirements.txt
```

## Configuration
- update `config.py` with the path to the your Chrome WebDriver

## Run Scraper
### Project Documentation Scraper
```
python3 verra_scraper.py PROGRAM
```
use `python3 verra_scraper.py all` for all programs

### Methodologies and Verification Section Scraper
```
python3 verra_methods.py SECTION_ARG
```
use `python3 verra_methods.py all` for all sections

### Views/Notices/News Section Scraper
```
python3 verra_views.py SECTION_ARG
```
use `python3 verra_views.py all` for all sections


