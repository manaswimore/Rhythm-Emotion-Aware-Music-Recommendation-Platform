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
    """
    Convert a frontend image data URL into an OpenCV image.
    """

    if not isinstance(image_data, str):
        raise ValueError("Image must be a base64 string.")

    image_data = image_data.strip()

    match = DATA_URL_PATTERN.match(image_data)

    if not match:
        raise ValueError(
            "Invalid image format. Expected a JPEG or PNG data URL."
        )

    encoded_data = match.group("data")

    try:
        image_bytes = base64.b64decode(
            encoded_data,
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            "Invalid base64 image data."
        ) from exc

    if not image_bytes:
        raise ValueError("The image data is empty.")

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise ValueError(
            "Unable to decode the uploaded image."
        )

    if image.size == 0:
        raise ValueError(
            "The uploaded image is empty."
        )

    return image


def detect_emotion(image_data: str):
    """
    Detect the dominant facial emotion from a base64 image.
    """

    image = decode_base64_image(image_data)

    # Basic image validation
    height, width = image.shape[:2]

    if width < 100 or height < 100:
        raise ValueError(
            "Image is too small. Please capture your face again."
        )

    try:
        results = DeepFace.analyze(
            img_path=image,
            actions=["emotion"],
            enforce_detection=True,
            detector_backend="opencv",
        )

    except Exception as exc:
        print(
            "DEEPFACE ERROR:",
            repr(exc),
            flush=True,
        )

        raise ValueError(
            "No detectable face was found. "
            "Please make sure your face is clearly visible, "
            "well lit, and centered in the camera."
        ) from exc

    if not results:
        raise ValueError(
            "No face was detected in the image."
        )

    # DeepFace normally returns a list.
    if isinstance(results, list):
        result = results[0]
    else:
        result = results

    if not isinstance(result, dict):
        raise ValueError(
            "Unexpected response from emotion detection."
        )

    emotion = result.get("dominant_emotion")

    emotions = result.get(
        "emotion",
        {},
    )

    if not emotion:
        raise ValueError(
            "Emotion detection did not return a dominant emotion."
        )

    confidence = emotions.get(
        emotion,
        0,
    )

    try:
        confidence = float(confidence) / 100
    except (TypeError, ValueError):
        confidence = 0

    return {
        "emotion": str(emotion).lower(),
        "confidence": round(
            confidence,
            4,
        ),
    }
