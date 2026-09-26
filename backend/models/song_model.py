from datetime import datetime, timezone


def create_song(
    db,
    title,
    artist,
    genre,
    moods,
    duration,
    album_art=None,
    preview_url=None,
):
    now = datetime.now(timezone.utc)

    song = {
        "title": title.strip(),
        "artist": artist.strip(),
        "genre": genre.strip(),
        "moods": [
            mood.lower().strip()
            for mood in moods
        ],
        "duration": duration.strip(),
        "album_art": album_art,
        "preview_url": preview_url,
        "created_at": now,
        "updated_at": now,
    }

    result = db.songs.insert_one(song)

    song["_id"] = result.inserted_id

    return song


def serialize_song(song):
    return {
        "id": str(song["_id"]),
        "title": song.get("title", ""),
        "artist": song.get("artist", ""),
        "genre": song.get("genre", ""),
        "moods": song.get("moods", []),
        "duration": song.get("duration", ""),
        "album_art": song.get("album_art"),
        "preview_url": song.get("preview_url"),
    }


def find_songs_by_emotion(
    db,
    emotion,
    limit=10,
):
    songs = db.songs.find(
        {
            "moods": emotion.lower()
        }
    ).limit(limit)

    return [
        serialize_song(song)
        for song in songs
    ]


def find_songs_by_genres(
    db,
    genres,
    limit=10,
):
    if not genres:
        return []

    songs = db.songs.find(
        {
            "genre": {
                "$in": genres
            }
        }
    ).limit(limit)

    return [
        serialize_song(song)
        for song in songs
    ]


def find_songs_by_artists(
    db,
    artists,
    limit=10,
):
    if not artists:
        return []

    songs = db.songs.find(
        {
            "artist": {
                "$in": artists
            }
        }
    ).limit(limit)

    return [
        serialize_song(song)
        for song in songs
    ]