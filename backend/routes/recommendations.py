from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from db import get_db
from models.user_model import find_user_by_id
from models.song_model import serialize_song


recommendation_bp = Blueprint(
    "recommendations",
    __name__,
    url_prefix="/api/recommendations",
)


# ==========================================================
# HELPERS
# ==========================================================

def normalize_list(values):
    """
    Convert a list of strings to lowercase,
    remove empty values and duplicates.
    """

    if not isinstance(values, list):
        return []

    result = []

    for value in values:
        if isinstance(value, str) and value.strip():
            normalized = value.strip().lower()

            if normalized not in result:
                result.append(normalized)

    return result


def calculate_song_score(song, emotion, favorite_genres, favorite_artists):
    """
    Calculate a simple recommendation score.

    This is NOT the final HGNN algorithm.
    It is the initial recommendation layer that we can
    replace with the trained graph model later.
    """

    score = 0

    song_moods = normalize_list(
        song.get("moods", [])
    )

    song_genre = song.get(
        "genre",
        ""
    ).strip().lower()

    song_artist = song.get(
        "artist",
        ""
    ).strip().lower()

    # ------------------------------------------------------
    # Emotion match
    # ------------------------------------------------------

    if emotion and emotion.lower() in song_moods:
        score += 50

    # ------------------------------------------------------
    # Favorite genre match
    # ------------------------------------------------------

    if song_genre in favorite_genres:
        score += 25

    # ------------------------------------------------------
    # Favorite artist match
    # ------------------------------------------------------

    if song_artist in favorite_artists:
        score += 25

    return score


def get_user_history(db, user_id):
    """
    Get the user's listening history.

    History will be stored in the user document as:

    "listening_history": [
        {
            "song_id": "...",
            "played_at": ...
        }
    ]

    """

    user = find_user_by_id(
        db,
        user_id
    )

    if not user:
        return []

    return user.get(
        "listening_history",
        []
    )


# ==========================================================
# MAIN RECOMMENDATION ENDPOINT
# ==========================================================

@recommendation_bp.post("")
@jwt_required()
def get_recommendations():

    # ------------------------------------------------------
    # Get logged-in user
    # ------------------------------------------------------

    user_id = get_jwt_identity()

    db = get_db()

    user = find_user_by_id(
        db,
        user_id
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    # ------------------------------------------------------
    # Read request
    # ------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    emotion = data.get(
        "emotion",
        "neutral"
    )

    if not isinstance(emotion, str):
        emotion = "neutral"

    emotion = emotion.strip().lower()

    # ------------------------------------------------------
    # User preferences
    # ------------------------------------------------------

    favorite_genres = normalize_list(
        user.get(
            "favorite_genres",
            []
        )
    )

    favorite_artists = normalize_list(
        user.get(
            "favorite_artists",
            []
        )
    )

    # ------------------------------------------------------
    # Get all songs
    # ------------------------------------------------------

    songs_cursor = db.songs.find({})

    songs = list(
        songs_cursor
    )

    # ------------------------------------------------------
    # Score songs
    # ------------------------------------------------------

    scored_songs = []

    for song in songs:

        score = calculate_song_score(
            song=song,
            emotion=emotion,
            favorite_genres=favorite_genres,
            favorite_artists=favorite_artists,
        )

        serialized = serialize_song(
            song
        )

        serialized["score"] = score

        scored_songs.append(
            serialized
        )

    # ------------------------------------------------------
    # Sort by recommendation score
    # ------------------------------------------------------

    scored_songs.sort(
        key=lambda song: song["score"],
        reverse=True
    )

    # ------------------------------------------------------
    # Recommended songs
    # ------------------------------------------------------

    recommended_songs = scored_songs[:10]

    # ------------------------------------------------------
    # Emotion-specific songs
    # ------------------------------------------------------

    emotion_songs = [
        song
        for song in scored_songs
        if emotion in [
            mood.lower()
            for mood in song.get(
                "moods",
                []
            )
        ]
    ][:10]

    # ------------------------------------------------------
    # Genre-based songs
    # ------------------------------------------------------

    genre_songs = [
        song
        for song in scored_songs
        if song.get(
            "genre",
            ""
        ).lower() in favorite_genres
    ][:10]

    # ------------------------------------------------------
    # Favorite artist songs
    # ------------------------------------------------------

    artist_songs = [
        song
        for song in scored_songs
        if song.get(
            "artist",
            ""
        ).lower() in favorite_artists
    ][:10]

    # ------------------------------------------------------
    # Listening history
    # ------------------------------------------------------

    listening_history = get_user_history(
        db,
        user_id
    )

    history_song_ids = [
        item.get("song_id")
        for item in listening_history
        if isinstance(item, dict)
    ]

    recent_songs = [
        song
        for song in scored_songs
        if song["id"] in history_song_ids
    ][:10]

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return jsonify({
        "success": True,

        "emotion": emotion,

        "preferences": {
            "favorite_genres": favorite_genres,
            "favorite_artists": favorite_artists,
        },

        "recommended": recommended_songs,

        "by_emotion": emotion_songs,

        "by_genre": genre_songs,

        "by_artist": artist_songs,

        "recently_played": recent_songs,
    }), 200