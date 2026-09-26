import time
import requests

from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from config import Config


# =========================================================
# SETTINGS
# =========================================================

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

SONGS_PER_MOOD = 105

COUNTRY = "IN"

SEARCH_LIMIT = 200

REQUEST_DELAY = 0.15


MOODS = [
    "happy",
    "sad",
    "angry",
    "fear",
    "disgust",
    "surprise",
    "neutral",
]


# =========================================================
# MOOD SEARCH TERMS
# =========================================================
#
# Hindi/Bollywood is prioritized.
#
# These are search themes rather than hard-coded songs.
# The iTunes catalog supplies the actual tracks.
# =========================================================

MOOD_SEARCH_TERMS = {

    "happy": [
        "Hindi happy songs",
        "Bollywood happy songs",
        "Hindi upbeat songs",
        "Hindi party songs",
        "Bollywood dance songs",
        "Hindi feel good songs",
        "Hindi celebration songs",
        "Indian pop happy songs",
        "Arijit Singh happy songs",
        "Neha Kakkar songs",
        "Badshah songs",
        "Diljit Dosanjh songs",
        "Jubin Nautiyal songs",
        "Shreya Ghoshal happy songs",
    ],

    "sad": [
        "Hindi sad songs",
        "Bollywood sad songs",
        "Hindi emotional songs",
        "Hindi heartbreak songs",
        "Hindi breakup songs",
        "Bollywood emotional songs",
        "Hindi soulful songs",
        "Arijit Singh sad songs",
        "Atif Aslam Hindi songs",
        "Jubin Nautiyal sad songs",
        "Shreya Ghoshal sad songs",
        "Mohit Chauhan emotional songs",
        "KK sad songs",
    ],

    "angry": [
        "Hindi angry songs",
        "Bollywood intense songs",
        "Hindi aggressive songs",
        "Hindi powerful songs",
        "Bollywood rock songs",
        "Hindi motivational songs",
        "Hindi high energy songs",
        "Bollywood action songs",
        "Hindi attitude songs",
        "Badshah attitude songs",
        "Yo Yo Honey Singh songs",
        "DIVINE songs",
        "Raftaar songs",
        "Emiway Bantai songs",
    ],

    "fear": [
        "Hindi dark songs",
        "Bollywood dark songs",
        "Hindi haunting songs",
        "Hindi mysterious songs",
        "Bollywood thriller songs",
        "Hindi suspense songs",
        "Hindi intense emotional songs",
        "Hindi eerie songs",
        "Indian dark pop songs",
        "Bollywood horror songs",
        "Hindi dramatic songs",
    ],

    "disgust": [
        "Hindi dark songs",
        "Hindi attitude songs",
        "Bollywood intense songs",
        "Hindi revenge songs",
        "Hindi betrayal songs",
        "Bollywood negative songs",
        "Hindi villain songs",
        "Hindi aggressive rap",
        "Indian hip hop attitude songs",
        "Hindi confrontation songs",
        "Bollywood action songs",
        "DIVINE songs",
        "Raftaar songs",
    ],

    "surprise": [
        "Hindi energetic songs",
        "Bollywood energetic songs",
        "Hindi upbeat songs",
        "Bollywood dance songs",
        "Hindi party songs",
        "Indian pop energetic songs",
        "Hindi celebration songs",
        "Bollywood festive songs",
        "Hindi catchy songs",
        "Hindi trending songs",
        "Arijit Singh songs",
        "Shreya Ghoshal songs",
        "Diljit Dosanjh songs",
        "Badshah songs",
    ],

    "neutral": [
        "Hindi chill songs",
        "Bollywood chill songs",
        "Hindi relaxing songs",
        "Hindi calm songs",
        "Indian acoustic songs",
        "Hindi soft songs",
        "Bollywood mellow songs",
        "Hindi lo-fi songs",
        "Hindi peaceful songs",
        "Indian indie songs",
        "Arijit Singh songs",
        "Mohit Chauhan songs",
        "Shreya Ghoshal songs",
        "Prateek Kuhad songs",
    ],
}


