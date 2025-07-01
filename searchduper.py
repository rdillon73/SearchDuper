"""
SearchDuper v 0.2.0
by Roberto Dillon

A meta-search script that collates results from multiple search engines,
removes duplicates, and saves unique results to a CSV file.

Usage:
    python searchduper.py -s "Your Search Query" -n 100
    python searchduper.py --search_query "machine learning" --num_results 75

Dependencies:
    pip install requests beautifulsoup4 pandas
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import quote_plus, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


class SearchEngine:
    """Configuration for individual search engines."""
    
    def __init__(self, name: str, url_template: str, result_selector: str = "a[href]"):
        self.name = name
        self.url_template = url_template
        self.result_selector = result_selector


class SearchDuper:
    """Meta-search engine that aggregates results from multiple sources."""
    
    # Search engine configurations
    SEARCH_ENGINES = {
        "google": SearchEngine(
            "google",
            "https://www.google.com/search?q={query}&num={num_results}"
        ),
        "bing": SearchEngine(
            "bing", 
            "https://www.bing.com/search?q={query}&count={num_results}"
        ),
        "yahoo": SearchEngine(
            "yahoo",
            "https://search.yahoo.com/search?p={query}&n={num_results}"
        )
    }
    
    # Common headers to mimic browser requests
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize SearchDuper.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate if a URL is properly formed and relevant.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and relevant
        """
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must be HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Filter out common unwanted domains
            unwanted_domains = {
                'google.com', 'bing.com', 'yahoo.com', 'search.yahoo.com',
                'accounts.google.com', 'support.google.com', 'policies.google.com'
            }
            
            domain = parsed.netloc.lower()
            if any(unwanted in domain for unwanted in unwanted_domains):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _extract_urls_from_page(self, html: str, engine_name: str) -> Set[str]:
        """
        Extract valid URLs from search results page.
        
        Args:
            html: HTML content of the page
            engine_name: Name of the search engine
            
        Returns:
            Set of unique, valid URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        urls = set()
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            anchor_text = link.get_text(strip=True)
            
            if not href or not anchor_text:
                continue
            
            # Skip links that contain the search engine name in anchor text
            if engine_name.lower() in anchor_text.lower():
                continue
            
            # Extract HTTPS URLs using regex
            url_match = re.search(r'https://[^\s<>"\']+', href)
            if url_match:
                url = url_match.group(0)
                
                # Clean up URL (remove tracking parameters, etc.)
                url = self._clean_url(url)
                
                if self._is_valid_url(url):
                    urls.add(url)
        
        return urls
    
    def _clean_url(self, url: str) -> str:
        """
        Clean URL by removing common tracking parameters.
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL
        """
        # Remove common tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
        
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Remove tracking parameters
            for param in tracking_params:
                query_params.pop(param, None)
            
            # Reconstruct URL
            new_query = urlencode(query_params, doseq=True)
            cleaned_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
            
            return cleaned_url
            
        except Exception:
            return url  # Return original if cleaning fails
    
    def search_engine(self, query: str, num_results: int, engine_name: str) -> List[str]:
        """
        Search a specific search engine.
        
        Args:
            query: Search query string
            num_results: Number of results to retrieve
            engine_name: Name of search engine
            
        Returns:
            List of unique URLs from search results
        """
        if engine_name not in self.SEARCH_ENGINES:
            self.logger.error(f"Unknown search engine: {engine_name}")
            return []
        
        engine = self.SEARCH_ENGINES[engine_name]
        encoded_query = quote_plus(query)
        search_url = engine.url_template.format(
            query=encoded_query, 
            num_results=num_results
        )
        
        self.logger.info(f"Searching {engine_name.title()} for: {query}")
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(search_url, timeout=self.timeout)
                response.raise_for_status()
                
                urls = self._extract_urls_from_page(response.text, engine_name)
                self.logger.info(f"Found {len(urls)} unique URLs from {engine_name.title()}")
                
                return list(urls)
                
            except requests.RequestException as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed for {engine_name}: {str(e)}"
                )
                if attempt == self.max_retries - 1:
                    self.logger.error(f"Failed to retrieve results from {engine_name}")
                    return []
    
    def search_all_engines(self, query: str, num_results: int) -> Dict[str, List[str]]:
        """
        Search all configured search engines.
        
        Args:
            query: Search query string
            num_results: Number of results per engine
            
        Returns:
            Dictionary mapping engine names to their results
        """
        results = {}
        
        for engine_name in self.SEARCH_ENGINES:
            results[engine_name] = self.search_engine(query, num_results, engine_name)
        
        return results
    
    def combine_unique_results(self, results: Dict[str, List[str]]) -> List[str]:
        """
        Combine results from all engines, removing duplicates.
        
        Args:
            results: Dictionary of results from each engine
            
        Returns:
            List of unique URLs
        """
        unique_urls = set()
        
        for engine_name, urls in results.items():
            self.logger.info(f"{engine_name.title()}: {len(urls)} results")
            unique_urls.update(urls)
        
        unique_list = list(unique_urls)
        self.logger.info(f"Total unique results: {len(unique_list)}")
        
        return unique_list
    
    def save_results_to_csv(self, query: str, results: List[str]) -> str:
        """
        Save search results to CSV file.
        
        Args:
            query: Original search query
            results: List of URLs to save
            
        Returns:
            Path to saved file
        """
        if not results:
            self.logger.warning("No results to save")
            return ""
        
        # Create safe filename
        safe_query = re.sub(r'[^\w\s-]', '', query)[:50]  # Remove special chars, limit length
        safe_query = re.sub(r'[-\s]+', '_', safe_query)  # Replace spaces/hyphens with underscores
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{safe_query}_{timestamp}.csv"
        
        # Create DataFrame and save
        df = pd.DataFrame({
            'URL': results,
            'Search_Query': [query] * len(results),
            'Retrieved_At': [datetime.now().isoformat()] * len(results)
        })
        
        try:
            df.to_csv(filename, index=False)
            self.logger.info(f"Results saved to: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {str(e)}")
            return ""
    
    def run_search(self, query: str, num_results: int) -> str:
        """
        Run complete search process.
        
        Args:
            query: Search query string
            num_results: Number of results per engine
            
        Returns:
            Path to saved CSV file
        """
        self.logger.info(f"Starting search for: '{query}' ({num_results} results per engine)")
        
        # Search all engines
        results = self.search_all_engines(query, num_results)
        
        # Combine unique results
        unique_results = self.combine_unique_results(results)
        
        # Save to CSV
        filename = self.save_results_to_csv(query, unique_results)
        
        return filename


def print_banner():
    """Print application banner."""
    print("=" * 50)
    print("=                                                =")
    print("=             SearchDuper v.0.2.0                =")
    print("=         Meta-Search w/out Duplicates           =")
    print("=            by Roberto Dillon                   =")
    print("=        https://github.com/rdillon73            =")
    print("=                                                =")
    print("=" * 50)


def main():
    """Main entry point."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Search multiple engines and save unique results to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python searchduper.py -s "artificial intelligence" -n 100
  python searchduper.py --search_query "python programming" --num_results 50
        """
    )
    
    parser.add_argument(
        "-s", "--search_query",
        required=True,
        help="Search query string"
    )
    
    parser.add_argument(
        "-n", "--num_results",
        type=int,
        default=50,
        help="Number of search results per engine (default: 50)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    
    parser.add_argument(
        "--max_retries",
        type=int,
        default=3,
        help="Maximum retry attempts (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.num_results <= 0:
        print("Error: Number of results must be positive")
        sys.exit(1)
    
    if not args.search_query.strip():
        print("Error: Search query cannot be empty")
        sys.exit(1)
    
    # Run search
    try:
        searcher = SearchDuper(timeout=args.timeout, max_retries=args.max_retries)
        filename = searcher.run_search(args.search_query.strip(), args.num_results)
        
        if filename:
            print(f"\n✅ Search completed successfully!")
            print(f"📁 Results saved to: {filename}")
        else:
            print("\n❌ Search failed or no results found")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Search interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()