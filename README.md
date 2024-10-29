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
python3 scraper_proj.py PROGRAM
```
use `python3 scraper_proj.py all` for all programs

### Methodologies and Verification Section Scraper
```
python3 scraper_methods.py SECTION_ARG
```
use `python3 scraper_methods.py all` for all sections

### Views/Notices/News Section Scraper
```
python3 scraper_views.py SECTION_ARG
```
use `python3 scraper_views.py all` for all sections


