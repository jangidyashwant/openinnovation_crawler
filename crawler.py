import argparse,os,json
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from helpers import load_urls_from_json, load_config_from_yaml, process_url_batch


try:
    BASE_DIR = os.path.dirname(__file__)
except Exception as E:
    BASE_DIR = os.getcwd()

BASE_DIR = os.path.abspath(BASE_DIR)
SEED_URLS_DIR = os.path.join(BASE_DIR, 'SEED_URLS')

if not os.path.isdir(SEED_URLS_DIR):
    os.makedirs(SEED_URLS_DIR)
PAGE_HTML_DIR = os.path.join(BASE_DIR, 'PAGEHTML')
if not os.path.isdir(PAGE_HTML_DIR):
    os.makedirs(PAGE_HTML_DIR)
LISTING_DATA_DIR = os.path.join(BASE_DIR, 'LISTING')
if not os.path.isdir(LISTING_DATA_DIR):
    os.makedirs(LISTING_DATA_DIR)

PRODUCT_DATA_DIR = os.path.join(BASE_DIR, 'PRODUCT')
if not os.path.isdir(PRODUCT_DATA_DIR):
    os.makedirs(PRODUCT_DATA_DIR)

def main(source_name, url_file_path, yaml_file_path, num_pages, num_threads, out_file_json, out_file_csv, crawl_type):
    urls = load_urls_from_json(url_file_path)
    config = load_config_from_yaml(yaml_file_path)
    batch_size = 20
    url_batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]
    all_product_data = []

    num_threads = max(1, min(num_threads, len(url_batches)))
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(process_url_batch, batch, num_pages, config, source_name, crawl_type) for batch in url_batches]
        for future in as_completed(futures):
            try:
                all_product_data.extend(future.result())
            except Exception as e:
                print(f"Error processing batch: {e}")

    with open(out_file_json, 'w', encoding="utf-8") as out_f:
        for p_data in all_product_data:
            out_f.write(json.dumps(p_data, ensure_ascii=False) + "\n")

    df = pd.DataFrame(all_product_data)
    df.to_csv(out_file_csv, index=False)
    print(f"Scraped {len(all_product_data)} products and saved to {out_file_csv}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl URLs and save HTML.')
    parser.add_argument('--source_name', type=str, required=True, help='Pass the source name which you want to scrape')
    parser.add_argument('--seed_file', type=str, required=True, help='Pass the seed file name')
    parser.add_argument('--threads', type=int, default=5, help='Number of threads to use (default: 5)')
    parser.add_argument('--no_pages', type=int, default=5, help='Number of pages to scrape')
    parser.add_argument('--crawl_type', type=str, required=True, help='Scrapper type (Requests or Selenium)')

    args = parser.parse_args()
    print(args)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    if args.crawl_type == "listing":
        url_file_path = os.path.join(SEED_URLS_DIR,args.source_name ,args.seed_file)
        s_name = args.source_name.lower().replace("-","_")
        out_file_folder = os.path.join(LISTING_DATA_DIR,timestamp,args.source_name)
        if not os.path.isdir(out_file_folder):
            os.makedirs(out_file_folder)
        out_file_json = os.path.join(out_file_folder,f"{s_name}_listing_data_{timestamp}.json" )
        out_file_csv = os.path.join(out_file_folder,f"{s_name}_listing_data_{timestamp}.csv" )
    
    if args.crawl_type == "product":
        url_file_path = os.path.join(LISTING_DATA_DIR,timestamp, args.source_name, args.seed_file)
        s_name = args.source_name.lower().replace("-","_")
        out_file_folder = os.path.join(PRODUCT_DATA_DIR,timestamp,args.source_name)
        if not os.path.isdir(out_file_folder):
            os.makedirs(out_file_folder)
        out_file_json = os.path.join(out_file_folder,f"{s_name}_product_data_{timestamp}.json" )
        out_file_csv = os.path.join(out_file_folder,f"{s_name}_product_data_{timestamp}.csv" )


    yaml_file_path = os.path.join(BASE_DIR,"config.yaml")

    main(args.source_name , url_file_path, yaml_file_path, args.no_pages, args.threads, out_file_json,out_file_csv ,args.crawl_type)
