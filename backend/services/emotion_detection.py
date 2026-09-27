import base64
import binascii
import re

import cv2
import numpy as np
from deepface import DeepFace


DATA_URL_PATTERN = re.compile(
    r"^data:image/(?P<format>jpeg|jpg|png);base64,(?P<data>.+)$",
    re.IGNORECASE,
)


def decode_base64_image(image_data: str):
    if not isinstance(image_data, str):
        raise ValueError("Image must be a base64 string.")

    image_data = image_data.strip()
    match = DATA_URL_PATTERN.match(image_data)

    if not match:
        raise ValueError(
            "Invalid image format. Expected a JPEG or PNG data URL."
        )

    try:
        image_bytes = base64.b64decode(
            match.group("data"),
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 image data.") from exc

    if not image_bytes:
        raise ValueError("The image data is empty.")

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None or image.size == 0:
        raise ValueError("Unable to decode the uploaded image.")

    return image


def detect_face(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    cascade_path = (
        cv2.data.haarcascades
        + "haarcascade_frontalface_default.xml"
    )

    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        raise RuntimeError("OpenCV face detector could not be loaded.")

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )

    if len(faces) == 0:
        raise ValueError(
            "No face detected. Please keep your face clearly visible "
            "and centered in the camera."
        )

    x, y, w, h = max(
        faces,
        key=lambda face: face[2] * face[3],
    )

    padding = int(0.25 * max(w, h))

    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(image.shape[1], x + w + padding)
    y2 = min(image.shape[0], y + h + padding)

    face = image[y1:y2, x1:x2]

    if face.size == 0:
        raise ValueError("Unable to crop the detected face.")

    return face


def detect_emotion(image_data: str):
    image = decode_base64_image(image_data)
    height, width = image.shape[:2]

    print(f"EMOTION: received image {width}x{height}", flush=True)

    if width < 100 or height < 100:
        raise ValueError(
            "Image is too small. Please capture your face again."
        )

    print("EMOTION: detecting face with OpenCV", flush=True)
    face = detect_face(image)

    face_height, face_width = face.shape[:2]
    print(
        f"EMOTION: face cropped {face_width}x{face_height}",
        flush=True,
    )

    try:
        print(
            "EMOTION: starting DeepFace emotion analysis",
            flush=True,
        )

        result = DeepFace.analyze(
            img_path=face,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend="skip",
        )

        print("EMOTION: DeepFace.analyze returned", flush=True)

    except Exception as exc:
        print("DEEPFACE ERROR:", repr(exc), flush=True)
        raise RuntimeError(
            "Emotion analysis failed on the server."
        ) from exc

    if not result:
        raise RuntimeError("Emotion detection returned no result.")

    result = result[0] if isinstance(result, list) else result

    if not isinstance(result, dict):
        raise RuntimeError("Unexpected response from DeepFace.")

    emotion = result.get("dominant_emotion")

    if not emotion:
        raise RuntimeError("DeepFace did not return an emotion.")

    emotions = result.get("emotion", {})
    confidence = emotions.get(emotion, 0)

    try:
        confidence = float(confidence) / 100
    except (TypeError, ValueError):
        confidence = 0

    print(
        f"EMOTION: detected {emotion} confidence={confidence:.4f}",
        flush=True,
    )

    return {
        "emotion": str(emotion).lower(),
        "confidence": round(confidence, 4),
    }
