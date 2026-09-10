"""
Test Image Generator for METROSCAN AI OCR Testing
==================================================

Generates synthetic product label images for local test verification:
  1. label_compliant.png — Complete, clear product label with all 4 declarations.
  2. label_low_confidence.png — Rotated label simulating tilted image upload.
  3. label_missing_fields.png — Label with missing manufacturer and incomplete data.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_test_label_image(
    output_path: str,
    title: str,
    lines: list[str],
    rotate_deg: float = 0.0,
    width: int = 600,
    height: int = 400,
):
    """Draw a synthetic product label image with text lines."""
    # Create white canvas
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw border card
    draw.rectangle([20, 20, width - 20, height - 20], outline=(50, 50, 50), width=3)

    # Use default PIL font
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        body_font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Draw Header
    draw.text((40, 40), title, fill=(0, 0, 128), font=title_font)
    draw.line([(40, 75), (width - 40, 75)], fill=(200, 200, 200), width=2)

    # Draw Text Lines
    curr_y = 100
    for line in lines:
        draw.text((40, curr_y), line, fill=(20, 20, 20), font=body_font)
        curr_y += 40

    # Convert to OpenCV numpy BGR
    img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    if abs(rotate_deg) > 0.1:
        (h, w) = img_np.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), rotate_deg, 1.0)
        img_np = cv2.warpAffine(img_np, M, (w, h), borderValue=(255, 255, 255))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img_np)
    return output_path


def generate_all_test_images(target_dir: str) -> list[str]:
    """Generate all test images into target_dir."""
    paths = []

    # 1. Compliant Label
    p1 = os.path.join(target_dir, "label_compliant.png")
    create_test_label_image(
        p1,
        title="TATA SALT IODIZED - 1 KG",
        lines=[
            "M.R.P.: Rs 28.00 (Incl. of all taxes)",
            "Net Quantity: 1 kg",
            "Manufactured by: Tata Chemicals Ltd, Mumbai 400001",
            "Best Before 24 Months from Mfg",
        ],
    )
    paths.append(p1)

    # 2. Tilted / Low Confidence Label
    p2 = os.path.join(target_dir, "label_low_confidence.png")
    create_test_label_image(
        p2,
        title="PARLE-G GOLD BISCUITS",
        lines=[
            "MRP ₹30.00",
            "Net Wt. 200g",
            "Mfd by: Parle Products Pvt Ltd",
            "Mfg Date: 12/2026",
        ],
        rotate_deg=4.5,
    )
    paths.append(p2)

    # 3. Missing Fields Label
    p3 = os.path.join(target_dir, "label_missing_fields.png")
    create_test_label_image(
        p3,
        title="LOCAL BRAND MUSTARD OIL",
        lines=[
            "Price: Rs 85",
            "Net Volume: 500ml",
            "Packed Date: 05/2026",
            # Manufacturer missing completely!
        ],
    )
    paths.append(p3)

    return paths


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "images")
    created = generate_all_test_images(out_dir)
    print(f"Generated {len(created)} test images in {out_dir}:")
    for p in created:
        print(f"  - {p}")
