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
    setCameraReady(false);

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

        await new Promise((resolve) => {
          if (videoRef.current.readyState >= 2) {
            resolve();
          } else {
            videoRef.current.onloadedmetadata = resolve;
          }
        });

        await videoRef.current.play();
      }

      setCameraReady(true);
    } catch (err) {
      console.error("CAMERA START ERROR:", err);

      setCameraReady(false);

      if (err.name === "NotAllowedError") {
        setError(
          "Camera permission was denied. Please allow camera access in your browser."
        );
      } else if (err.name === "NotFoundError") {
        setError("No camera was found on this device.");
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
    console.log("=================================");
    console.log("RHYTHM: Capture button clicked");
    console.log("=================================");

    if (!videoRef.current || !canvasRef.current) {
      console.error("VIDEO OR CANVAS REF IS MISSING");
      setError("Camera is not ready. Please try again.");
      return;
    }

    if (!cameraReady) {
      console.error("CAMERA IS NOT READY");
      setError("Camera is not ready. Please try again.");
      return;
    }

    setCapturing(true);
    setError("");

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      console.log("Video dimensions:", {
        width: video.videoWidth,
        height: video.videoHeight,
      });

      if (!video.videoWidth || !video.videoHeight) {
        throw new Error(
          "Camera image is not ready yet. Please wait a moment and try again."
        );
      }

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const context = canvas.getContext("2d");

      if (!context) {
        throw new Error("Unable to create image canvas.");
      }

      context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
      );

      const image = canvas.toDataURL(
        "image/jpeg",
        0.85
      );

      console.log("Image captured successfully.");
      console.log("Image type:", image.substring(0, 30));
      console.log(
        "Image size:",
        Math.round(image.length / 1024),
        "KB"
      );

      /*
       * Stop the camera only after the image
       * has been successfully captured.
       */
      stopCamera();

      console.log(
        "Sending POST request to:",
        "/emotion/detect"
      );

      const response = await api.post(
        "/emotion/detect",
        {
          image: image,
        },
        {
          timeout: 120000,
        }
      );

      console.log(
        "Emotion API response:",
        response.data
      );

      if (!response.data?.success) {
        throw new Error(
          response.data?.message ||
            "Emotion detection failed."
        );
      }

      const detectedEmotion =
        response.data.emotion;

      const confidence =
        response.data.confidence;

      console.log(
        "Detected emotion:",
        detectedEmotion
      );

      console.log(
        "Confidence:",
        confidence
      );

      navigate("/recommendations", {
        state: {
          emotion: detectedEmotion,
          confidence: confidence,
        },
      });
    } catch (err) {
      console.error(
        "================================="
      );

      console.error(
        "RHYTHM EMOTION DETECTION ERROR"
      );

      console.error(
        "================================="
      );

      console.error("Error:", err);

      if (err.response) {
        console.error(
          "HTTP status:",
          err.response.status
        );

        console.error(
          "Server response:",
          err.response.data
        );
      }

      if (err.request) {
        console.error(
          "Request was created but no response was received."
        );
      }

      const message =
        err.response?.data?.message ||
        err.message ||
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

                <p>{error}</p>

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
        style={{
          display: "none",
        }}
      />
    </main>
  );
}
