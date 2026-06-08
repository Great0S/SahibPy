from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from scraper import SahibindenScraper

console = Console()


def main():
    console.print("[bold cyan]SahibPy Scraper Initializer[/bold cyan]")
    proxy = None
    if Confirm.ask("Do you want to use a proxy? (Helps bypass Cloudflare)", default=False):
        proxy = Prompt.ask("Enter proxy string ([dim]e.g. host:port or user:pass@host:port[/dim])")
    
    scraper = SahibindenScraper(proxy=proxy)
    
    try:
        while True:
            console.clear()
            menu_text = (
                "[bold cyan]1.[/bold cyan] Search\n"
                "[bold cyan]2.[/bold cyan] Filter Results\n"
                "[bold cyan]3.[/bold cyan] Display Current Results\n"
                "[bold cyan]4.[/bold cyan] Save to CSV\n"
                "[bold cyan]5.[/bold cyan] Reset Filters\n"
                "[bold cyan]6.[/bold cyan] Exit"
            )
            console.print(Panel(
                menu_text,
                title="[bold white]SahibPy Scraper[/bold white]",
                subtitle="[dim]Status: Ready[/dim]",
                border_style="bright_blue",
                expand=False,
                padding=(1, 2)
            ))
            
            console.print() # Spacer to prevent cursor from touching the border
            choice = Prompt.ask(
                "[bold yellow]❯ Selection[/bold yellow]",
                choices=["1", "2", "3", "4", "5", "6"],
                default="1"
            )
            
            if choice == "1":
                console.print("\n[bold yellow]>>> SEARCH MODE[/bold yellow]")
                search_query = Prompt.ask("Enter search query")
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
                console.print("\n[bold yellow]>>> FILTERING MODE[/bold yellow]")
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
                
                with console.status("[bold green]Applying filters...", spinner="dots"):
                    filtered = scraper.filter_results(data_to_filter, keywords, categories, locations)
                    scraper.filtered_data = filtered
                
                if filtered:
                    table = scraper.create_results_table(filtered, "Filtered Results")
                    console.print(table)
                else:
                    console.print("[red]No results match the filter criteria.[/red]")
            
            elif choice == "3":
                console.print("\n[bold yellow]>>> DISPLAYING RESULTS[/bold yellow]")
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
                console.print("\n[bold yellow]>>> CSV EXPORT[/bold yellow]")
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
                
                with console.status("[bold green]Writing CSV files...", spinner="dots"):
                    if save_choice == "1" and scraper.filtered_data:
                        scraper.save_to_csv(scraper.filtered_data, "filtered_results.csv")
                    elif save_choice == "2":
                        scraper.save_to_csv(scraper.original_data, "original_results.csv")
                    elif save_choice == "3":
                        scraper.save_to_csv(scraper.original_data, "original_results.csv")
                        if scraper.filtered_data:
                            scraper.save_to_csv(scraper.filtered_data, "filtered_results.csv")
            
            elif choice == "5":
                console.print("\n[bold yellow]>>> RESETTING FILTERS[/bold yellow]")
                scraper.filtered_data = []
                console.print("[green]Filters reset successfully.[/green]")
            
            elif choice == "6":
                console.print("[yellow]Thank you for using SahibPy Scraper![/yellow]")
                break
            
            if choice != "6":
                Prompt.ask("Press Enter to continue", default="")
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    main()