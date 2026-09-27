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


def detect_emotion(image_data: str):
    image = decode_base64_image(image_data)
    height, width = image.shape[:2]

    if width < 100 or height < 100:
        raise ValueError(
            "Image is too small. Please capture your face again."
        )

    print(
        f"EMOTION: received image {width}x{height}",
        flush=True,
    )

    try:
        print("EMOTION: starting DeepFace.analyze", flush=True)

        results = DeepFace.analyze(
            img_path=image,
            actions=["emotion"],
            enforce_detection=True,
            detector_backend="opencv",
        )

        print("EMOTION: DeepFace.analyze returned", flush=True)

    except ValueError as exc:
        print(
            "DEEPFACE FACE DETECTION ERROR:",
            repr(exc),
            flush=True,
        )
        raise ValueError(
            "No detectable face was found. "
            "Please make sure your face is clearly visible, "
            "well lit, and centered in the camera."
        ) from exc

    except Exception as exc:
        print(
            "DEEPFACE RUNTIME ERROR:",
            repr(exc),
            flush=True,
        )
        raise RuntimeError(
            "Emotion detection service failed during DeepFace processing."
        ) from exc

    if not results:
        raise ValueError("No face was detected in the image.")

    result = results[0] if isinstance(results, list) else results

    if not isinstance(result, dict):
        raise RuntimeError("Unexpected response from emotion detection.")

    emotion = result.get("dominant_emotion")
    emotions = result.get("emotion", {})

    if not emotion:
        raise RuntimeError(
            "Emotion detection did not return a dominant emotion."
        )

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
