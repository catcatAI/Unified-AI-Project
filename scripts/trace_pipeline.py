"""Trace the full encode -> SNN -> decode pipeline."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.garden.garden_engine import GARDENEngine

e = GARDENEngine(compatibility_mode=True)
ckpt = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints", "garden_checkpoint")
if os.path.isdir(ckpt):
    e.load(ckpt)

def trace(label, text):
    print(f"\n{'='*60}")
    print(f"  {label}: {text}")
    print(f"{'='*60}")

    # Step 1: encode
    input_keys = e.dictionary.encode(text)
    print(f"\n[1] dictionary.encode() -> {input_keys}")
    for k in input_keys:
        entry = e.dictionary.entries.get(k)
        if entry:
            sf = entry.surface_forms.get("zh") or entry.surface_forms.get("en") or k
            print(f"    {k} -> surface_form: {sf}")

    # Step 2: decode input_keys (what would fallback give?)
    decoded_input = e.dictionary.decode(input_keys)
    print(f"\n[2] dictionary.decode(input_keys) -> {decoded_input!r}")

    # Step 3: SNN forward
    snn_out = e.snn.forward(input_keys)
    sorted_out = sorted(snn_out.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n[3] snn.forward() -> top10 output keys:")
    for k, v in sorted_out:
        entry = e.dictionary.entries.get(k)
        sf = "???"
        if entry:
            sf = entry.surface_forms.get("zh") or entry.surface_forms.get("en") or k
        print(f"    {k:8s} score={v:.3f}  surface_form={sf}")

    # Step 4: decode SNN output
    output_keys = [k for k, _ in sorted_out]
    decoded_output = e.dictionary.decode(output_keys)
    print(f"\n[4] dictionary.decode(snn_output) -> {decoded_output!r}")

    # Step 5: what anchored_decode gives
    from ai.garden.garden_engine import _anchored_decode
    anchored = _anchored_decode(snn_out, input_keys, e.dictionary)
    print(f"\n[5] anchored_decode() -> {anchored!r}")

# Test with a math question
trace("MATH", "1+1=?")

# Test with logic
trace("LOGIC", "true OR false")

# Test with reasoning
trace("REASONING", "Mallory is taller than Judy. Judy is taller than Niaj. Who is tallest?")
