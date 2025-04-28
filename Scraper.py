import requests
from bs4 import BeautifulSoup
from lxml import etree
import os
import pandas as pd

def fetch_and_save_card_offers(url, headers, output_file):
    page = 0
    base_url = 'https://www.vipio.com'
    while True:
        params = {"order": "popularity", "page": page} if page > 0 else None
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to fetch page {page}: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select('a.card.card-offer')

        if not cards:
            print(f"No offers found on page {page}. Ending search.")
            break

        with open(output_file, "a", encoding="utf-8") as file:
            for card in cards:
                if "href" in card.attrs:
                    href = base_url + card["href"]
                    file.write(f"{href}\n")

        print(f"Page {page}: Appended {len(cards)} offers to {output_file}.")
        page += 1

    print(f"All offers have been saved to {output_file}.")


def extract_data_from_page(url):
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        tree = etree.HTML(response.text)

        # Extract details from the page
        hotel_name = tree.xpath('//span[@class="offer-title"]/text()')
        hotel_name = hotel_name[0].strip() if hotel_name else "N/A"

        address = tree.xpath('(//ul[@class="list horizontal divider small"]/li)[1]/text()')
        address = address[0].strip() if address else "N/A"
        parts = address.split(",")
        location = parts[0].strip() if len(parts) > 0 else "N/A"
        city = parts[1].strip() if len(parts) > 1 else "N/A"
        country = parts[2].strip() if len(parts) > 2 else "N/A"

        attributes = tree.xpath('//ul[@class="list horizontal"]/li/text()')
        attributes = [attr.strip() for attr in attributes if attr.strip()]
        features = ", ".join(attributes)

        rate_per_night = tree.xpath('//div[@class="card-head"]//span[@class="from-price"]/text()')
        rate_per_night = rate_per_night[0].strip() if rate_per_night else "N/A"

        return [
            hotel_name,
            address,
            location,
            city,
            country,
            rate_per_night,
            features,
            url,
        ]

    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
        return []
    except Exception as e:
        print(f"Error extracting data: {e}")
        return []
def save_data(all_data):
    file_name = "vipio_offers.xlsx"
    old_data = pd.DataFrame()  # Initialize old_data to an empty DataFrame

    if os.path.exists(file_name):
        old_data = pd.read_excel(file_name)

    if all_data:
        df = pd.DataFrame(
            all_data,
            columns=[
                "Hotel Name",
                "Address",
                "Location",
                "City",
                "Country",
                "Rate per Night",
                "Features",
                "URL",
            ],
        )
        if not old_data.empty:  # Check if old_data is not empty
            df = pd.concat([old_data, df], ignore_index=True)
        df.to_excel(file_name, index=False)
        print("Data saved to 'vipio_offers.xlsx'.")

def main():
    url = "https://www.vipio.com/en/a-special-stay/"
    headers = {
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }
    output_file = "offers.csv"
    rename_file = "old_offers.csv"
    output_data = "vipio_offers.xlsx"
    output_rename = "vipio_offers_old.xlsx"
    
    # Step 0: Remove existing output files and rename old ones if needed
    if os.path.exists(output_file):
        if os.path.exists(rename_file):
            os.remove(rename_file)
        os.rename(output_file , 'old_offers.csv')
        print(f"Removed existing {output_file}.")

    if os.path.exists(output_data):
        if os.path.exists(output_rename):
            os.remove(output_rename)
        os.rename(output_data , output_rename)
        print(f"Removed existing {output_data}.")
        

    # Step 1: Fetch and save offer URLs
    fetch_and_save_card_offers(url, headers, output_file)

    # Step 2: Read URLs from the file
    try:
        urls = pd.read_csv(output_file, header=None, names=["URL"])
    except FileNotFoundError:
        print(f"Error: {output_file} not found.")
        return

    # Step 3: Extract data for each URL
    all_data = []
    for i, row in urls.iterrows():
        url = row["URL"]
        print(f"Extracting data {i + 1} from: {url}")
        data = extract_data_from_page(url)
        if data:  # Only append if data extraction was successful
            print(data)
            all_data.append(data)
            if len(all_data) % 100 == 0:
                save_data(all_data)
                all_data = [] 
    if all_data: #
        save_data(all_data)

if __name__ == "__main__":
    main()
