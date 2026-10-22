import requests
from flask import Flask, render_template, request


TVMAZE_SEARCH_URL = "https://api.tvmaze.com/search/shows"
app = Flask(__name__)


def search_shows(query):
    response = requests.get(
        TVMAZE_SEARCH_URL,
        params={"q": query},
        timeout=10,
    )
    response.raise_for_status()

    shows = response.json()
    if not isinstance(shows, list):
        raise ValueError("TVMaze returned an unexpected response format.")

    return shows


def format_show_result(result):
    show = result.get("show", {})
    image = show.get("image") or {}
    return {
        "name": show.get("name", "Unknown title"),
        "premiered": show.get("premiered", "Premiere date unknown"),
        "genres": show.get("genres") or ["Unknown genre"],
        "status": show.get("status", "Status unknown"),
        "official_site": show.get("officialSite") or "#",
        "image": image.get("medium") or image.get("original") or "",
        "summary": show.get("summary") or "No summary available.",
    }


@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    results = []
    error_message = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if not query:
            error_message = "Please enter a search term."
        else:
            try:
                raw_results = search_shows(query)
                results = [format_show_result(item) for item in raw_results]
                if not results:
                    error_message = "No shows found."
            except requests.exceptions.HTTPError as error:
                error_message = f"TVMaze returned an HTTP error: {error}"
            except requests.exceptions.RequestException as error:
                error_message = f"Could not connect to TVMaze: {error}"
            except ValueError as error:
                error_message = f"Could not read TVMaze's response: {error}"

    return render_template("index.html", query=query, results=results, error_message=error_message)


if __name__ == "__main__":
    app.run(debug=True)
