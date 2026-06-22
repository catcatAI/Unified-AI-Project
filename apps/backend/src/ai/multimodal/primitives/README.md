# Primitives Package

Compositional image generation system for Angela AI.

## Overview

This package implements a learnable compositional image generation system that decomposes images into visual primitives (points, lines, planes) and composes them to generate new images from text descriptions.

## Architecture

```
Text/CLIP Embedding → Sequence Generator → Drawing Instructions → PIL Renderer → Image
         ↑                                    ↑                        ↑
    SemanticVisualEncoder              PrimitiveLibrary           ImageDraw
    ConceptLibrary                     AutoExpansion
```

## Components

### 1. Primitive Types (`primitive_types.py`)
- `Point`: Position, color, size
- `Line`: Start/end points, width, color
- `Plane`: Polygon vertices, fill/outline colors
- `DrawingInstructions`: Complete set of drawing instructions

### 2. Primitive Renderer (`primitive_renderer.py`)
- Renders `DrawingInstructions` to PIL Images
- Supports points, lines, and planes
- Configurable canvas size

### 3. Primitive Library (`primitive_library.py`)
- Stores primitives with embeddings
- Similarity search via cosine similarity
- Auto-expansion when new primitives are sufficiently different
- Save/load to JSON

### 4. Primitive Encoder (`primitive_encoder.py`)
- Encodes `DrawingInstructions` to fixed-size embeddings
- Decodes embeddings back to instructions
- Trainable via reconstruction loss

## Usage

### Basic Rendering
```python
from ai.multimodal.primitives import Point, Line, DrawingInstructions, PrimitiveRenderer

# Create instructions
instructions = DrawingInstructions(
    background_color=(255, 255, 255),
    points=[Point(0.5, 0.5, (255, 0, 0), 0.1)],
    lines=[Line(Point(0.0, 0.0, (0, 0, 0), 0.0),
               Point(1.0, 1.0, (0, 0, 0), 0.0),
               0.05, (0, 0, 255))]
)

# Render
renderer = PrimitiveRenderer(canvas_size=(128, 128))
img = renderer.render(instructions)
img.save("output.png")
```

### Primitive Library
```python
from ai.multimodal.primitives import PrimitiveLibrary, PrimitiveEncoder

# Create library and encoder
library = PrimitiveLibrary(embedding_dim=64)
encoder = PrimitiveEncoder(embedding_dim=64)

# Add primitives
embedding = encoder.encode(instructions)
library.add_primitive("my_primitive", instructions, embedding)

# Find similar
similar = library.find_similar(embedding, top_k=5)
```

### Training
```python
# Train encoder to improve reconstruction
encoder.train(instructions_list, epochs=100, lr=0.001)
```

## Tests

Run all tests:
```bash
pytest tests/ai/multimodal/primitives/ -v
```

## Integration with CLIP

The primitives system integrates with the existing CLIP encoder:
1. Encode images/text with `SemanticVisualEncoder`
2. Map CLIP embeddings to primitive embeddings
3. Generate drawing instructions from embeddings
4. Render to images

## Future Work

### Phase 1: Primitive Discovery
- Use CLIP to discover visual primitives from CIFAR-10
- Learn to reconstruct images from primitives

### Phase 2: Sequence Generator
- Train RNN to predict drawing instructions from CLIP embeddings
- Generate complex compositions from text

### Phase 3: Rendering Pipeline
- SVG rendering for scalable output
- Evaluation metrics (CLIP similarity, FID)
- API integration

## File Structure

```
primitives/
├── __init__.py
├── primitive_types.py      # Data classes for primitives
├── primitive_renderer.py   # PIL rendering
├── primitive_library.py    # Storage and retrieval
├── primitive_encoder.py    # Embedding conversion
└── README.md              # This file
```
