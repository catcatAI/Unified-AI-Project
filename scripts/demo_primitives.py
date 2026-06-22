"""Demo script for compositional image generation primitives."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

from ai.multimodal.primitives import (
    Point, Line, Plane, DrawingInstructions, PrimitiveRenderer, PrimitiveLibrary
)
import numpy as np


def demo_simple_drawing():
    """Create a simple drawing using primitives."""
    print("=== Simple Drawing Demo ===")
    
    # Create drawing instructions
    instructions = DrawingInstructions(
        background_color=(240, 240, 240),
        points=[
            Point(0.5, 0.3, (255, 0, 0), 0.15),  # Red circle
            Point(0.3, 0.7, (0, 255, 0), 0.1),   # Green circle
            Point(0.7, 0.7, (0, 0, 255), 0.1),   # Blue circle
        ],
        lines=[
            Line(
                Point(0.3, 0.7, (0, 0, 0), 0.0),
                Point(0.7, 0.7, (0, 0, 0), 0.0),
                0.03,
                (0, 0, 0)
            ),
            Line(
                Point(0.5, 0.3, (0, 0, 0), 0.0),
                Point(0.5, 0.7, (0, 0, 0), 0.0),
                0.02,
                (128, 128, 128)
            ),
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
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    img = renderer.render(instructions)
    
    # Save
    output_path = project_root / "data" / "test_files" / "primitives_demo.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Saved simple drawing to {output_path}")
    
    return instructions


def demo_primitive_library():
    """Demonstrate primitive library operations."""
    print("\n=== Primitive Library Demo ===")
    
    # Create library
    library = PrimitiveLibrary(embedding_dim=64, max_primitives=100)
    
    # Create some primitives
    primitives = []
    for i in range(5):
        # Create random embedding
        embedding = np.random.randn(64).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        
        # Create random drawing instructions
        instructions = DrawingInstructions(
            background_color=(255, 255, 255),
            points=[
                Point(np.random.random(), np.random.random(), 
                     (int(np.random.random() * 255), 
                      int(np.random.random() * 255),
                      int(np.random.random() * 255)), 
                     0.1)
            ]
        )
        
        # Add to library
        name = f"prim_{i:04d}"
        library.add_primitive(name, instructions, embedding)
        primitives.append((name, embedding, instructions))
    
    print(f"Library size: {library.size}")
    
    # Find similar primitives
    query_embedding = primitives[0][1]  # Use first primitive's embedding
    similar = library.find_similar(query_embedding, top_k=3)
    print(f"Similar primitives to {primitives[0][0]}:")
    for name, sim in similar:
        print(f"  {name}: {sim:.4f}")
    
    # Auto-expand test
    new_embedding = np.random.randn(64).astype(np.float32)
    new_embedding = new_embedding / np.linalg.norm(new_embedding)
    new_instructions = DrawingInstructions(
        points=[Point(0.5, 0.5, (255, 0, 0), 0.1)]
    )
    
    new_name = library.auto_expand(new_embedding, new_instructions, threshold=0.5)
    if new_name:
        print(f"Auto-expanded with new primitive: {new_name}")
    else:
        print("Auto-expand rejected (too similar)")
    
    # Save library
    library_path = project_root / "data" / "test_files" / "primitive_library.json"
    library.save(library_path)
    print(f"Saved library to {library_path}")
    
    return library


def demo_vector_conversion():
    """Demonstrate vector conversion for ML."""
    print("\n=== Vector Conversion Demo ===")
    
    # Create instructions
    instructions = DrawingInstructions(
        background_color=(128, 128, 128),
        points=[
            Point(0.25, 0.25, (255, 0, 0), 0.1),
            Point(0.75, 0.75, (0, 255, 0), 0.1),
        ],
        lines=[
            Line(
                Point(0.1, 0.5, (0, 0, 0), 0.0),
                Point(0.9, 0.5, (0, 0, 0), 0.0),
                0.05,
                (0, 0, 255)
            )
        ]
    )
    
    # Convert to vector
    vec = instructions.to_vector()
    print(f"Vector shape: {vec.shape}")
    print(f"Vector dtype: {vec.dtype}")
    print(f"First 10 values: {vec[:10]}")
    
    # Convert back
    restored = DrawingInstructions.from_vector(vec)
    print(f"Restored background color: {restored.background_color}")
    print(f"Restored points: {len(restored.points)}")
    print(f"Restored lines: {len(restored.lines)}")
    
    return instructions


def main():
    """Run all demos."""
    print("Compositional Image Generation Primitives Demo")
    print("=" * 50)
    
    # Run demos
    demo_simple_drawing()
    demo_primitive_library()
    demo_vector_conversion()
    
    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    main()
