import json
from urllib.error import URLError

from flask import Flask, render_template, request

from logging_config import get_logger
from tvmaze_api import load_config, search_shows


app = Flask(__name__)
logger = get_logger()


@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    shows = []
    error_message = ""
    searched = request.method == "POST"
    minimum_rating = 0.0
    include_unrated = False
    rating_options = [0, 5, 6, 7, 8, 9, 10]

    try:
        config = load_config()
        minimum_rating = config.minimum_rating
        if minimum_rating not in rating_options:
            rating_options.append(minimum_rating)
            rating_options.sort()

        if searched:
            query = request.form.get("query", "").strip()
            include_unrated = request.form.get("include_unrated") == "on"
            if not query:
                error_message = "Enter a show name to search."
            else:
                submitted_rating = request.form.get("minimum_rating", "")
                if submitted_rating:
                    minimum_rating = float(submitted_rating)
                if not 0 <= minimum_rating <= 10:
                    raise ValueError("Minimum rating must be between 0 and 10.")
                shows = search_shows(query, minimum_rating, include_unrated)
                logger.info("Web search completed; returned %d results", len(shows))
    except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
        logger.exception("Web search failed")
        error_message = str(error) if isinstance(error, ValueError) else (
            "TVMaze could not complete the search. Please try again."
        )

    return render_template(
        "index.html",
        query=query,
        shows=shows,
        searched=searched,
        error_message=error_message,
        minimum_rating=minimum_rating,
        rating_options=rating_options,
        include_unrated=include_unrated,
    )


if __name__ == "__main__":
    app.run(debug=False)
