import time


def main():
    print("Welcome to the Search Simulator!")
    search_term = input("Enter a search term: ").strip()

    if not search_term:
        print("Please enter a search term.")
        return

    print(f"\nSimulating a search for: {search_term}")
    print("Retrieving data...")
    time.sleep(1)

    results = [
        f"Overview of {search_term}",
        f"Recent updates about {search_term}",
        f"Frequently asked questions: {search_term}",
    ]

    print("\nSearch summary")
    print(f"Search term: {search_term}")
    print("Retrieval status: Simulated (no external data was accessed)")
    print(f"Results found: {len(results)}")
    for number, result in enumerate(results, start=1):
        print(f"{number}. {result}")


if __name__ == "__main__":
    main()
