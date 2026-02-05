import pytest
import numpy as np
from apps.backend.src.core.perception.visual_sampler import VisualSampler, SamplingDistribution

def test_sampler_initialization():
    sampler = VisualSampler()
    assert sampler.particles == []
    assert sampler.current_focus == (0.5, 0.5)

def test_generate_cloud_gaussian():
    sampler = VisualSampler()
    particles = sampler.generate_cloud(count=100, center=(0.5, 0.5), distribution=SamplingDistribution.GAUSSIAN)
    
    assert len(particles) == 100
    # Check if they are mostly around center
    xs = [p.x for p in particles]
    ys = [p.y for p in particles]
    assert 0.4 < np.mean(xs) < 0.6
    assert 0.4 < np.mean(ys) < 0.6

def test_apply_transform_scale():
    sampler = VisualSampler()
    # Generate points in a small cluster
    sampler.generate_cloud(count=100, center=(0.5, 0.5), spread=0.1)
    stats_before = sampler.get_attention_stats()
    
    # Scale up
    sampler.apply_transform(scale=2.0)
    stats_after = sampler.get_attention_stats()
    
    # Range should increase
    assert stats_after["attention_range"] > stats_before["attention_range"]

def test_apply_transform_deformation():
    sampler = VisualSampler()
    sampler.generate_cloud(count=100, center=(0.5, 0.5), spread=0.1)
    
    # Deformation should move particles
    orig_xs = [p.x for p in sampler.particles]
    sampler.apply_transform(deformation=0.5)
    new_xs = [p.x for p in sampler.particles]
    
    assert orig_xs != new_xs

def test_attention_stats():
    sampler = VisualSampler()
    sampler.generate_cloud(count=500, center=(0.5, 0.5), distribution=SamplingDistribution.GAUSSIAN, spread=0.2)
    stats = sampler.get_attention_stats()
    
    assert stats["particle_count"] == 500
    assert 0 < stats["average_precision"] <= 1.0
    assert stats["attention_range"] > 0
    assert stats["focus_point"] == (0.5, 0.5)

@pytest.mark.asyncio
async def test_sample_image():
    sampler = VisualSampler()
    sampler.generate_cloud(count=10, center=(0.5, 0.5))
    
    # Create a dummy image (100x100 RGB)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[50, 50] = [255, 255, 255] # White pixel at center
    
    samples = await sampler.sample_image(img)
    assert len(samples) == 10
    for s in samples:
        assert "pos" in s
        assert "color" in s
        assert "intensity" in s
