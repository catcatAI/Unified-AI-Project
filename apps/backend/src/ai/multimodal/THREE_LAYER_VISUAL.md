# Three-Layer Visual Architecture

## Overview

The Three-Layer Visual Architecture is a learnable image representation and generation system for Angela AI. Instead of fixed geometric primitives, it uses **PCA components as learned primitives** to capture the geometric essence of images.

### Architecture

```
Input Image (32×32×3 = 3072-dim)
  ↓ PCA Encoder (learned projection)
Latent Space (128-dim, 95.6% variance)
  ↓ Decoder (nonlinear neural network)
Reconstructed Image (3072-dim)
  ↓ Post-processing (contrast + unsharp mask)
Enhanced Image (sharp, structured)
```

### Key Innovation

PCA components serve as **learned visual primitives**:
- Each component captures a different pattern in the data
- More meaningful than fixed geometric types (points, lines, planes)
- Captures the "geometric essence" of each class
- Same representation used for both recognition and generation

## Performance

| Metric | Geometric Primitives (263-dim) | Three-Layer (128-dim) |
|--------|-------------------------------|------------------------|
| MSE | 0.04 | **0.009** |
| Visual Quality | Gray circles | **Colored, structured** |
| Training Time | 15 min | **2.5 min** |
| Class Centers | Gray blur | **Distinguishable features** |
| Interpolation | Meaningless | **Smooth transition** |

## Usage

### Python API

```python
from ai.multimodal.three_layer_visual import ThreeLayerVisual

# Initialize
model = ThreeLayerVisual(model_dir="models/three_layer")

# Train on CIFAR-10 style data
import numpy as np
images = np.random.rand(500, 3072).astype(np.float32)  # (N, 3072)
labels = np.repeat(np.arange(10), 50)  # (N,)
class_names = ["airplane", "automobile", "bird", "cat", "deer",
               "dog", "frog", "horse", "ship", "truck"]

metrics = model.fit(images, labels, class_names, n_epochs=100)
print(f"MSE: {metrics['test_mse']:.4f}")

# Encode images to latent space
latent = model.encode(images)  # (N, 128)

# Decode latent vectors to images
recon = model.decode(latent)  # (N, 3072)

# Reconstruct with post-processing
recon_enhanced = model.reconstruct(images, enhance=True)  # (N, 3072)

# Generate from class center
airplane = model.generate_from_class(0, enhance=True)  # (3072,)

# Interpolate between classes
interp = model.interpolate(0, 3, n_steps=10)  # (10, 3072)

# Recognize images
preds, dists = model.recognize(images, top_k=3)  # (N, 3)

# Save/load model
model.save()
model.load()
```

### Visual Components

```python
# Get PCA components as visual primitives
components = model.get_pca_components(n_components=10)  # (10, 3072)

# Each component captures a different visual pattern
for i, comp in enumerate(components):
    print(f"Component {i}: variance captured")
```

## Training Data

The model works best with:
- **Images**: 32×32 RGB (CIFAR-10 style), flattened to 3072-dim vectors
- **Labels**: Integer class indices (0-9 for CIFAR-10)
- **Minimum**: ~50 images per class for meaningful results
- **Recommended**: ~500+ images per class

## Post-Processing

The model applies two enhancement steps:

1. **Contrast Enhancement** (1.3x)
   - Increases dynamic range
   - Makes features more distinct

2. **Unsharp Mask**
   - Sharpens edges
   - Radius: 1, Strength: 120%, Threshold: 2

This transforms blurry reconstructions into sharper, more recognizable images.

## CPU Feasibility

| Configuration | Training Time | Inference | Quality |
|---------------|---------------|-----------|---------|
| 128-dim + small decoder | 2.5 min | instant | Blurry |
| 256-dim + medium decoder | ~5 min | instant | Better |
| 512-dim + large decoder | ~10 min | instant | Sharp |
| 3072-dim + full decoder | ~20 min | instant | Near-perfect |

**All configurations run on CPU. No GPU required.**

## Integration with Angela

The Three-Layer Visual architecture integrates with:

- **CLIP**: Maps text → semantic vectors → class predictions
- **Concept Library**: Stores learned class representations
- **Multimodal Bridge**: Connects visual understanding to dialogue

### Pipeline

```
User: "Generate an image of a cat"
  ↓
CLIP encode text → semantic vector (512-dim)
  ↓
Map to class center (128-dim)
  ↓
Three-Layer decode → image (3072-dim)
  ↓
Post-processing → sharp image (32×32×3)
  ↓
Display to user
```

## Limitations

1. **Resolution**: Currently 32×32 pixels (CIFAR-10 scale)
2. **Classes**: Limited to trained categories
3. **Blurriness**: Class centers are averages (inherently blurry)
4. **Training Data**: Requires labeled images for each class

## Future Improvements

1. **Higher Resolution**: Scale to 64×64, 128×128, 256×256
2. **More Classes**: Train on larger datasets (ImageNet, etc.)
3. **Better Decoder**: Deeper networks, perceptual loss
4. **VAE Extension**: Add KL regularization for smoother latent space
5. **Diffusion Integration**: Combine with diffusion models for high-quality generation

## Files

- `apps/backend/src/ai/multimodal/three_layer_visual.py` - Main implementation
- `apps/backend/src/api/routes/image_generation_routes.py` - API endpoints
- `scripts/train_three_layer.py` - Training script
- `scripts/three_layer_arch.py` - Architecture experiments
- `scripts/compare_pca_dims.py` - PCA dimension comparison
- `scripts/perceptual_loss.py` - Loss function experiments
- `scripts/sharpness_test.py` - Post-processing comparison

## API Endpoints

### POST /reconstruct-image

Reconstruct an image through the bottleneck.

**Request:**
```json
{
  "image_base64": "<base64-encoded PNG>",
  "enhance": true
}
```

**Response:**
```json
{
  "image_base64": "<reconstructed image>",
  "width": 32,
  "height": 32,
  "metrics": {
    "mse": 0.0042,
    "reconstruct_time": 0.001,
    "enhanced": true
  }
}
```

### POST /interpolate-classes

Interpolate between two class centers.

**Request:**
```json
{
  "class_a": 0,
  "class_b": 3,
  "n_steps": 10,
  "enhance": true
}
```

**Response:**
```json
{
  "images": ["<base64>", "..."],
  "width": 32,
  "height": 32,
  "metrics": {
    "class_a": 0,
    "class_b": 3,
    "n_steps": 10,
    "interpolate_time": 0.05
  }
}
```

### GET /generate-image/status

Check if image generation is available.

**Response:**
```json
{
  "gvv_available": true,
  "three_layer_available": true,
  "pipeline": "gvv",
  "vocab_size": 50,
  "concept_count": 10,
  "concept_space": true
}
```

## Training

```bash
# Train the model
python scripts/train_three_layer.py

# Output:
# - Model saved to models/three_layer/
# - Training: 50 epochs, ~84 seconds
# - MSE: 0.0042
# - Generates: reconstructions, class centers, interpolations
```

## References

- PCA: Principal Component Analysis for dimensionality reduction
- Learned Primitives: PCA components as visual building blocks
- Post-processing: Contrast enhancement + unsharp mask for sharpness
