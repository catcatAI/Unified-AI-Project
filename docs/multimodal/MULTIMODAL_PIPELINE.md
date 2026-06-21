# Multimodal Pipeline — Developer Guide

> **Document version**: P38 (2026-06-22)
> **Status**: ✅ Complete — 8 phases (P30-P38) all finished

## Architecture Overview

The multimodal pipeline provides a complete end-to-end system for encoding, decoding,
comparing, retrieving, generating, and evaluating multimodal data (vision + audio).

```
┌──────────────────────────────────────────────────────────────┐
│                      Multimodal Pipeline                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FRONTEND (Electron/Web/Mobile)                              │
│         │                                                    │
│         ▼ HTTP                                               │
│  API ROUTES (/multimodal/*) — 25+ endpoints                 │
│         │                                                    │
│         ▼                                                    │
│  SERVICE LAYER                                                │
│  ┌─ MultimodalService (orchestrator)                        │
│  │  ├─ encode / decode / compare / retrieve                 │
│  │  ├─ train / evaluate / generate                          │
│  │  ├─ continuous learning (CML) + memory                    │
│  │  └─ error recovery + state persistence + quality monitor │
│  └─ CrossModalRouter (routing) ─── CrossModalQualityDashboard│
│         │                                                    │
│         ▼                                                    │
│  SINGLE-MODALITY PIPELINES                                   │
│  ┌─ VisionPipeline (bytes → latent → image → SSIM)          │
│  ├─ AudioPipeline (WAV → latent → waveform → SNR)           │
│  └─ Cross-Modal (vision↔audio via shared latent space)      │
│         │                                                    │
│         ▼                                                    │
│  AI MODULE LAYER                                             │
│  ├─ VisualEncoder (256-dim CNN Gabor filter bank)            │
│  ├─ AudioSpectralEncoder (128-dim MFCC + temporal attention) │
│  ├─ SharedLatentSpace (64-dim + contrastive + cross-attn)    │
│  ├─ VisualDecoder (latent → 128×128 RGB)                     │
│  ├─ AudioWaveformDecoder (latent → 16kHz PCM)                │
│  ├─ MultimodalRetriever (numpy cosine vector index)          │
│  ├─ MultimodalRAGEngine (encode → query → ED3N entries)      │
│  ├─ ReconstructionCycle (feature-level autoencoder)          │
│  ├─ TrainingPipeline (contrastive + reconstruction)           │
│  └─ quality_metrics (SSIM / PSNR / SNR)                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Phase Overview (P30-P38)

| Phase | Name | Description | Tests |
|:-----:|------|-------------|:-----:|
| **P30** | MultimodalService + API | Orchestrator service with 9 REST endpoints, 27 tests | ✅ |
| **P31** | VisionPipeline | vision→encode→latent→decode→SSIM, 20 tests | ✅ |
| **P32** | AudioPipeline | audio→encode→latent→decode→SNR, 20 tests | ✅ |
| **P33** | CrossModalRouter + Quality | Routing, quality dashboard, ED3N deep integration, 25 tests | ✅ |
| **P34** | Desktop Frontend UI | Electron MultimodalPanel (5 tabs), API client, 11 tests | ✅ |
| **P35** | Mobile Frontend UI | React Native camera/audio capture (skipped) | ⬜ |
| **P36** | Continuous Learning + Memory | CML (auto micro-train), MultimodalMemoryStore (7/30d TTL), 20 tests | ✅ |
| **P37** | Production Hardening | ErrorRecovery (retry/fallback/checkpoint), StatePersistence (save/load/list), QualityMonitor (60s background loop), 23 tests | ✅ |
| **P38** | Maintenance & Testing | End-to-end integration, stress tests, multilingual tests, docs, crisis_log dedup, 10 tests | ✅ |

**Total**: P30-P38 = **167 tests** all passing ✅

## Getting Started

### Prerequisites

```bash
pip install numpy pillow    # Core dependencies
pip install pytest          # For running tests
```

### Quick Start

```python
from services.multimodal_service import MultimodalService

svc = MultimodalService()

# Encode an image
with open("image.png", "rb") as f:
    img_data = f.read()
result = await svc.encode(img_data, "vision")
print(f"Vision: {result['item_id']}, dim={result['dim']}")

# Encode audio
with open("audio.wav", "rb") as f:
    aud_data = f.read()
