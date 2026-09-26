import { useEffect, useRef, useState } from "react";

import {
  Heart,
  LogOut,
  Music2,
  Pause,
  Play,
  Sparkles,
} from "lucide-react";

import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import BrandMark from "../components/BrandMark";
import api from "../services/api";


/* =========================================================
   FORMAT EMOTION
========================================================= */

function formatEmotion(emotion) {

  if (!emotion) {
    return "Neutral";
  }

  return (
    emotion.charAt(0).toUpperCase() +
    emotion.slice(1)
  );
}


/* =========================================================
   SONG CARD
========================================================= */

function SongCard({
  song,
  featured = false,
  currentlyPlaying,
  onPlay,
}) {

  const [liked, setLiked] =
    useState(false);

  const isPlaying =
    currentlyPlaying === song.id;


  const handlePlay = () => {

    if (!song.preview_url) {
      return;
    }

    onPlay(song);
  };


  return (
    <article
      className={
        `song-card ${
          featured
            ? "song-card-featured"
            : ""
        }`
      }
    >

      {/* -------------------------------------------------
          ARTWORK
      ------------------------------------------------- */}

      <div className="song-art">

        {song.album_art ? (

          <img
            src={song.album_art}
            alt={`${song.title} album art`}
          />

        ) : (

          <div className="song-art-placeholder">

            <Music2 size={24} />

          </div>

        )}


        {/* PLAY BUTTON */}

        <button
          type="button"
          className="song-play"
          onClick={handlePlay}
          disabled={!song.preview_url}
          aria-label={
            isPlaying
              ? `Pause ${song.title}`
              : `Play ${song.title}`
          }
        >

          {isPlaying ? (

            <Pause
              size={15}
              fill="currentColor"
            />

          ) : (

            <Play
              size={15}
              fill="currentColor"
            />

          )}

        </button>

      </div>


      {/* -------------------------------------------------
          SONG INFO
      ------------------------------------------------- */}

      <div className="song-info">

        <h3>
          {song.title}
        </h3>

        <p>
          {song.artist}
        </p>

        <span>
          {song.genre}

          {song.duration
            ? ` · ${song.duration}`
            : ""}
        </span>

      </div>


      {/* -------------------------------------------------
          FAVORITE
      ------------------------------------------------- */}

      <button
        type="button"
        className={
          `song-like ${
            liked
              ? "liked"
              : ""
          }`
        }
        onClick={() =>
          setLiked(!liked)
        }
        aria-label={
          `Favorite ${song.title}`
        }
      >

        <Heart
          size={17}
          fill={
            liked
              ? "currentColor"
              : "none"
          }
        />

      </button>

    </article>
  );
}


/* =========================================================
   SONG SECTION
========================================================= */

function SongSection({
  title,
  subtitle,
  songs,
  currentlyPlaying,
  onPlay,
}) {

  if (
    !songs ||
    songs.length === 0
  ) {
    return null;
  }


  return (
    <section className="recommendation-section">

      <div className="section-heading">

        <div>

          <h2>
            {title}
          </h2>

          {subtitle && (

            <p>
              {subtitle}
            </p>

          )}

        </div>


        <span className="section-count">
          {songs.length}
        </span>

      </div>


      <div className="song-grid">

        {songs.map((song) => (

          <SongCard
            key={
              `${song.id}-${title}`
            }
            song={song}
            currentlyPlaying={
              currentlyPlaying
            }
            onPlay={onPlay}
          />

        ))}

      </div>

    </section>
  );
}


/* =========================================================
   RECOMMENDATIONS PAGE
========================================================= */

