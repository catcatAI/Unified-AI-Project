# BACKBONE_TOPOLOGY — the shared-instance registry

> What the backbone is, which modules live in it, and why the chat pipeline
> must not build its own copies.

ANGELA-MATRIX: [L2] [β] [A] [L0-L11]

---

## 1. What it is

`core/backbone/backbone.py` is the project's **single-instance registry**. It
exists because the chat pipeline used to build its own copy of every shared
subsystem: two `EmotionSystem`s, two `StateMatrix4D`s, two ED3N engines. The
copies drifted, and a write in one place was invisible in the other — the
"the last-resort branch observed `None` and the fallback could never fire"
class of bug.

The registry gives every shared subsystem exactly one address:

```python
from core.backbone import get_backbone

bb = get_backbone()
engine = bb.get_module("chat.ed3n_engine")   # fetch
bb.register_module("chat.ed3n_engine", engine) # publish
```

## 2. The module keys

| Key | Subsystem | Registered by |
|---|---|---|
| `chat.state_matrix` | `StateMatrix4D` (the shared matrix) | `api.routes.chat_routes._get_state_matrix` |
| `chat.emotion_system` | `EmotionSystem` (emotion state, cross-process) | `api/lifespan.get_emotion_system` |
| `chat.emotion_analyzer` | `EmotionAnalyzer` (text → PAD) | `api.routes.chat_routes._get_emotion_analyzer` |
| `chat.query_classifier` | `QueryClassifier` | `api.routes.chat_routes._get_query_classifier` |
| `chat.lifecycle` | `AutonomousLifeCycle` (life phase) | `api/lifespan.get_lifecycle` |
| `chat.bio_integrator` | `BiologicalIntegrator` | `api.routes.chat_routes._get_bio_integrator` |
| `chat.eta_axis` | `EtaAxis` (θ) | `api.routes.chat_routes._get_eta_axis` |
| `chat.modality_gateway` | `ModalityGateway` | `api.routes.chat_routes._get_modality_gateway` |
| `chat.dialogue_ctx` | dialogue context | `api.routes.chat_routes._get_dialogue_ctx` |
| `chat.ed3n_engine` | `ED3NEngine` | `api.routes.chat_routes._get_ed3n_engine` |
| `chat.msba_pipeline` | `MSBAPipeline` (semantic blocks) | `api.routes.chat_routes._get_msba_pipeline` |
| `chat.vision_service` | `VisionService` | `api/lifespan.get_vision_service` |

> The keys are namespaced `chat.*` because the backbone is process-wide: the
> game agent (a separate process) shares the same key space, and a future
> `game.*` namespace will not collide with it.

## 3. The rule for the chat pipeline

**Never construct a shared subsystem inline.** Use the lifespan accessor:

```python
# wrong — a second copy, invisible to every other consumer
from ai.alignment.emotion_system import EmotionSystem
system = EmotionSystem()

# right — the one instance everybody observes
from api.lifespan import get_emotion_system
system = get_emotion_system()
```

`api/lifespan.py` owns the lifecycle: it creates the instance, registers it
in the backbone and hands out the same object to every caller.

## 4. The other registries

Besides modules, the backbone carries the *cross-cutting* registries:

| Registry | Holds | Used by |
|---|---|---|
| `registries.modules` | the shared instances (above) | the chat pipeline |
| `registries.axes` | named state axes | `StateMatrixAdapter`, θ routing |
| `dictionaries` | named dictionaries | ED3N / GARDEN / MSBA |
| `pairs` | learned concept pairs | ED3N relation learning |
| `subscriptions` | event subscriptions | CNS event bus |
| `translators` | cross-module translators | backbone↔external bridges |
| `external` | externally mounted modules | HSP / external connectors |

## 5. Verifying the topology

```bash
pytest tests/core/backbone/ -q          # the registry contract
python -c "from core.backbone import get_backbone; print(get_backbone().summary())"
```

`summary()` lists the mounted modules and the size of every registry — the
quickest way to see whether a subsystem was registered twice or not at all.

## 6. What this document replaces

The task list used to carry "T-BACKBONE-1: 新增 `docs/architecture/BACKBONE_TOPOLOGY.md`"
as an open item: the topology was only discoverable by reading
`api/lifespan.py` and `core/backbone/`. This file is the map.
