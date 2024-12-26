from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from scraper import SahibindenScraper

console = Console()


def main():
    console.print(Panel(
        "[cyan]Welcome to SahibPy Scraper[/cyan]\n\n"
        "[yellow]Note: The script will attempt to bypass Cloudflare protection. "
        "This may take a few seconds.[/yellow]",
        title="Information",
        border_style="blue"
    ))
    
    scraper = SahibindenScraper()
    
    while True:
        console.print(Panel("""
        [cyan]Available Commands:[/cyan]
        1. Search
        2. Filter Results
        3. Display Current Results
        4. Save to CSV
        5. Reset Filters
        6. Exit
        """,
        title="Menu",
        border_style="cyan"))
        
        choice = Prompt.ask(
            "Enter your choice",
            choices=["1", "2", "3", "4", "5", "6"],
            default="1"
        )
        
        if choice == "1":
            search_query = Prompt.ask("\nEnter search query")
            results_date = Prompt.ask("Choose a date range:", 
            choices=["Last 24 hours", "Last 3 days", "Last 7 days", "Last 15 days", "Last 30 days"],
            default="Last 24 hours")
            
            results = scraper.fetch_search_results(search_query, results_date)
            
            if results:
                scraper.original_data = results
                scraper.filtered_data = []
                table = scraper.create_results_table(
                    results,
                    f"Search Results for '{search_query}'"
                )
                console.print(table)
            else:
                console.print("[red]No results found.[/red]")
        
        elif choice == "2":
            keywords = None
            categories = None
            locations = None

            if not scraper.original_data:
                console.print("[red]No search results to filter. Please search first.[/red]")
                continue
            
            console.print("""[cyan]Filtering Options:[/cyan]
                          1. Filter using common words.
                          2. Enter filter criteria.""")
            
            filter_choice = Prompt.ask(
                "Choose filter option",
                choices=["1", "2"],
                default="1"
            )
            if filter_choice == "2":
                keywords = Prompt.ask("Keywords to exclude (comma-separated)").split(",")
                categories = Prompt.ask("Categories to include (comma-separated)").split(",")
                locations = Prompt.ask("Locations to include (comma-separated)").split(",")
            
            data_to_filter = scraper.filtered_data if scraper.filtered_data else scraper.original_data
            filtered = scraper.filter_results(data_to_filter, keywords, categories, locations)
            scraper.filtered_data = filtered
            
            if filtered:
                table = scraper.create_results_table(filtered, "Filtered Results")
                console.print(table)
            else:
                console.print("[red]No results match the filter criteria.[/red]")
        
        elif choice == "3":
            if not scraper.original_data:
                console.print("[red]No results to display. Please search first.[/red]")
                continue
                
            data = scraper.filtered_data if scraper.filtered_data else scraper.original_data
            table = scraper.create_results_table(
                data,
                "Filtered Results" if scraper.filtered_data else "Original Results"
            )
            console.print(table)
        
        elif choice == "4":
            if not scraper.original_data:
                console.print("[red]No results to save. Please search first.[/red]")
                continue
                
            console.print("""
            [cyan]Save Options:[/cyan]
            1. Filtered data only
            2. Original data only
            3. Both (separate files)
            """)
            
            save_choice = Prompt.ask(
                "Save option",
                choices=["1", "2", "3"],
                default="1"
            )
            
            if save_choice == "1" and scraper.filtered_data:
                scraper.save_to_csv(scraper.filtered_data, "filtered_results.csv")
            elif save_choice == "2":
                scraper.save_to_csv(scraper.original_data, "original_results.csv")
            elif save_choice == "3":
                scraper.save_to_csv(scraper.original_data, "original_results.csv")
                if scraper.filtered_data:
                    scraper.save_to_csv(scraper.filtered_data, "filtered_results.csv")
        
        elif choice == "5":
            scraper.filtered_data = []
            console.print("[green]Filters reset successfully.[/green]")
        
        elif choice == "6":
            console.print("[yellow]Thank you for using SahibPy Scraper![/yellow]")
            break
        
        if choice != "6":
            if not Prompt.ask("\nPress Enter to continue..."):
                continue

if __name__ == "__main__":
    main()