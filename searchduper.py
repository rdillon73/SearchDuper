'''
SearchDuper v 0.1.0
by Roberto Dillon (Adsumsoft)

A simple meta-search script written in python that collates results from different search engines by using beautifulsoup4 for web scraping, 
re for parsing results and pandas to save unique results (no duplicates) in a CSV file. 

Example: 
> python searchduper.py -s "Your Search Query" -n 100

This will perform the search on Google, Bing, and Yahoo, retrieve the top 100 results from each, 
and save only the unique ones to a CSV file with a name based on the search query and the current date and time. 
By adjusting the -n parameter we can specify a different number of results (default is 50).

Basic help available with 
> python search_duper.py -h

Be sure you install the following libraries if needed:
> pip install requests beautifulsoup4 pandas argparse datetime re


'''

import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def print_intro():
    print("=========================================")
    print("=                                       =")
    print("=          SearchDuper v.0.1.0          =")
    print("=      Meta-Search w/out Duplicates     =")
    print("=           by Roberto Dillon           =")
    print("=     https://github.com/rdillon73      =") 
    print("=                                       =") 
    print("=========================================")

# Function to fetch search results from a search engine
def search(query, num_results=50, search_engine="google"):
    search_url = {
        "google": f"https://www.google.com/search?q={query}&num={num_results}",
        "bing": f"https://www.bing.com/search?q={query}&count={num_results}",
        "yahoo": f"https://search.yahoo.com/search?p={query}&n={num_results}",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    response = requests.get(search_url.get(search_engine, search_url["google"]), headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        links = set()  # Use a set to store unique links

        for link in soup.find_all("a", href=True):
            href = link.get("href")
            anchor_text = link.text

            # we need to parse a complex (and very messy) page of results and filter only the relevant links
            if href and anchor_text:
                #print(search_engine.lower());
                # Check if anchor text doesn't contain the search engine name
                if search_engine.lower() not in anchor_text.lower():
                    # Use a regular expression to extract URLs that start with "https"
                    url_match = re.search(r"https:\/\/\S+", href)
                    if url_match:
                        url = url_match.group(0)
                        # Check if the URL does not contain the search engine name (case-insensitive)
                        if not re.search(fr"{search_engine.lower()}\.\w+", url, re.I):
                            links.add(url)

        return list(links)
    else:
        print(f"Failed to retrieve results from {search_engine}. Status Code: {response.status_code}")
        return []



# Function to save search results to a CSV file
def save_to_csv(query, results):
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{query[:20]}_{current_datetime}.csv"
    df = pd.DataFrame(results, columns=["Search Results"])
    df.to_csv(file_name, index=False)
    print(f"Unique and relevant search results saved to {file_name}")


def main():
    print_intro();

    parser = argparse.ArgumentParser(description="Searches Google, Bing and Yahoo and saves unique results to a CSV file.")
    parser.add_argument("-s", "--search_query", required=True, help="Search query string")
    parser.add_argument("-n", "--num_results", type=int, default=50, help="Number of search results (default: 50)")

    args = parser.parse_args()

    query = args.search_query
    num_results = args.num_results
    print (f"Searching for {query} and {num_results} results per engine...")

    search_engines = ["google", "bing", "yahoo"]
    results = {}

    for engine in search_engines:
        results[engine] = search(query, num_results, engine)

    # Combine unique results from all search engines
    unique_results = set()
    for engine_results in results.values():
        unique_results.update(engine_results)

    save_to_csv(query, list(unique_results))

if __name__ == "__main__":
    main()
