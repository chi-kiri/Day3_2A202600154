from src.core.movie_api import movie_api

def search_movies(query: str) -> str:
    """Useful for searching movies by title. Argument is movie title."""
    # Split query and year if model provides it in string like "Inception, 2010"
    parts = [p.strip() for p in query.split(",")]
    title = parts[0].strip("'\"")
    year = None
    if len(parts) > 1:
        try:
            year = int(parts[1])
        except ValueError:
            pass
            
    result = movie_api.search_movies(title, year)
    if result["status"] == "success":
        return movie_api.format_search_results(result["results"], limit=5)
    return f"Error: {result.get('message', 'Unknown error')}"

def find_by_genre(genre_info: str) -> str:
    """Useful for finding movies by genre ID. Argument is genre_id (int)."""
    try:
        genre_id = int(genre_info.strip("'\""))
        result = movie_api.get_movies_by_genre(genre_id)
        if result["status"] == "success":
            return movie_api.format_search_results(result["results"], limit=5)
        return f"Error: {result.get('message', 'Unknown error')}"
    except ValueError:
        return "Error: Invalid genre ID. Must be an integer."

def get_details(movie_id: str) -> str:
    """Useful for getting full details of a movie. Argument is movie_id (int)."""
    try:
        m_id = int(movie_id.strip("'\""))
        result = movie_api.get_movie_details(m_id)
        if result["status"] == "success":
            movie = result["movie"]
            return f"""
Title: {movie.get('title')}
Release: {movie.get('release_date')}
Rating: {movie.get('vote_average')}/10
Overview: {movie.get('overview')}
"""
        return f"Error: {result.get('message', 'Unknown error')}"
    except ValueError:
        return "Error: Invalid movie ID. Must be an integer."

def get_movie_tools():
    return [
        {
            "name": "search_movies",
            "description": "Search for movies by title. Arg: 'title' or 'title, year'.",
            "func": search_movies
        },
        {
            "name": "find_by_genre",
            "description": "Find movies in a genre by ID. Arg: genre_id (int). Examples: 28 (Action), 35 (Comedy), 27 (Horror).",
            "func": find_by_genre
        },
        {
            "name": "get_details",
            "description": "Get plot and rating for a specific movie. Arg: movie_id (int).",
            "func": get_details
        }
    ]
