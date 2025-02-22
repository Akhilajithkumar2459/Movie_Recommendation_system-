from flask import Flask, jsonify, render_template
import pickle
import pandas as pd
import requests

app = Flask(__name__)

API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
BASE_URL = "https://api.themoviedb.org/3"

# Load movie data safely
try:
    movies_dict = pickle.load(open('mov.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    print(f"✅ Loaded {len(movies)} movies from mov.pkl")
except FileNotFoundError:
    print("❌ mov.pkl not found! No movies available.")
    movies = pd.DataFrame(columns=["movie_id", "title"])
    similarity = None

# Fetch movie details (poster, release date, rating, overview)
def fetch_movie_details(movie_id):
    try:
        url = f"{BASE_URL}/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        data = requests.get(url).json()
        return {
            "poster": f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '')}" if data.get('poster_path') else "https://via.placeholder.com/200",
            "title": data.get("title", "Unknown"),
            "release_date": data.get("release_date", "N/A"),
            "rating": data.get("vote_average", "N/A"),
            "overview": data.get("overview", "No description available.")
        }
    except Exception as e:
        print(f"❌ Error fetching details for movie {movie_id}: {e}")
        return {
            "poster": "https://via.placeholder.com/200",
            "title": "Unknown",
            "release_date": "N/A",
            "rating": "N/A",
            "overview": "No description available."
        }

# API to send movies (only titles)
@app.route('/movies', methods=['GET'])
def get_movies():
    if movies.empty:
        return jsonify([])

    movie_list = [{"title": row["title"]} for _, row in movies.iterrows()]
    return jsonify(movie_list)

# API to fetch recommendations with details
@app.route('/recommend/<movie_title>', methods=['GET'])
def recommend_movies(movie_title):
    if similarity is None:
        return jsonify({"error": "Similarity data not available"}), 500

    try:
        movie_index = movies[movies['title'] == movie_title].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommendations = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            recommendations.append(fetch_movie_details(movie_id))

        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve homepage
@app.route('/')
def home():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
