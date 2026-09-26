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
    Convert a frontend data URL into an OpenCV image.
    """

    if not isinstance(image_data, str):
        raise ValueError("Image must be a base64 string.")

    match = DATA_URL_PATTERN.match(image_data.strip())

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

    return image


def detect_emotion(image_data: str):
    """
    Detect the dominant facial emotion from an image.
    """

    image = decode_base64_image(image_data)

    try:
        results = DeepFace.analyze(
            img_path=image,
            actions=["emotion"],
            enforce_detection=True,
            detector_backend="opencv",
        )

    except Exception as exc:
        raise ValueError(
            "No detectable face was found in the image."
        ) from exc

    if not results:
        raise ValueError(
            "No face was detected."
        )

    # DeepFace can return either a dictionary
    # or a list depending on the version/configuration.
    result = (
        results[0]
        if isinstance(results, list)
        else results
    )

    emotion = result.get("dominant_emotion")

    emotions = result.get("emotion", {})

    if not emotion:
        raise ValueError(
            "Emotion detection did not return a result."
        )

    confidence = emotions.get(
        emotion,
        0,
    )

    return {
        "emotion": emotion.lower(),
        "confidence": round(
            float(confidence) / 100,
            4,
        ),
    }