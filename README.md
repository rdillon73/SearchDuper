# SearchDuper v.0.2.0
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

------
Major Improvements in v0.2.0:
1. Object-Oriented Design

Created a SearchDuper class for better organization and reusability
Added a SearchEngine class for cleaner configuration management
Separated concerns into logical methods

2. Better Error Handling & Logging

Added comprehensive logging with different levels (INFO, WARNING, ERROR)
Implemented retry logic with configurable attempts
Added proper exception handling throughout
Input validation for arguments

3. Enhanced URL Processing

Improved URL validation with proper parsing
Added URL cleaning to remove tracking parameters
Better filtering of unwanted domains and URLs
More robust regex patterns for URL extraction

4. Code Quality & Maintainability

Added comprehensive docstrings for all methods
Type hints for better code documentation
Used constants for configuration
Separated business logic from presentation
Added proper imports organization

5. Enhanced Features

Configurable timeout and retry settings
Better CSV output with additional metadata (search query, timestamp)
Safer filename generation
More informative console output with emojis
Enhanced command-line interface with examples

6. Performance & Reliability

Uses requests.Session() for connection pooling
Better memory management with sets for deduplication
More efficient URL processing
Proper resource cleanup

7. Security & Best Practices

Safer URL handling
Input sanitization for filenames
Proper encoding of search queries
Updated user agent string

Key Features Added:

Logging system for debugging and monitoring
Retry mechanism for failed requests
URL cleaning to remove tracking parameters
Enhanced CSV output with metadata
Better error messages and user feedback
Input validation and argument checking
Configurable timeouts and retry attempts
