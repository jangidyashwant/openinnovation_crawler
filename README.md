# Web Scraper for Product Data
This project contains a web scraper designed to collect product data from e-commerce or similar marketplaces using headless browsers with dynamic content handling, pagination, and error handling.
+ I have configured steamcommunity.com in the script . we can configure other sources also in the config.yaml file.
+ The code will also fetch "Recent activity" and "Historial data" from  the product page in JSON fornat
+ I configured retry option if we get timeout or toomany request error 
+ I have implemented multithreading to run the code parallelly however the website detect if we hit many request at a time from a IP address so it will require proxies to pass unique IP in each thread 
## Project Structure
```Bash
openinnovation_crawler/
│
├── helpers.py                # All helper functions for scraping logic
├── crawler.py                 # Main script that manages scraping execution
├── config.yaml               # Configuration file for sources and scraping parameters
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container setup
├── README.md                 # Instructions to set up and run the project
└── SEED_URLS/                # Directory for storing seed URLs
    └── sample_source.json     # Sample listing seed file 
└──LISTING/                   #listing crawled data dir
└──PRODUCT/                   # product data dir
└── dep/                # Directory for chromediver
    └── chromedriver
    
```
## Prerequisites
Ensure you have the following installed:


Python 3.x
Docker (if you want to run the script inside a Docker container)
virtualenv (for running manually)
## Setup Instructions
# 1. Using a Virtual Environment
## Step 1: Install virtualenv
If you don't have virtualenv installed, install it using pip:

```Bash
pip install virtualenv
```
## Step 2: Create a Virtual Environment
In your project directory, create a virtual environment:

```Bash
virtualenv venv
```
## Step 3: Activate the Virtual Environment
Activate the virtual environment:

For macOS/Linux:

```Bash
source venv/bin/activate
```
For Windows:

```Bash
.\venv\Scripts\activate
```
## Step 4: Install Required Dependencies
With the virtual environment activated, install the required dependencies:

```Bash
pip install -r requirements.txt
```
## Step 5: Running the Scraper
To run the scraper, use the following commands:

For Listing Crawl:

```Bash
python3 crawler.py --source_name Steamcommunity-US --seed_file steamcommunity_listing_seed.json --threads 1 --no_pages 50 --crawl_type listing
```
For Product Crawl (after running the listing crawl):

```Bash
python3 crawler.py --source_name Steamcommunity-US --seed_file steamcommunity_us_listing_data_20240914.json --threads 1 --no_pages 3 --crawl_type product
```
## Step 6: Deactivate the Virtual Environment
When you're done, deactivate the virtual environment by running:

```Bash
deactivate
```
# 2. Using Docker
## Step 1: Build the Docker Image
Navigate to the directory where your Dockerfile is located, and build the Docker image:

```Bash
docker build -t web_scraper_image .
```
Step 2: Run the Scraper Inside Docker
Run the scraper using the following commands:

For Listing Crawl:

```Bash
docker run --rm -v $(pwd):/app web_scraper_image python3 crawler.py --source_name Steamcommunity-US --seed_file steamcommunity_listing_seed.json --threads 1 --no_pages 50 --crawl_type listing
```
For Product Crawl (after running the listing crawl):

```Bash
docker run --rm -v $(pwd):/app web_scraper_image python3 crawler.py --source_name Steamcommunity-US --seed_file steamcommunity_us_listing_data_20240914.json --threads 1 --no_pages 3 --crawl_type product
```
## Explanation:
+ --rm: Automatically removes the container after it exits.
+ -v $(pwd):/app: Mounts the current directory to the /app directory inside the container, making the files accessible on your machine.
## Directory Structure
+ SEED_URLS: Contains the seed URLs for scraping.
+ PAGEHTML: Stores the HTML pages downloaded from the URLs.
+ LISTING: Contains the listing data.
+ PRODUCT: Contains the scraped product details.
+ config.yaml: Configuration file with XPaths and scraping rules.
## Additional Notes
Run the listing crawl first to gather product URLs before running the product crawl.
