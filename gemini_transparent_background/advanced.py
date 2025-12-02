import cv2
import numpy as np
from typing import Optional, Tuple

def remove_background_advanced(
    image_path: str,
    output_path: str,
    despill_strength: float = 0.7,
    feather_amount: int = 5,
    erode_iterations: int = 0,
    dilate_iterations: int = 1,
    lower_green: Tuple[int, int, int] = (35, 100, 100), # Slightly wider range for initial detection
    upper_green: Tuple[int, int, int] = (85, 255, 255)
) -> None:
    """
    Removes green background using advanced techniques: edge detection,
    morphological operations, feathering, and despill.

    Args:
        image_path (str): Path to the input image.
        output_path (str): Path to save the output image.
        despill_strength (float): Strength of green spill removal (0.0 to 1.0).
        feather_amount (int): Amount of Gaussian blur for feathering edges (odd number).
        lower_green (Tuple[int, int, int]): Lower bound for green color in HSV.
        upper_green (Tuple[int, int, int]): Upper bound for green color in HSV.
    """
    # 1. Read image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found at {image_path}")

    # 2. Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 3. Create initial green mask
    lower_bound = np.array(lower_green)
    upper_bound = np.array(upper_green)
    mask = cv2.inRange(hsv, lower_bound, upper_bound)

    # 4. Morphological operations to clean up the mask
    # Erode to remove small noise (green spots in foreground)
    kernel = np.ones((3, 3), np.uint8)
    if erode_iterations > 0:
        mask = cv2.erode(mask, kernel, iterations=erode_iterations)
    
    # Dilate to ensure we cover all green edges
    if dilate_iterations > 0:
        mask = cv2.dilate(mask, kernel, iterations=dilate_iterations)

    # 5. Create Alpha Channel
    # Invert mask for alpha: 0 (transparent) for green, 255 (opaque) for foreground
    alpha = cv2.bitwise_not(mask)

    # 6. Feathering
    # Convert alpha to float for blurring
    alpha_float = alpha.astype(float) / 255.0
    # Blur the alpha channel to soften edges
    if feather_amount > 0:
        if feather_amount % 2 == 0:
            feather_amount += 1 # Must be odd
        alpha_float = cv2.GaussianBlur(alpha_float, (feather_amount, feather_amount), 0)
    
    # Expand alpha back to 0-255 range
    alpha_uint8 = (alpha_float * 255).astype(np.uint8)

    # 7. Despill (Green Spill Removal)
    # Work on the BGR image
    b, g, r = cv2.split(img)
    
    # Identify pixels that might have green spill (edges mainly)
    # We can use the edge of the mask or just apply to the whole image where Green is dominant
    # Simple despill logic: if G > max(R, B), reduce G
    
    # Create a mask for pixels where Green is dominant
    max_rb = np.maximum(r, b)
    green_excess = np.subtract(g, max_rb, dtype=np.int16) # Use int16 to avoid underflow
    green_excess = np.maximum(green_excess, 0) # Clamp negative values to 0
    
    # Only apply despill near the edges to preserve green objects if any (though prompt says no green in subject)
    # For safety, we can apply it where alpha is semi-transparent or globally if we assume no green subject.
    # The prompt says "Subject should not use green", so global despill is safer for edges but we should be careful.
    # Let's use the logic provided in the prompt:
    # edge_pixels = edge_only_mask > 0 (We can approximate this by looking at the dilated mask vs eroded mask, or just use the whole image since subject has no green)
    
    # Let's refine the despill mask to be more targeted if needed, but for now, global despill on green-dominant pixels is standard for green screen.
    # However, to strictly follow the "edge only" hint from the prompt:
    # "edge_pixels = edge_only_mask > 0"
    # Let's create an edge mask from the alpha channel (pixels that are not fully opaque and not fully transparent, plus some padding)
    
    # Actually, the prompt logic:
    # edge_pixels = edge_only_mask > 0
    # max_rb = np.maximum(r, b)
    # green_excess = g - max_rb
    # despill_mask = edge_pixels & (green_excess > 20)
    # ...
    
    # Let's define edge pixels as pixels that are close to the background.
    # We can use the dilated mask (background) - eroded mask (background) to find edges.
    # Or simply: pixels where we detected green (mask > 0) are background.
    # We want to despill the FOREGROUND pixels that are close to the green background.
    # So we dilate the green mask to overlap with the foreground edges.
    
    dilated_green_mask = cv2.dilate(mask, kernel, iterations=3)
    # The part of dilated_green_mask that is NOT in the original green mask is the edge of the foreground.
    # But simpler: just use the dilated green mask as the area to check for despill.
    # Because the original green mask is going to be transparent anyway.
    # So we only care about the pixels that will remain visible (alpha > 0).
    
    # Let's stick to the prompt's logic structure but adapt it to working code.
    # We will apply despill to the whole image where G > max(R, B) because the subject is guaranteed not to be green.
    # This is safer and more effective for general "green screen" removal where the subject doesn't contain the key color.
    
    despill_mask = (g > max_rb) & (green_excess > 20)
    
    # Apply despill
    if despill_strength > 0:
        # Calculate amount to subtract
        amount = (green_excess * despill_strength).astype(np.uint8)
        
        # Subtract from Green channel where mask is true
        g = np.where(despill_mask, g - amount, g)
        
        # Optional: Add the removed green to Red and Blue to preserve luminance (purple-ish cast removal)
        # r = np.where(despill_mask, r + amount // 2, r)
        # b = np.where(despill_mask, b + amount // 2, b)
        # The prompt didn't ask for luminance preservation, just subtraction.

    # Merge channels back
    img_despilled = cv2.merge((b, g, r))

    # 8. Convert to BGRA
    bgra = cv2.cvtColor(img_despilled, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha_uint8

    # 9. Save
    cv2.imwrite(output_path, bgra)
    print(f"Processed (Advanced): {image_path} -> {output_path}")