result = await svc.encode(aud_data, "audio")
print(f"Audio: {result['item_id']}, dim={result['dim']}")

# Compare
similarity = await svc.compare("vision_item", "audio_item")
print(f"Cross-modal similarity: {similarity['similarity']:.2f}")
```

### API Endpoints

All endpoints are under `/multimodal/` prefix:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/multimodal/encode` | POST | Encode image/audio to feature vector + latent |
| `/multimodal/decode` | POST | Decode latent to image/audio (base64) |
| `/multimodal/compare` | POST | Cross-modal similarity comparison |
| `/multimodal/retrieve` | POST | RAG retrieval by latent query |
| `/multimodal/train` | POST | Trigger training pipeline |
| `/multimodal/evaluate` | POST | Evaluate generation quality |
| `/multimodal/generate` | POST | Cross-modal generation (vision↔audio) |
| `/multimodal/visualize` | POST | Latent space 2D projection |
| `/multimodal/items` | GET | List registered items |
| `/multimodal/clear` | POST | Clear all items |
| `/multimodal/health` | GET | Health check (P37 enhanced) |
| `/multimodal/cross-infer` | POST | Cross-modal inference routing |
| `/multimodal/quality/dashboard` | GET | Quality dashboard |
| `/multimodal/recovery/*` | GET/POST | Error recovery state |
| `/multimodal/checkpoint/*` | GET/POST | State persistence |
| `/multimodal/quality/*` | GET/POST | Quality monitoring |
| `/multimodal/cml/*` | GET/POST | Continuous learning |
| `/multimodal/memory/*` | GET/POST | Memory store |

## Core Components

### MultimodalService

The central orchestrator. All multimodal operations go through this service.

```python
svc = MultimodalService()

# Core operations
await svc.encode(data, modality, item_id)       # → dict with latent, feature_vector
await svc.decode(item_id, modality)              # → dict with decoded data (base64/PIL/raw)
await svc.compare(item_a, item_b)               # → dict with similarity [0,1]
await svc.retrieve(query_id, top_k)             # → list of {key, score, modality}
await svc.train(mode, epochs, lr)               # → dict with status, loss
await svc.evaluate(item_id, modality)           # → dict with SSIM/PSNR/SNR
await svc.generate(source_id, target_modality)  # → dict with generated data

# Production hardening
await svc.encode_with_retry(data, modality)     # 3 retries + exponential backoff
await svc.decode_with_fallback(item_id, modality)  # text description on failure
await svc.save_checkpoint(label)                # save full state
await svc.load_checkpoint(label)                # restore from checkpoint
await svc.start_quality_monitor()               # 60s background sampling
```

### VisionPipeline (P31)

Complete vision pipeline: bytes → encode → latent → decode → SSIM.

```python
from ai.vision.vision_pipeline import VisionPipeline

pipeline = VisionPipeline()
result = pipeline.process(image_bytes)
# result = {latent, decoded_image, ssim, psnr, feature_vector}
```

### AudioPipeline (P32)

Complete audio pipeline: WAV → encode → latent → decode → SNR.

```python
from ai.audio.audio_pipeline import AudioPipeline

pipeline = AudioPipeline()
result = pipeline.process(audio_bytes)
# result = {latent, decoded_waveform, snr, feature_vector}
```

### CrossModalRouter (P33)

Routes requests to correct pipeline with fallback chain.

```python
from services.cross_modal_router import CrossModalRouter

router = CrossModalRouter()
result = await router.route("vision", data, "encode")
# Routes to vision pipeline with confidence scoring
```

### ContinuousMultimodalLearning (P36)

Auto micro-trains when buffer fills up.

```python
cml = ContinuousMultimodalLearning()
cml.record_encode("vision", features, latent, quality=0.85)
if cml.should_train():
    result = cml.micro_train()
```

### Error Recovery (P37)

```python
er = MultimodalErrorRecovery(service)
result = await er.encode_with_retry(data, "vision")  # 3 retries
result = await er.decode_with_fallback(id, "vision")  # text description
result = await er.train_with_checkpoint(mode="full")  # pre-save checkpoint
```

### State Persistence (P37)

```python
sp = MultimodalStatePersistence(service)
await sp.save_checkpoint("production_v1")
await sp.load_checkpoint("production_v1")
checkpoints = await sp.list_checkpoints()
await sp.prune_checkpoints(keep=5)
```

