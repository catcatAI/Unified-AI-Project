import sys, os
sys.path.insert(0, os.path.join('apps', 'backend', 'src'))

class MockModule:
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()
    def __iter__(self):
        return iter([])

for mod in ['torch', 'torch.nn', 'torch.nn.functional', 'torch.cuda', 'torch.optim']:
    sys.modules[mod] = MockModule()

import time
from ai.garden.garden_engine import GardenEngine

garden = GardenEngine()

test_pairs = [
    ("What is the capital of France?", "The capital of France is Paris."),
    ("1+1", "2"),
    ("What color is the sky?", "The sky is blue."),
    ("How does a refrigerator work?", "A refrigerator compresses refrigerant vapor, which cools down in the condenser, then evaporates in the evaporator."),
]

total_time = 0
total_new = 0
for user, response in test_pairs:
    start = time.time()
    result = garden.learn_from_interaction(user, response)
    elapsed = time.time() - start
    total_time += elapsed
    total_new += len(result["new_concepts"])
    print(f"Time: {elapsed:.2f}s | New: {len(result['new_concepts'])} | Input keys: {len(result['input_keys'])} | Output keys: {len(result['output_keys'])}")

print(f"\nTotal: {total_time:.2f}s for {len(test_pairs)} interactions ({total_time/len(test_pairs):.2f}s avg)")
print(f"Total new concepts: {total_new}")
print(f"Dictionary size: {len(garden.dictionary.entries)}")
