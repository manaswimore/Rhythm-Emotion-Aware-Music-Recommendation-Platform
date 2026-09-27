import requests

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


ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

EMOTION_SEARCH_TERMS = {
    "happy": "Hindi happy Bollywood songs",
    "sad": "Hindi sad Bollywood songs",
    "angry": "Hindi powerful Bollywood songs",
    "fear": "Hindi dark dramatic songs",
    "disgust": "Hindi intense attitude songs",
    "surprise": "Hindi energetic Bollywood songs",
    "neutral": "Hindi chill relaxing songs",
}


def normalize_list(values):
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
    score = 0

    song_moods = normalize_list(song.get("moods", []))

    song_genre = song.get("genre", "").strip().lower()
    song_artist = song.get("artist", "").strip().lower()

    if emotion and emotion.lower() in song_moods:
        score += 50

    if song_genre in favorite_genres:
        score += 25

    if song_artist in favorite_artists:
        score += 25

    return score


def get_user_history(db, user_id):
    user = find_user_by_id(db, user_id)

    if not user:
        return []

    return user.get("listening_history", [])


def get_live_itunes_songs(emotion, limit=10):
    """
    Get real catalog songs with artwork and playable preview URLs.

    This is used because the current prototype MongoDB records are
    placeholder records with null album_art/preview_url values.
    """

    term = EMOTION_SEARCH_TERMS.get(
        emotion,
        EMOTION_SEARCH_TERMS["neutral"],
    )

    try:
        response = requests.get(
            ITUNES_SEARCH_URL,
            params={
                "term": term,
                "media": "music",
                "entity": "song",
                "country": "IN",
                "limit": min(limit * 3, 50),
            },
            timeout=12,
        )

        response.raise_for_status()

        results = response.json().get("results", [])

    except requests.RequestException as exc:
        print(
            "iTunes recommendation search failed:",
            repr(exc),
            flush=True,
        )
        return []

    songs = []
    seen = set()

    for item in results:
        track_id = item.get("trackId")
        title = item.get("trackName")
        artist = item.get("artistName")

        if not track_id or not title or not artist:
            continue

        if track_id in seen:
            continue

        artwork = item.get("artworkUrl100")
        preview = item.get("previewUrl")

        # Only return tracks that can actually be displayed and played.
        if not artwork or not preview:
            continue

        artwork = artwork.replace(
            "100x100",
            "600x600",
        )

        duration_ms = item.get("trackTimeMillis", 0)

        if duration_ms:
            total_seconds = int(duration_ms / 1000)
            duration = (
                f"{total_seconds // 60}:"
                f"{total_seconds % 60:02d}"
            )
        else:
            duration = ""

        songs.append({
            "id": f"itunes-{track_id}",
            "external_id": str(track_id),
            "title": title.strip(),
            "artist": artist.strip(),
            "genre": item.get(
                "primaryGenreName",
                "Music",
            ),
            "moods": [emotion],
            "duration": duration,
            "album_art": artwork,
            "preview_url": preview,
            "score": 50,
        })

        seen.add(track_id)

        if len(songs) >= limit:
            break

    return songs


@recommendation_bp.post("")
@jwt_required()
def get_recommendations():

    user_id = get_jwt_identity()

    db = get_db()

    user = find_user_by_id(
        db,
        user_id,
    )

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found.",
        }), 404

    data = request.get_json(
        silent=True,
    ) or {}

    emotion = data.get(
        "emotion",
        "neutral",
    )

    if not isinstance(emotion, str):
        emotion = "neutral"

    emotion = emotion.strip().lower()

    favorite_genres = normalize_list(
        user.get(
            "favorite_genres",
            [],
        )
    )

    favorite_artists = normalize_list(
        user.get(
            "favorite_artists",
            [],
        )
    )

    songs = list(
        db.songs.find({})
    )

    scored_songs = []

    for song in songs:
        score = calculate_song_score(
            song=song,
            emotion=emotion,
            favorite_genres=favorite_genres,
            favorite_artists=favorite_artists,
        )

        serialized = serialize_song(song)
        serialized["score"] = score

        scored_songs.append(serialized)

    scored_songs.sort(
        key=lambda song: song["score"],
        reverse=True,
    )

    # The current Atlas prototype contains placeholder songs whose
    # artwork and preview URLs are null. Use real iTunes catalog data
    # when those assets are unavailable.
    has_playable_catalog = any(
        song.get("album_art") and song.get("preview_url")
        for song in scored_songs
    )

    if not has_playable_catalog:
        live_songs = get_live_itunes_songs(
            emotion,
            limit=10,
        )

        if live_songs:
            recommended_songs = live_songs[:10]
            emotion_songs = live_songs[:10]
        else:
            recommended_songs = scored_songs[:10]
            emotion_songs = [
                song
                for song in scored_songs
                if emotion in [
                    mood.lower()
                    for mood in song.get("moods", [])
                ]
            ][:10]
    else:
        recommended_songs = scored_songs[:10]

        emotion_songs = [
            song
            for song in scored_songs
            if emotion in [
                mood.lower()
                for mood in song.get("moods", [])
            ]
        ][:10]

    genre_songs = [
        song
        for song in scored_songs
        if song.get("genre", "").lower() in favorite_genres
    ][:10]

    artist_songs = [
        song
        for song in scored_songs
        if song.get("artist", "").lower() in favorite_artists
    ][:10]

    listening_history = get_user_history(
        db,
        user_id,
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
