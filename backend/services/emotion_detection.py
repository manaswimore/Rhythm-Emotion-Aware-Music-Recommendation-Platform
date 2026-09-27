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


def prepare_image(image):
    """
    Normalize the camera image before face detection.

    Large browser captures are resized to keep OpenCV fast and
    improve detection consistency on the Render CPU instance.
    """
    height, width = image.shape[:2]

    max_dimension = 960

    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)

        image = cv2.resize(
            image,
            (
                max(1, int(width * scale)),
                max(1, int(height * scale)),
            ),
            interpolation=cv2.INTER_AREA,
        )

    return image


def build_face_cascade():
    cascade_path = (
        cv2.data.haarcascades
        + "haarcascade_frontalface_default.xml"
    )

    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        raise RuntimeError(
            "OpenCV face detector could not be loaded."
        )

    return face_cascade


def detect_face(image):
    """
    Detect the largest face.

    We try a few detection configurations because browser camera
    captures can vary with lighting, distance and face size.
    """
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    gray = cv2.equalizeHist(gray)

    face_cascade = build_face_cascade()

    detection_configs = [
        {
            "scaleFactor": 1.08,
            "minNeighbors": 4,
            "minSize": (60, 60),
        },
        {
            "scaleFactor": 1.10,
            "minNeighbors": 4,
            "minSize": (50, 50),
        },
        {
            "scaleFactor": 1.12,
            "minNeighbors": 3,
            "minSize": (40, 40),
        },
    ]

    faces = ()

    for config in detection_configs:
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=config["scaleFactor"],
            minNeighbors=config["minNeighbors"],
            minSize=config["minSize"],
        )

        print(
            "EMOTION: OpenCV detection attempt "
            f"{config} -> {len(faces)} face(s)",
            flush=True,
        )

        if len(faces) > 0:
            break

    if len(faces) == 0:
        raise ValueError(
            "No face detected. Please face the camera directly, "
            "move a little closer, and make sure your face is "
            "well lit."
        )

    x, y, w, h = max(
        faces,
        key=lambda face: face[2] * face[3],
    )

    padding = int(
        0.25 * max(w, h)
    )

    x1 = max(
        0,
        x - padding,
    )

    y1 = max(
        0,
        y - padding,
    )

    x2 = min(
        image.shape[1],
        x + w + padding,
    )

    y2 = min(
        image.shape[0],
        y + h + padding,
    )

    face = image[
        y1:y2,
        x1:x2,
    ]

    if face.size == 0:
        raise ValueError(
            "Unable to crop the detected face."
        )

    return face


def detect_emotion(image_data: str):
    image = decode_base64_image(
        image_data
    )

    original_height, original_width = (
        image.shape[:2]
    )

    print(
        "EMOTION: received image "
        f"{original_width}x{original_height}",
        flush=True,
    )

    if (
        original_width < 100
        or original_height < 100
    ):
        raise ValueError(
            "Image is too small. Please capture your "
            "face again."
        )

    image = prepare_image(image)

    height, width = image.shape[:2]

    print(
        "EMOTION: prepared image "
        f"{width}x{height}",
        flush=True,
    )

    print(
        "EMOTION: detecting face with OpenCV",
        flush=True,
    )

    face = detect_face(
        image
    )

    face_height, face_width = (
        face.shape[:2]
    )

    print(
        "EMOTION: face cropped "
        f"{face_width}x{face_height}",
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

        print(
            "EMOTION: DeepFace.analyze returned",
            flush=True,
        )

    except Exception as exc:
        print(
            "DEEPFACE ERROR:",
            repr(exc),
            flush=True,
        )

        raise RuntimeError(
            "Emotion analysis failed on the server."
        ) from exc

    if not result:
        raise RuntimeError(
            "Emotion detection returned no result."
        )

    result = (
        result[0]
        if isinstance(result, list)
        else result
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            "Unexpected response from DeepFace."
        )

    emotion = result.get(
        "dominant_emotion"
    )

    if not emotion:
        raise RuntimeError(
            "DeepFace did not return an emotion."
        )

    emotions = result.get(
        "emotion",
        {},
    )

    confidence = emotions.get(
        emotion,
        0,
    )

    try:
        confidence = (
            float(confidence)
            / 100
        )
    except (
        TypeError,
        ValueError,
    ):
        confidence = 0

    print(
        "EMOTION: detected "
        f"{emotion} "
        f"confidence={confidence:.4f}",
        flush=True,
    )

    return {
        "emotion": str(
            emotion
        ).lower(),
        "confidence": round(
            confidence,
            4,
        ),
    }
