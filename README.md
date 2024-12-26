# SahibPy

SahibPy is a Python-based web scraping tool designed to extract job postings from sahibinden.com, a popular online classifieds platform in Turkey. It provides functionalities to search for listings based on keywords and date ranges, filter the results, and save the data to CSV files.

## Files

* `sahibpy.py`: This is the main script that provides a command-line interface for interacting with the scraper. It uses the `SahibindenScraper` class from `scraper.py` to perform the scraping and data manipulation.
* `scraper.py`: Contains the `SahibindenScraper` class, which implements the core web scraping logic. It uses `seleniumbase` to handle dynamic content and bypass Cloudflare protection.
* `requirements.txt`: Lists the project's dependencies, including `rich`, `seleniumbase`, `beautifulsoup4`, and `dataclasses`.
* `filtered_results.csv`: Stores the job postings after applying filters. This file is generated when the "Save to CSV" option is used after filtering.
* `original_results.csv`: Stores the raw job postings fetched from sahibinden.com. This file is generated when the "Save to CSV" option is used.
* `downloaded_files/`: This directory might contain files downloaded by `seleniumbase` during the scraping process.

## Dependencies

The project requires the following libraries, which can be installed using pip:

```bash
pip install -r requirements.txt
```

## Usage

1. **Running the script:**
    Execute the `sahibpy.py` script from your terminal:

    ```bash
    python sahibpy.py
    ```

2. **Available Commands:**
    The script provides a menu-driven interface with the following commands:

    *   **Search**: Allows you to search for job postings based on a query and a date range (Last 24 hours, Last 3 days, Last 7 days, Last 15 days, Last 30 days).
    *   **Filter Results**: Filters the current search results based on keywords, categories, and locations. You can choose to filter using a predefined list of common words to exclude or enter your own criteria.
    *   **Display Current Results**: Shows the current results, either the original search results or the filtered results if filters have been applied.
    *   **Save to CSV**: Saves the current results (original, filtered, or both) to CSV files.
    *   **Reset Filters**: Clears any applied filters, reverting to the original search results.
    *   **Exit**: Closes the script.

## Functionality Details

### Scraping with SeleniumBase

The `SahibindenScraper` class utilizes `seleniumbase` to automate a headless Chrome browser. This is necessary to handle the website's dynamic content and bypass Cloudflare's protection mechanisms.

### Data Extraction

The scraper extracts the following information for each job posting:

*   **Title**: The title of the job posting.
*   **Location**: The location of the job.
*   **Date**: The date the job was posted.
*   **URL**: The link to the job posting on sahibinden.com.

### Filtering

The filtering functionality allows users to refine the search results by excluding listings containing certain keywords (common words like 'kurye', 'gemi', etc. are excluded by default) and including specific categories or locations.

## Notes

*   The script attempts to bypass Cloudflare protection, which may introduce a slight delay at the beginning of the scraping process.
*   Ensure you have the necessary drivers for `seleniumbase` installed. `seleniumbase` should handle driver downloads automatically.

## Example Workflow

1. Run `python sahibpy.py`.
2. Choose "Search" and enter a job title (e.g., "Python Developer") and a date range.
3. If needed, choose "Filter Results" to narrow down the results.
4. Review the results using "Display Current Results".
5. Save the results to a CSV file using "Save to CSV".

This README provides a comprehensive overview of the SahibPy project, its functionalities, and how to use it.