### Quality Monitor (P37)

```python
qm = MultimodalQualityMonitor(service)
await qm.start()  # 60s background loop
report = qm.report()
trend = qm.quality_trend()
```

## Testing

```bash
# Run all multimodal tests
pytest tests/services/test_multimodal_service.py -v
pytest tests/ai/multimodal/ -v
pytest tests/services/test_cross_modal.py -v
pytest tests/services/test_multimodal_production.py -v

# End-to-end integration
pytest tests/services/test_multimodal_integration.py -v

# Stress tests (slow)
pytest tests/benchmarks/test_multimodal_stress.py -v --timeout=120

# Multilingual tests
pytest tests/ai/multimodal/test_multilingual_multimodal.py -v

# All tests
pytest tests/services/test_cross_modal.py tests/services/test_multimodal_service.py tests/api/test_multimodal_routes.py tests/ai/vision/test_vision_pipeline.py tests/ai/audio/test_audio_pipeline.py tests/services/test_multimodal_production.py tests/services/test_multimodal_integration.py -v
```

## File Map

```
apps/backend/src/
├── ai/
│   ├── vision/
│   │   ├── vision_pipeline.py       P31: Full vision pipeline
│   │   └── quality_monitor.py        P31: Vision quality tracking
│   ├── audio/
│   │   ├── audio_pipeline.py         P32: Full audio pipeline
│   │   └── quality_monitor.py        P32: Audio quality tracking
│   └── multimodal/
│       ├── visual_encoder.py         P15: CNN Gabor filter bank 256-dim
│       ├── audio_encoder_spectral.py P15: MFCC 128-dim
│       ├── shared_latent_space.py    P16: 64-dim + contrastive + attention
│       ├── visual_decoder.py         P18: latent → 128×128 RGB
│       ├── audio_decoder.py          P18: latent → 16kHz PCM
│       ├── reconstruction_cycle.py   P19: autoencoder training
│       ├── similarity_service.py     P15b: encode/decode/compare API
│       ├── multimodal_retriever.py   P21: vector index
│       ├── multimodal_rag_engine.py  P21: encode→query→ED3N
│       ├── multimodal_ed3n_adapter.py P22: ED3N bidirectional
│       ├── quality_metrics.py        P24: SSIM/PSNR/SNR
│       ├── training_pipeline.py      P27: 2-stage training
│       ├── data_loader.py            P28: CIFAR-10/ESC-50
│       ├── continuous_multimodal_learning.py  P36: auto micro-train
│       └── multimodal_memory.py      P36: persistent memory store
├── services/
│   ├── multimodal_service.py         P30: Orchestrator + P36/P37 methods
│   ├── cross_modal_router.py         P33: routing + confidence
│   ├── cross_modal_quality.py        P33: quality dashboard
│   ├── multimodal_error_recovery.py  P37: retry/fallback/checkpoint
│   ├── multimodal_state_persistence.py P37: save/load/list/prune
│   └── multimodal_quality_monitor.py P37: 60s background sampling
├── api/routes/
│   └── multimodal_routes.py          P30+P33+P36+P37: 25+ endpoints
└── core/
    └── crisis_log.py                 P38: shared logging utility
docs/
└── multimodal/
    └── MULTIMODAL_PIPELINE.md        P38: This file
tests/
├── services/
│   ├── test_multimodal_service.py    P30: 27 tests
│   ├── test_cross_modal.py           P33: 25 tests
│   ├── test_multimodal_production.py P37: 23 tests
│   └── test_multimodal_integration.py P38: 10 tests (NEW)
├── api/
│   └── test_multimodal_routes.py     P30: 9 tests
├── ai/
│   ├── vision/
│   │   └── test_vision_pipeline.py   P31: 20 tests
│   ├── audio/
│   │   └── test_audio_pipeline.py    P32: 20 tests
│   ├── multimodal/
│   │   ├── test_continuous_multimodal_learning.py P36: 20 tests
│   │   └── test_multilingual_multimodal.py P38: 8 tests (NEW)
│   └── multimodal/ (P15-P29)
├── benchmarks/
│   └── test_multimodal_stress.py     P38: 5 tests (NEW)
└── desktop/
    └── test_multimodal_panel.py      P34: 11 tests
```
