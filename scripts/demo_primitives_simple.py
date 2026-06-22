"""Simple demo of primitives without CLIP dependency."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

from ai.multimodal.primitives import (
    Point, Line, Plane, DrawingInstructions, PrimitiveRenderer, PrimitiveLibrary, PrimitiveEncoder
)
import numpy as np


def main():
    """Simple primitives demo."""
    print("Simple Primitives Demo")
    print("=" * 50)
    
    # Initialize components
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    encoder = PrimitiveEncoder(embedding_dim=64)
    library = PrimitiveLibrary(embedding_dim=64, max_primitives=100)
    
    # Create a simple drawing
    print("\n1. Creating simple drawing...")
    instructions = DrawingInstructions(
        background_color=(240, 240, 240),
        points=[
            Point(0.3, 0.3, (255, 0, 0), 0.15),  # Red circle
            Point(0.7, 0.7, (0, 255, 0), 0.1),   # Green circle
        ],
        lines=[
            Line(
                Point(0.3, 0.3, (0, 0, 0), 0.0),
                Point(0.7, 0.7, (0, 0, 0), 0.0),
                0.05,
                (0, 0, 255)
            )
        ],
        planes=[
            Plane(
                [
                    Point(0.1, 0.1, (0, 0, 0), 0.0),
                    Point(0.9, 0.1, (0, 0, 0), 0.0),
                    Point(0.9, 0.9, (0, 0, 0), 0.0),
                    Point(0.1, 0.9, (0, 0, 0), 0.0),
                ],
                (200, 200, 255),  # Light blue fill
                (0, 0, 0),        # Black outline
                0.02
            )
        ]
    )
    
    # Render
    img = renderer.render(instructions)
    output_path = project_root / "data" / "test_files" / "simple_primitives.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Saved drawing to {output_path}")
    
    # Add to library
    print("\n2. Adding to primitive library...")
    embedding = encoder.encode(instructions)
    library.add_primitive("simple_drawing", instructions, embedding)
    print(f"Library size: {library.size}")
    
    # Find similar
    print("\n3. Finding similar primitives...")
    similar = library.find_similar(embedding, top_k=3)
    for name, sim in similar:
        print(f"  {name}: {sim:.4f}")
    
    # Encode/decode roundtrip
    print("\n4. Encode/decode roundtrip...")
    decoded = encoder.decode(embedding)
    print(f"Original: {len(instructions.points)} points, {len(instructions.lines)} lines")
    print(f"Decoded: {len(decoded.points)} points, {len(decoded.lines)} lines")
    
    # Render decoded
    decoded_img = renderer.render(decoded)
    decoded_path = project_root / "data" / "test_files" / "simple_primitives_decoded.png"
    decoded_img.save(decoded_path)
    print(f"Saved decoded drawing to {decoded_path}")
    
    # Create multiple variations
    print("\n5. Creating variations...")
    variations = []
    for i in range(3):
        # Random variations
        var_instructions = DrawingInstructions(
            background_color=(255, 255, 255),
            points=[
                Point(np.random.random(), np.random.random(),
                     (int(np.random.random() * 255),
                      int(np.random.random() * 255),
                      int(np.random.random() * 255)),
                     0.1)
            ],
            lines=[
                Line(
                    Point(np.random.random(), np.random.random(), (0, 0, 0), 0.0),
                    Point(np.random.random(), np.random.random(), (0, 0, 0), 0.0),
                    0.03,
                    (int(np.random.random() * 255),
                     int(np.random.random() * 255),
                     int(np.random.random() * 255))
                )
            ]
        )
        
        # Render
        var_img = renderer.render(var_instructions)
        var_path = project_root / "data" / "test_files" / f"variation_{i}.png"
        var_img.save(var_path)
        variations.append(var_img)
        print(f"Saved variation {i} to {var_path}")
    
    print("\n" + "=" * 50)
    print("Demo complete!")
    print(f"Generated {len(variations) + 2} images in data/test_files/")


if __name__ == "__main__":
    main()