export default function Recommendations() {

  const location =
    useLocation();

  const navigate =
    useNavigate();


  /* -------------------------------------------------------
     AUDIO
  ------------------------------------------------------- */

  const audioRef =
    useRef(null);


  /* -------------------------------------------------------
     STATE
  ------------------------------------------------------- */

  const [data, setData] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [currentlyPlaying, setCurrentlyPlaying] =
    useState(null);


  /* -------------------------------------------------------
     EMOTION
  ------------------------------------------------------- */

  const emotion =
    location.state?.emotion ||
    "neutral";

  const confidence =
    location.state?.confidence ||
    0;


  /* =======================================================
     LOAD RECOMMENDATIONS
  ======================================================= */

  useEffect(() => {

    loadRecommendations();


    return () => {

      if (audioRef.current) {
        audioRef.current.pause();

        audioRef.current = null;
      }

    };

  }, []);


  const loadRecommendations =
    async () => {

      setLoading(true);

      setError("");


      try {

        const response =
          await api.post(
            "/recommendations",
            {
              emotion,
            }
          );


        setData(
          response.data
        );

      } catch (err) {

        console.error(err);


        if (
          err.response?.status ===
          401
        ) {

          localStorage.removeItem(
            "rhythm_token"
          );

          localStorage.removeItem(
            "rhythm_user"
          );

          navigate(
            "/login",
            {
              replace: true,
            }
          );

          return;
        }


        setError(
          err.response?.data?.message ||
          "Unable to load recommendations."
        );

      } finally {

        setLoading(false);

      }

    };


  /* =======================================================
     PLAY / PAUSE
  ======================================================= */

  const handlePlay =
    (song) => {

      if (!song.preview_url) {

        console.warn(
          "No preview available:",
          song.title
        );

        return;
      }


      /* ---------------------------------------------------
         SAME SONG
      --------------------------------------------------- */

      if (
        currentlyPlaying === song.id &&
        audioRef.current
      ) {

        audioRef.current.pause();

        setCurrentlyPlaying(null);

        return;
      }


      /* ---------------------------------------------------
         STOP PREVIOUS
      --------------------------------------------------- */

      if (audioRef.current) {

        audioRef.current.pause();

        audioRef.current = null;

      }


      /* ---------------------------------------------------
         CREATE AUDIO
      --------------------------------------------------- */

      const audio =
        new Audio(
          song.preview_url
        );


      audioRef.current =
        audio;


      /* ---------------------------------------------------
         EVENTS
      --------------------------------------------------- */

      audio.onended = () => {

        setCurrentlyPlaying(
          null
        );

      };


      audio.onerror = () => {

        console.error(
          "Audio preview could not be played."
        );

        setCurrentlyPlaying(
          null
        );

      };


      /* ---------------------------------------------------
         PLAY
      --------------------------------------------------- */

      audio
        .play()
        .then(() => {

          setCurrentlyPlaying(
            song.id
          );

        })
        .catch((err) => {

          console.error(
            "Audio playback failed:",
            err
          );

          setCurrentlyPlaying(
            null
          );

        });

    };


  /* =======================================================
     LOGOUT
  ======================================================= */

  const handleLogout =
    () => {

      if (audioRef.current) {

        audioRef.current.pause();

        audioRef.current = null;

      }


      localStorage.removeItem(
        "rhythm_token"
      );

      localStorage.removeItem(
        "rhythm_user"
      );


      navigate(
        "/login"
      );

    };


  /* =======================================================
     NEW MOOD
  ======================================================= */

  const handleNewMood =
    () => {

      if (audioRef.current) {

        audioRef.current.pause();

        audioRef.current = null;

      }

      setCurrentlyPlaying(
        null
      );

      navigate(
        "/camera"
      );

    };


  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {

    return (
      <main className="recommendations-page">

        <header className="recommendations-header">

          <BrandMark size="small" />

          <button
            type="button"
            className="recommendation-logout"
            onClick={
              handleLogout
            }
          >

            <LogOut size={16} />

            <span>
              Logout
            </span>

          </button>

        </header>


        <div className="recommendation-loading">

          <div className="recommendation-spinner" />

          <h2>
            Creating your music mood...
          </h2>

          <p>
            RHYTHM is finding songs that
            match how you're feeling.
          </p>

        </div>

      </main>
    );
  }


  /* =======================================================
     ERROR
  ======================================================= */

  if (error) {

    return (
      <main className="recommendations-page">

        <header className="recommendations-header">

          <BrandMark size="small" />

          <button
            type="button"
            className="recommendation-logout"
            onClick={
              handleLogout
            }
          >

            <LogOut size={16} />

            <span>
              Logout
            </span>

          </button>

        </header>


        <div className="recommendation-error">

          <div className="recommendation-error-icon">
            !
          </div>


          <h2>
            Something went wrong
          </h2>


          <p>
            {error}
          </p>


          <div className="recommendation-error-actions">

            <button
              type="button"
              onClick={
                loadRecommendations
              }
            >
              Try again
            </button>


            <button
              type="button"
              className="secondary"
              onClick={
                handleNewMood
              }
            >
              New mood
            </button>

          </div>

        </div>

      </main>
    );
  }


  /* =======================================================
     DATA
  ======================================================= */

  const recommended =
    data?.recommended || [];

  const byEmotion =
    data?.by_emotion || [];

  const byGenre =
    data?.by_genre || [];

  const byArtist =
    data?.by_artist || [];

  const recentlyPlayed =
    data?.recently_played || [];

  const preferences =
    data?.preferences || {};


  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <main className="recommendations-page">


      {/* =================================================
          HEADER
      ================================================= */}

      <header className="recommendations-header">

        <BrandMark size="small" />


        <div className="recommendation-header-actions">

          <button
            type="button"
            className="new-mood-button"
            onClick={
              handleNewMood
            }
          >

            <Sparkles size={15} />

            New mood

          </button>


          <button
            type="button"
            className="recommendation-logout"
            onClick={
              handleLogout
            }
          >

            <LogOut size={16} />

            <span>
              Logout
            </span>

          </button>

        </div>

      </header>


      {/* =================================================
          CONTENT
      ================================================= */}

      <div className="recommendations-container">


        {/* =================================================
            MOOD HERO
        ================================================= */}

        <section className="mood-hero">

          <div className="mood-hero-text">

            <p className="recommendation-eyebrow">
              YOUR MOOD TODAY
            </p>


            <h1>

              Feeling{" "}

              <span>
                {formatEmotion(
                  emotion
                )}
              </span>

            </h1>


            <p>
              We've selected music around
              your current mood and
              listening preferences.
            </p>

          </div>


          <div className="mood-confidence">

            <div className="mood-icon">

              <Music2 size={26} />

            </div>


            <div>

              <strong>

                {formatEmotion(
                  emotion
                )}

              </strong>


              <span>

                {Math.round(
                  confidence * 100
                )}

                % detection confidence

              </span>

            </div>

          </div>

        </section>


        {/* =================================================
            RECOMMENDED
        ================================================= */}

        {recommended.length > 0 && (

          <section className="recommendation-section featured-section">

            <div className="section-heading">

              <div>

                <h2>
                  Recommended for you
                </h2>

                <p>
                  A mix of your mood and
                  personal preferences.
                </p>

              </div>


              <span className="section-count">

                {recommended.length}

              </span>

            </div>


            <div className="featured-song-grid">

              {recommended
                .slice(0, 4)
                .map((song) => (

                  <SongCard
                    key={
                      `recommended-${song.id}`
                    }
                    song={song}
                    featured
                    currentlyPlaying={
                      currentlyPlaying
                    }
                    onPlay={
                      handlePlay
                    }
                  />

                ))}

            </div>

          </section>

        )}


        {/* =================================================
            EMOTION
        ================================================= */}

        <SongSection
          title={
            `Because you're feeling ${formatEmotion(
              emotion
            )}`
          }
          subtitle={
            "Songs selected according to your detected mood."
          }
          songs={
            byEmotion
          }
          currentlyPlaying={
            currentlyPlaying
          }
          onPlay={
            handlePlay
          }
        />


        {/* =================================================
            GENRES
        ================================================= */}

        <SongSection
          title="Based on your genres"
          subtitle={
            preferences.favorite_genres?.length
              ? preferences.favorite_genres.join(
                  " · "
                )
              : "Your preferred genres"
          }
          songs={
            byGenre
          }
          currentlyPlaying={
            currentlyPlaying
          }
          onPlay={
            handlePlay
          }
        />


        {/* =================================================
            ARTISTS
        ================================================= */}

        <SongSection
          title="Your favorite artists"
          subtitle={
            preferences.favorite_artists?.length
              ? preferences.favorite_artists.join(
                  " · "
                )
              : "Artists you listen to"
          }
          songs={
            byArtist
          }
          currentlyPlaying={
            currentlyPlaying
          }
          onPlay={
            handlePlay
          }
        />


        {/* =================================================
            RECENTLY PLAYED
        ================================================= */}

        <SongSection
          title="Recently played"
          subtitle={
            "Continue listening from your recent activity."
          }
          songs={
            recentlyPlayed
          }
          currentlyPlaying={
            currentlyPlaying
          }
          onPlay={
            handlePlay
          }
        />


        {/* =================================================
            EMPTY
        ================================================= */}

        {!recommended.length &&
          !byEmotion.length &&
          !byGenre.length &&
          !byArtist.length &&
          !recentlyPlayed.length && (

            <div className="recommendation-empty">

              <Music2 size={30} />


              <h2>
                Your music library is getting ready.
              </h2>


              <p>
                Add some favorite artists
                and genres to make your
                recommendations more personal.
              </p>


              <button
                type="button"
                onClick={
                  handleNewMood
                }
              >
                Detect a new mood
              </button>

            </div>

          )}

      </div>

    </main>
  );
}