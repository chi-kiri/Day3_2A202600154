import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.telemetry.logger import logger

class MovieAPI:
    """
    API helper for TheMovieDB.org
    Handles movie queries based on genre, date, and other filters.
    """
    
    BASE_URL = "https://api.themoviedb.org/3"
    API_KEY = "79eb5f868743610d9bddd40d274eb15d"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        })
    
    def search_movies(self, query: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Search movies by title/query.
        
        Args:
            query: Movie title or keywords
            year: Optional release year filter
            
        Returns:
            Dict with movies list and metadata
        """
        try:
            endpoint = f"{self.BASE_URL}/search/movie"
            params = {
                "api_key": self.API_KEY,
                "query": query,
                "language": "en-US"
            }
            if year:
                params["primary_release_year"] = year
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.log_event("MOVIE_SEARCH", {
                "query": query,
                "year": year,
                "results_count": len(data.get("results", []))
            })
            
            return {
                "status": "success",
                "query": query,
                "results": data.get("results", []),
                "total_results": data.get("total_results", 0)
            }
        except Exception as e:
            logger.error(f"Movie search error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_movies_by_genre(self, genre_id: int, release_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get movies by genre ID.
        
        Args:
            genre_id: TheMovieDB genre ID
            release_date: Optional filter by release date (YYYY-MM-DD)
            
        Returns:
            Dict with movies list
        """
        try:
            endpoint = f"{self.BASE_URL}/discover/movie"
            params = {
                "api_key": self.API_KEY,
                "with_genres": genre_id,
                "language": "en-US",
                "sort_by": "popularity.desc"
            }
            
            if release_date:
                params["primary_release_date.gte"] = release_date
                params["primary_release_date.lte"] = release_date
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.log_event("GENRE_SEARCH", {
                "genre_id": genre_id,
                "release_date": release_date,
                "results_count": len(data.get("results", []))
            })
            
            return {
                "status": "success",
                "genre_id": genre_id,
                "date": release_date,
                "results": data.get("results", []),
                "total_results": data.get("total_results", 0)
            }
        except Exception as e:
            logger.error(f"Genre search error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_movie_recommendations(self, movie_id: int) -> Dict[str, Any]:
        """
        Get similar/recommended movies based on a movie ID.
        
        Args:
            movie_id: TheMovieDB movie ID
            
        Returns:
            Dict with recommendations
        """
        try:
            endpoint = f"{self.BASE_URL}/movie/{movie_id}/recommendations"
            params = {
                "api_key": self.API_KEY,
                "language": "en-US"
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.log_event("MOVIE_RECOMMEND", {"movie_id": movie_id, "results_count": len(data.get("results", []))})
            
            return {
                "status": "success",
                "results": data.get("results", []),
                "total_results": data.get("total_results", 0)
            }
        except Exception as e:
            logger.error(f"Movie recommendation error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific movie.
        
        Args:
            movie_id: TheMovieDB movie ID
            
        Returns:
            Dict with movie details
        """
        try:
            endpoint = f"{self.BASE_URL}/movie/{movie_id}"
            params = {
                "api_key": self.API_KEY,
                "language": "en-US"
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.log_event("MOVIE_DETAIL", {"movie_id": movie_id})
            
            return {
                "status": "success",
                "movie": data
            }
        except Exception as e:
            logger.error(f"Movie detail error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def format_search_results(self, results: List[Dict[str, Any]], limit: int = 5) -> str:
        """
        Format movie search results into readable text.
        
        Args:
            results: List of movie results
            limit: Max number to show
            
        Returns:
            Formatted string for display
        """
        if not results:
            return "No movies found."
        
        output = []
        for i, movie in enumerate(results[:limit], 1):
            title = movie.get("title", "Unknown")
            release_date = movie.get("release_date", "N/A")
            rating = movie.get("vote_average", "N/A")
            movie_id = movie.get("id", "N/A")
            output.append(
                f"{i}. {title} ({release_date}) [ID: {movie_id}] - Rating: {rating}/10"
            )
        
        return "\n".join(output)

# Global instance
movie_api = MovieAPI()
