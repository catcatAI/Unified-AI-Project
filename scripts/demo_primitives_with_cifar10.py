"""Demo: Use primitives with CIFAR-10 images."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

from ai.multimodal.primitives import (
    Point, Line, Plane, DrawingInstructions, PrimitiveRenderer, PrimitiveLibrary, PrimitiveEncoder
)
from PIL import Image
import numpy as np


def main():
    """Demo primitives with CIFAR-10 images."""
    print("Primitives with CIFAR-10 Demo")
    print("=" * 50)
    
    # Load a CIFAR-10 image
    cifar_path = project_root / "data" / "multimodal" / "cifar10"
    if not cifar_path.exists():
        print("CIFAR-10 not found, skipping demo")
        return
    
    # Find first image
    for class_dir in cifar_path.iterdir():
        if class_dir.is_dir():
            for img_file in class_dir.glob("*.png"):
                print(f"Loading image: {img_file}")
                img = Image.open(img_file)
                
                # Resize to 128x128
                img_resized = img.resize((128, 128), Image.Resampling.LANCZOS)
                
                # Save resized
                output_path = project_root / "data" / "test_files" / "cifar10_sample.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                img_resized.save(output_path)
                print(f"Saved CIFAR-10 sample to {output_path}")
                
                # Create primitive representation
                print("\nCreating primitive representation...")
                
                # Extract dominant colors from image
                arr = np.array(img_resized)
                
                # Simple color quantization
                from collections import Counter
                pixels = arr.reshape(-1, 3)
                # Quantize to 8 colors
                quantized = (pixels // 32) * 32
                color_counts = Counter(map(tuple, quantized))
                dominant_colors=[color for color, _ in color_counts.most_common(8)]
                
                print(f"Dominant colors: {dominant_colors}")
                
                # Create primitive instructions based on image
                instructions = DrawingInstructions(
                    background_color=dominant_colors[0] if dominant_colors else (255, 255, 255),
                    points=[
                        Point(0.5, 0.5, dominant_colors[1] if len(dominant_colors) > 1 else (255, 0, 0), 0.2),
                    ],
                    planes=[
                        Plane(
                            [
                                Point(0.1, 0.1, (0, 0, 0), 0.0),
                                Point(0.9, 0.1, (0, 0, 0), 0.0),
                                Point(0.9, 0.9, (0, 0, 0), 0.0),
                                Point(0.1, 0.9, (0, 0, 0), 0.0),
                            ],
                            dominant_colors[2] if len(dominant_colors) > 2 else (200, 200, 200),
                            (0, 0, 0),
                            0.01
                        )
                    ]
                )
                
                # Render primitive version
                renderer = PrimitiveRenderer(canvas_size=(128, 128))
                primitive_img = renderer.render(instructions)
                
                # Save primitive version
                primitive_path = project_root / "data" / "test_files" / "cifar10_primitive.png"
                primitive_img.save(primitive_path)
                print(f"Saved primitive version to {primitive_path}")
                
                # Compare images
                print("\nComparison:")
                print(f"  Original: {img_resized.size}, {img_resized.mode}")
                print(f"  Primitive: {primitive_img.size}, {primitive_img.mode}")
                
                # Calculate similarity (simple pixel comparison)
                original_arr = np.array(img_resized).astype(float)
                primitive_arr = np.array(primitive_img).astype(float)
                mse = np.mean((original_arr - primitive_arr) ** 2)
                print(f"  MSE between images: {mse:.2f}")
                
                return img_resized, primitive_img
    print("No CIFAR-10 images found")


if __name__ == "__main__":
    main()
