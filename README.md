# SearchDuper
A simple meta-search that queries different search engines and collates unique results in a csv file.
by Roberto Dillon (Adsumsoft)

SearchDuper is a simple meta-search python script that collates results from different search engines by using beautifulsoup4 for web scraping, 
re for parsing results and pandas to save unique results (no duplicates) in a CSV file. 

Example: 
> python searchduper.py -s "Your Search Query" -n 100

This will perform the search on Google, Bing, and Yahoo, retrieve the top 100 results from each, 
and save only the unique ones to a CSV file with a name based on the search query and the current date and time. 
By adjusting the -n parameter we can specify a different number of results (default is 50).

Basic help available with 
> python searchduper.py -h

Be sure you install the following libraries if needed:
> pip install requests beautifulsoup4 pandas argparse datetime re