# =========================================================
# GENERIC FALLBACK SEARCHES
# =========================================================
#
# Used only when a particular mood doesn't reach 105.
#
# We still prioritize Indian/Hindi music.
# =========================================================

FALLBACK_SEARCH_TERMS = [
    "Hindi songs",
    "Bollywood songs",
    "Indian pop songs",
    "Hindi film songs",
    "Indian music",
    "Bollywood classics",
    "Hindi romantic songs",
    "Hindi melody songs",
    "Hindi acoustic songs",
    "Indian indie songs",
]


# =========================================================
# ITUNES SEARCH
# =========================================================

def search_itunes(term):
    """
    Search the iTunes catalog.
    """

    try:

        response = requests.get(
            ITUNES_SEARCH_URL,
            params={
                "term": term,
                "media": "music",
                "entity": "song",
                "country": COUNTRY,
                "limit": SEARCH_LIMIT,
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "results",
            []
        )

    except requests.RequestException as exc:

        print(
            f"Search failed for '{term}':"
        )

        print(exc)

        return []


# =========================================================
# NORMALIZE ITUNES RESULT
# =========================================================

def normalize_song(result, mood):
    """
    Convert iTunes result into our MongoDB schema.
    """

    track_id = result.get(
        "trackId"
    )

    title = result.get(
        "trackName"
    )

    artist = result.get(
        "artistName"
    )

    genre = result.get(
        "primaryGenreName",
        "Indian Music"
    )

    duration_ms = result.get(
        "trackTimeMillis"
    )

    artwork_url = result.get(
        "artworkUrl100"
    )

    preview_url = result.get(
        "previewUrl"
    )


    if not track_id:
        return None

    if not title:
        return None

    if not artist:
        return None


    # -----------------------------------------------------
    # Album artwork
    # -----------------------------------------------------

    if artwork_url:

        artwork_url = artwork_url.replace(
            "100x100",
            "600x600"
        )


    # -----------------------------------------------------
    # Duration
    # -----------------------------------------------------

    if duration_ms:

        total_seconds = int(
            duration_ms / 1000
        )

        minutes = total_seconds // 60

        seconds = total_seconds % 60

        duration = (
            f"{minutes}:"
            f"{seconds:02d}"
        )

    else:

        duration = ""


    return {
        "external_id": str(track_id),

        "title": title.strip(),

        "artist": artist.strip(),

        "genre": genre.strip(),

        "moods": [
            mood
        ],

        "duration": duration,

        "album_art": artwork_url,

        "preview_url": preview_url,
    }


# =========================================================
# COLLECT SONGS FOR MOOD
# =========================================================

def collect_songs_for_mood(
    mood,
    already_used_global,
):
    """
    Collect exactly SONGS_PER_MOOD songs
    for a particular emotion.
    """

    print()
    print("=" * 60)

    print(
        f"Collecting songs for: "
        f"{mood.upper()}"
    )

    print("=" * 60)


    songs = []

    seen_track_ids = set()


    # -----------------------------------------------------
    # First: mood-specific searches
    # -----------------------------------------------------

    search_terms = (
        MOOD_SEARCH_TERMS.get(
            mood,
            []
        )
    )


    for term in search_terms:

        if len(songs) >= SONGS_PER_MOOD:
            break


        print(
            f"Searching: {term}"
        )


        results = search_itunes(
            term
        )


        for result in results:

            if len(songs) >= SONGS_PER_MOOD:
                break


            track_id = result.get(
                "trackId"
            )


            if not track_id:
                continue


            # Don't duplicate inside this mood.
            if track_id in seen_track_ids:
                continue


            seen_track_ids.add(
                track_id
            )


            song = normalize_song(
                result,
                mood
            )


            if not song:
                continue


            # Prefer Hindi/Indian music.
            language_score = calculate_indian_score(
                result
            )


            # Add song.
            song["_language_score"] = (
                language_score
            )


            songs.append(
                song
            )


        time.sleep(
            REQUEST_DELAY
        )


    # -----------------------------------------------------
    # Sort Indian/Hindi music first
    # -----------------------------------------------------

    songs.sort(
        key=lambda item:
            item.get(
                "_language_score",
                0
            ),
        reverse=True
    )


    # -----------------------------------------------------
    # If we don't have 105, use fallback searches.
    # -----------------------------------------------------

    if len(songs) < SONGS_PER_MOOD:

        print()
        print(
            f"{mood}: "
            f"Only {len(songs)} found."
        )

        print(
            "Using Hindi/Indian fallback searches..."
        )


        for term in FALLBACK_SEARCH_TERMS:

            if len(songs) >= SONGS_PER_MOOD:
                break


            print(
                f"Fallback: {term}"
            )


            results = search_itunes(
                term
            )


            for result in results:

                if len(songs) >= SONGS_PER_MOOD:
                    break


                track_id = result.get(
                    "trackId"
                )


                if not track_id:
                    continue


                if track_id in seen_track_ids:
                    continue


                seen_track_ids.add(
                    track_id
                )


                song = normalize_song(
                    result,
                    mood
                )


                if not song:
                    continue


                song["_language_score"] = (
                    calculate_indian_score(
                        result
                    )
                )


                songs.append(
                    song
                )


            time.sleep(
                REQUEST_DELAY
            )


    # -----------------------------------------------------
    # Remove temporary field
    # -----------------------------------------------------

    for song in songs:

        song.pop(
            "_language_score",
            None
        )


    # -----------------------------------------------------
    # Final validation
    # -----------------------------------------------------

    if len(songs) < SONGS_PER_MOOD:

        raise RuntimeError(
            f"Could not collect "
            f"{SONGS_PER_MOOD} songs "
            f"for mood '{mood}'. "
            f"Only found {len(songs)}."
        )


    # -----------------------------------------------------
    # Limit to exactly 105
    # -----------------------------------------------------

    songs = songs[
        :SONGS_PER_MOOD
    ]


    print()
    print(
        f"✓ {mood.upper()}: "
        f"{len(songs)} songs collected"
    )


    return songs


# =========================================================
# INDIAN MUSIC SCORE
# =========================================================

def calculate_indian_score(result):
    """
    Gives preference to Indian/Hindi music.
    """

    score = 0


    text_parts = [

        result.get(
            "artistName",
            ""
        ),

        result.get(
            "trackName",
            ""
        ),

        result.get(
            "collectionName",
            ""
        ),

        result.get(
            "primaryGenreName",
            ""
        ),

    ]


    text = " ".join(
        text_parts
    ).lower()


    indian_keywords = [

        "hindi",

        "bollywood",

        "indian",

        "punjabi",

        "bhangra",

        "tamil",

        "telugu",

        "marathi",

        "bengali",

        "malayalam",

        "kannada",

        "gujarati",

        "rajasthani",

        "desi",

        "sufi",

    ]


    for keyword in indian_keywords:

        if keyword in text:
            score += 10


    genre = (
        result.get(
            "primaryGenreName",
            ""
        )
        .lower()
    )


    indian_genres = [

        "bollywood",

        "world",

        "indian",

        "regional indian",

        "punjabi",

    ]


    for genre_name in indian_genres:

        if genre_name in genre:
            score += 15


    return score


# =========================================================
# MERGE DUPLICATE TRACKS
# =========================================================
#
# A song can legitimately match multiple emotions.
#
# Example:
#
# "Kesariya"
# -> happy
# -> romantic
#
# But our 7 database categories are the DeepFace emotions.
#
# If the exact same track is selected for multiple emotions,
# we create separate emotion associations.
# =========================================================

def build_documents():
    """
    Build 105 entries for every emotion.
    """

    all_documents = []

    mood_counts = {}


    # -----------------------------------------------------
    # Collect each mood
    # -----------------------------------------------------

    for mood in MOODS:

        mood_songs = collect_songs_for_mood(
            mood,
            already_used_global=set()
        )


        mood_counts[mood] = len(
            mood_songs
        )


        for song in mood_songs:

            document = {
                "external_id": (
                    song["external_id"]
                ),

                "title": song["title"],

                "artist": song["artist"],

                "genre": song["genre"],

                "moods": [
                    mood
                ],

                "duration": song["duration"],

                "album_art": song["album_art"],

                "preview_url": song["preview_url"],

            }


            all_documents.append(
                document
            )


    # -----------------------------------------------------
    # Validate every mood
    # -----------------------------------------------------

    print()
    print("=" * 60)

    print(
        "MOOD COUNT VALIDATION"
    )

    print("=" * 60)


    for mood in MOODS:

        count = mood_counts.get(
            mood,
            0
        )


        print(
            f"{mood:<10} : {count}"
        )


        if count < SONGS_PER_MOOD:

            raise RuntimeError(
                f"{mood} contains only "
                f"{count} songs."
            )


    expected_total = (
        len(MOODS)
        * SONGS_PER_MOOD
    )


    if len(all_documents) != expected_total:

        raise RuntimeError(
            f"Expected "
            f"{expected_total} total "
            f"documents but got "
            f"{len(all_documents)}."
        )


    print()
    print(
        f"✓ Total entries: "
        f"{len(all_documents)}"
    )


    return all_documents


# =========================================================
# DATABASE
# =========================================================

def save_to_database(
    documents
):

    print()
    print(
        "Connecting to MongoDB..."
    )


    client = MongoClient(
        Config.MONGO_URI,
        serverSelectionTimeoutMS=5000,
    )


    client.admin.command(
        "ping"
    )


    db = client[
        Config.MONGO_DB
    ]


    print(
        "✓ MongoDB connected."
    )


    # -----------------------------------------------------
    # Clear existing songs
    # -----------------------------------------------------

    print()
    print(
        "Removing old song data..."
    )


    db.songs.delete_many({})


    # -----------------------------------------------------
    # Insert new songs
    # -----------------------------------------------------

    try:

        result = db.songs.insert_many(
            documents,
            ordered=False
        )


        print()
        print(
            f"✓ Inserted "
            f"{len(result.inserted_ids)} "
            f"song entries."
        )


    except BulkWriteError as exc:

        print()
        print(
            "Some documents could not "
            "be inserted."
        )

        print(exc.details)


    # -----------------------------------------------------
    # Indexes
    # -----------------------------------------------------

    db.songs.create_index(
        "moods"
    )

    db.songs.create_index(
        "artist"
    )

    db.songs.create_index(
        "genre"
    )

    db.songs.create_index(
        "external_id"
    )


    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    print()
    print(
        "=" * 60
    )

    print(
        "DATABASE STATISTICS"
    )

    print(
        "=" * 60
    )


    total = db.songs.count_documents({})

    print(
        f"Total songs: {total}"
    )


    for mood in MOODS:

        count = db.songs.count_documents(
            {
                "moods": mood
            }
        )

        print(
            f"{mood:<10} : {count}"
        )


    artwork_count = db.songs.count_documents(
        {
            "album_art": {
                "$ne": None
            }
        }
    )


    preview_count = db.songs.count_documents(
        {
            "preview_url": {
                "$ne": None
            }
        }
    )


    print()
    print(
        f"Album artwork: "
        f"{artwork_count}/{total}"
    )

    print(
        f"Audio previews: "
        f"{preview_count}/{total}"
    )


    client.close()


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 60)

    print(
        "RHYTHM SONG DATABASE BUILDER"
    )

    print("=" * 60)

    print()

    print(
        f"Target: "
        f"{SONGS_PER_MOOD} songs per emotion"
    )

    print(
        f"Emotions: "
        f"{len(MOODS)}"
    )

    print(
        f"Expected entries: "
        f"{SONGS_PER_MOOD * len(MOODS)}"
    )

    print()


    Config.validate()


    # -----------------------------------------------------
    # Build dataset
    # -----------------------------------------------------

    documents = build_documents()


    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_to_database(
        documents
    )


    print()
    print("=" * 60)

    print(
        "✓ RHYTHM DATABASE READY"
    )

    print("=" * 60)

    print()


if __name__ == "__main__":

    main()