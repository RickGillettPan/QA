import sys
import time
import textwrap


COLOR = sys.stdout.isatty()
RESET = "\033[0m"


def paint(text, color):
    # Keep redirected output readable by using color only in an interactive terminal.
    if COLOR:
        return f"\033[{color}m{text}{RESET}"
    return text


def banner(title):
    edge = "+" + "-" * 62 + "+"
    print(paint(edge, "36"))
    print(paint("|" + title.center(62) + "|", "1;36"))
    print(paint(edge, "36"))


def show_progress():
    print("\n  Retrieving simulated results")
    if not COLOR:
        time.sleep(0.8)
        print("  [####################] 100%\n")
        return
    for step in range(1, 6):
        filled = step * 4
        bar = "#" * filled + "-" * (20 - filled)
        print(f"\r  [{paint(bar, '32')}] {step * 20}%", end="", flush=True)
        time.sleep(0.16)
    print("\n")


def show_result(number, title, description):
    print(paint(f"  [{number:02}]  {title}", "1;33"))
    for line in textwrap.wrap(description, width=55):
        print(f"        {line}")
    print()


def main():
    banner("SEARCH SIMULATOR")
    print("  Explore a topic with a polished, simulated search experience.\n")
    try:
        prompt = "  Enter a topic to explore (for example, renewable energy): "
        search_term = input(paint(prompt, "1;36")).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Search cancelled.")
        return

    if not search_term:
        print(paint("\n  Please enter a search term and try again.", "31"))
        return

    print(f"\n  Searching for: {paint(search_term, '1;37')}")
    show_progress()

    results = [
        # These are example suggestions, not results fetched from the internet.
        ("Topic overview", f"A quick introduction to {search_term} and its key ideas."),
        ("Latest highlights", f"Notable themes and recent developments related to {search_term}."),
        ("Common questions", f"Questions people often ask when learning about {search_term}."),
    ]

    banner("SEARCH RESULTS")
    for number, (title, description) in enumerate(results, start=1):
        show_result(number, title, description)

    print(paint("  SUMMARY", "1;36"))
    print(f"  Query:    {search_term}")
    print(f"  Results:  {len(results)} simulated suggestions")
    print("  Source:   Demo content - no external data was accessed")
    print(paint("\n  Thanks for trying Search Simulator!", "32"))


if __name__ == "__main__":
    main()
