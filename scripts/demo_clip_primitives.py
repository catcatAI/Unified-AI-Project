"""End-to-end demo: CLIP encoding → primitive generation → rendering."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

from ai.multimodal.primitives import (
    Point, Line, Plane, DrawingInstructions, PrimitiveRenderer, PrimitiveLibrary, PrimitiveEncoder
)
from ai.multimodal.semantic_visual import SemanticVisualEncoder
import numpy as np
from PIL import Image


def demo_clip_to_primitives():
    """Demonstrate CLIP encoding to primitive generation."""
    print("=== CLIP to Primitives Demo ===")
    
    # Initialize CLIP encoder
    clip_encoder = SemanticVisualEncoder()
    if not clip_encoder.is_available:
        print("CLIP not available, using random embeddings for demo")
        # Create mock encoder for demo
        class MockEncoder:
            def encode(self, data):
                return np.random.randn(512).astype(np.float32)
            def encode_text(self, texts):
                return np.random.randn(len(texts), 512).astype(np.float32)
        clip_encoder = MockEncoder()
    
    # Initialize primitive components
    primitive_encoder = PrimitiveEncoder(embedding_dim=64)
    primitive_library = PrimitiveLibrary(embedding_dim=64, max_primitives=100)
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    
    # Create some initial primitives
    print("Creating initial primitive library...")
    for i in range(10):
        # Random primitive
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
        
        # Encode to embedding
        embedding = primitive_encoder.encode(instructions)
        
        # Add to library
        primitive_library.add_primitive(f"prim_{i:04d}", instructions, embedding)
    
    print(f"Library size: {primitive_library.size}")
    
    # Demo: Generate primitives from text
    print("\nGenerating primitives from text descriptions...")
    texts = ["a red circle", "a blue line", "a green square"]
    
    for text in texts:
        # Encode text with CLIP
        text_embedding = clip_encoder.encode_text([text])[0]
        
        # Find similar primitives in library
        similar = primitive_library.find_similar(text_embedding[:64], top_k=3)  # Truncate to 64 dim
        print(f"\nText: '{text}'")
        print(f"  Similar primitives:")
        for name, sim in similar:
            print(f"    {name}: {sim:.4f}")
    
    # Demo: Generate image from primitives
    print("\nGenerating sample images...")
    
    # Create a simple composition
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
    
    # Save
    output_path = project_root / "data" / "test_files" / "clip_primitives_demo.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Saved generated image to {output_path}")
    
    # Demo: Encode/decode roundtrip
    print("\nEncode/decode roundtrip demo...")
    embedding = primitive_encoder.encode(instructions)
    decoded = primitive_encoder.decode(embedding)
    
    print(f"Original: {len(instructions.points)} points, {len(instructions.lines)} lines")
    print(f"Decoded: {len(decoded.points)} points, {len(decoded.lines)} lines")
    
    # Render decoded
    decoded_img = renderer.render(decoded)
    decoded_path = project_root / "data" / "test_files" / "clip_primitives_decoded.png"
    decoded_img.save(decoded_path)
    print(f"Saved decoded image to {decoded_path}")
    
    return instructions, img


def demo_cifar10_integration():
    """Demo with CIFAR-10 images."""
    print("\n=== CIFAR-10 Integration Demo ===")
    
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
                
                return img_resized
    print("No CIFAR-10 images found")


def main():
    """Run all demos."""
    print("CLIP + Primitives Integration Demo")
    print("=" * 50)
    
    # Run demos
    demo_clip_to_primitives()
    demo_cifar10_integration()
    
    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    main()
