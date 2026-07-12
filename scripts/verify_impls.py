import sys

sys.path.insert(0, '.')

print('=== REAL IMPLEMENTATIONS (different names) ===')

# 1. ModelProvider -> LLMBackend
from services.llm.providers.registry import LLMBackend

print('1. ModelProvider -> LLMBackend (enum):')
print('   Values:', [e.name for e in LLMBackend])

# 2. AuditoryAttentionController -> AttentionController
from core.perception.attention_controller import AttentionController

methods = [m for m in dir(AttentionController) if not m.startswith('_')]
print('2. AuditoryAttentionController -> AttentionController:')
print('   Methods:', methods[:10])

# 3. ArtLearningSystem -> ArtLearningWorkflow
from core.engine.art_learning_workflow import ArtLearningWorkflow

methods = [m for m in dir(ArtLearningWorkflow) if not m.startswith('_')]
print('3. ArtLearningSystem -> ArtLearningWorkflow:')
print('   Methods:', methods)

# 4. DesktopPresence -> DesktopInteraction
from core.engine.desktop_interaction import DesktopInteraction

methods = [m for m in dir(DesktopInteraction) if not m.startswith('_')]
print('4. DesktopPresence -> DesktopInteraction:')
print('   Methods:', methods)

# 5. Live2DIntegration -> Live2DAvatarGenerator
from core.engine.live2d_avatar_generator import Live2DAvatarGenerator

methods = [m for m in dir(Live2DAvatarGenerator) if not m.startswith('_')]
print('5. Live2DIntegration -> Live2DAvatarGenerator:')
print('   Methods:', methods[:10])

# 6. MemoryNeuroplasticityBridge -> NeuroplasticitySystem
from core.bio.neuroplasticity_core import NeuroplasticitySystem

methods = [m for m in dir(NeuroplasticitySystem) if not m.startswith('_')]
print('6. MemoryNeuroplasticityBridge -> NeuroplasticitySystem:')
print('   Methods:', methods[:10])