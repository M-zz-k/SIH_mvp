"""
OpenCV Image Preprocessing Pipeline for METROSCAN AI OCR
=========================================================

Preprocesses product label images prior to OCR text detection and recognition.
Includes:
  1. Grayscale conversion
  2. Contrast enhancement via CLAHE (Contrast Limited Adaptive Histogram Equalization)
  3. Orientation and deskew correction using OpenCV contour angle analysis
"""

import math
from typing import Tuple, Optional
import cv2
import numpy as np


def preprocess_image(
    image_input: str | np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    enable_deskew: bool = True,
) -> Tuple[np.ndarray, float]:
    """Preprocess an image for optimal OCR performance.

    Args:
        image_input: Path to the image file or an existing OpenCV BGR/grayscale numpy array.
        clip_limit: CLAHE contrast threshold limit.
        tile_grid_size: Grid size for CLAHE histogram equalization.
        enable_deskew: Whether to calculate and apply deskew angle correction.

    Returns:
        A tuple of (preprocessed_image_bgr_array, deskew_angle_degrees).
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            raise FileNotFoundError(f"Unable to read image file at path: {image_input}")
    elif isinstance(image_input, np.ndarray):
        img = image_input.copy()
    else:
        raise ValueError("image_input must be a file path string or a numpy ndarray")

    # Ensure image is 3-channel BGR for consistent processing & PaddleOCR input
    if len(img.shape) == 2:
        gray = img
        img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. CLAHE Contrast Enhancement
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced_gray = clahe.apply(gray)

    # Re-assemble BGR image with enhanced contrast
    enhanced_bgr = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)

    deskew_angle = 0.0
    if enable_deskew:
        deskew_angle = calculate_deskew_angle(enhanced_gray)
        if abs(deskew_angle) > 0.5 and abs(deskew_angle) < 45.0:
            enhanced_bgr = rotate_image(enhanced_bgr, deskew_angle)

    return enhanced_bgr, deskew_angle


def calculate_deskew_angle(gray_image: np.ndarray) -> float:
    """Calculate the tilt angle of text lines in a grayscale image.

    Args:
        gray_image: Grayscale numpy image array.

    Returns:
        Rotation angle in degrees needed to deskew the image.
    """
    try:
        # Otsu thresholding to separate text foreground
        _, thresh = cv2.threshold(
            gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # Get coordinates of non-zero pixels
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 10:
            return 0.0

        # Compute minimum area bounding rectangle
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]

        # Adjust angle to [-45, 45] range
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Clamp extreme values to prevent erroneous rotation
        if abs(angle) > 45.0:
            return 0.0

        return float(angle)
    except Exception:
        return 0.0


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate an image around its center by a given angle in degrees.

    Args:
        image: Image array (BGR or Grayscale).
        angle: Angle in degrees.

    Returns:
        Rotated image array.
    """
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated
