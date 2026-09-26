import { useEffect, useRef, useState } from "react";
import { LogOut, Camera as CameraIcon, RotateCcw } from "lucide-react";
import { useNavigate } from "react-router-dom";

import BrandMark from "../components/BrandMark";
import api from "../services/api";

export default function Camera() {
  const navigate = useNavigate();

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState("");
  const [capturing, setCapturing] = useState(false);

  useEffect(() => {
    startCamera();

    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    setError("");

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Camera access is not supported by this browser."
        );
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: {
            ideal: 1280,
          },
          height: {
            ideal: 720,
          },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setCameraReady(true);
    } catch (err) {
      console.error(err);

      setCameraReady(false);

      if (err.name === "NotAllowedError") {
        setError(
          "Camera permission was denied. Please allow camera access in your browser."
        );
      } else if (err.name === "NotFoundError") {
        setError(
          "No camera was found on this device."
        );
      } else {
        setError(
          "Unable to access your camera. Please check your browser permissions."
        );
      }
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });

      streamRef.current = null;
    }
  };

  const captureImage = async () => {
    if (!videoRef.current || !canvasRef.current) {
      return;
    }

    setCapturing(true);
    setError("");

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const context = canvas.getContext("2d");

      context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
      );

      const image = canvas.toDataURL(
        "image/jpeg",
        0.9
      );

      stopCamera();

      const response = await api.post(
        "/emotion/detect",
        {
          image,
        }
      );

      const detectedEmotion = response.data.emotion;
      const confidence = response.data.confidence;

      navigate("/recommendations", {
        state: {
          emotion: detectedEmotion,
          confidence,
        },
      });
    } catch (err) {
      console.error(err);

      const message =
        err.response?.data?.message ||
        "Unable to detect your emotion. Please try again.";

      setError(message);

      await startCamera();
    } finally {
      setCapturing(false);
    }
  };

  const handleLogout = () => {
    stopCamera();

    localStorage.removeItem("rhythm_token");
    localStorage.removeItem("rhythm_user");

    navigate("/login");
  };

  return (
    <main className="camera-page">

      {/* =========================
          TOP BAR
      ========================= */}

      <header className="camera-header">

        <BrandMark size="small" />

        <button
          className="camera-logout"
          onClick={handleLogout}
          type="button"
        >
          <LogOut size={16} />
          <span>Logout</span>
        </button>

      </header>

      {/* =========================
          MAIN CONTENT
      ========================= */}

      <section className="camera-content">

        <div className="camera-intro">

          <p className="camera-eyebrow">
            EMOTION CHECK
          </p>

          <h1>
            Let your mood
            <br />
            choose the music.
          </h1>

          <p className="camera-description">
            Look at the camera naturally. RHYTHM will
            analyze your expression and create a
            personalized music experience.
          </p>

        </div>

        {/* =========================
            CAMERA CARD
        ========================= */}

        <div className="camera-card">

          <div className="camera-preview">

            {!cameraReady && !error && (
              <div className="camera-status">
                <div className="camera-spinner" />

                <p>
                  Starting camera...
                </p>
              </div>
            )}

            {error && !cameraReady && (
              <div className="camera-status camera-status-error">

                <div className="camera-error-icon">
                  !
                </div>

                <p>
                  {error}
                </p>

                <button
                  type="button"
                  className="camera-retry"
                  onClick={startCamera}
                >
                  <RotateCcw size={15} />
                  Try again
                </button>

              </div>
            )}

            <video
              ref={videoRef}
              className={`camera-video ${
                cameraReady ? "visible" : ""
              }`}
              autoPlay
              muted
              playsInline
            />

            {cameraReady && (
              <>

                {/* Face guide */}

                <div className="face-guide">

                  <span className="corner top-left" />
                  <span className="corner top-right" />
                  <span className="corner bottom-left" />
                  <span className="corner bottom-right" />

                </div>

                <div className="camera-hint">
                  Position your face inside the frame
                </div>

              </>
            )}

          </div>

          {/* =========================
              CAMERA CONTROLS
          ========================= */}

          <div className="camera-controls">

            <div className="camera-control-text">

              <strong>
                Ready when you are
              </strong>

              <span>
                Keep your face clearly visible.
              </span>

            </div>

            <button
              type="button"
              className="capture-button"
              onClick={captureImage}
              disabled={!cameraReady || capturing}
            >

              <span className="capture-icon">
                <CameraIcon size={21} />
              </span>

              <span>
                {capturing
                  ? "Analyzing..."
                  : "Capture mood"}
              </span>

            </button>

          </div>

        </div>

        <p className="camera-privacy">
          Your camera is used only to detect your current
          facial expression for this recommendation session.
        </p>

      </section>

      <canvas
        ref={canvasRef}
        style={{ display: "none" }}
      />

    </main>
  );
}