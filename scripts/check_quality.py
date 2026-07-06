"""Quick quality check on trained models."""
import json
import os
import sys

CKPT = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints")

def main():
    # ED3N stats
    ed3n_path = os.path.join(CKPT, "ed3n_full.json")
    if os.path.exists(ed3n_path):
        with open(ed3n_path, "r", encoding="utf-8") as f:
            ed3n = json.load(f)
        dict_entries = len(ed3n.get("dictionary", {}).get("entries", {}))
        reflex_count = len(ed3n.get("reflex", {}).get("patterns", {}))
        network_nodes = len(ed3n.get("network", {}).get("nodes", {}))
        print("=== ED3N ===")
        print(f"  Dictionary entries: {dict_entries}")
        print(f"  Reflex patterns:    {reflex_count}")
        print(f"  Network nodes:      {network_nodes}")
    else:
        print("ED3N checkpoint not found")

    # GARDEN stats
    garden_meta_path = os.path.join(CKPT, "garden_checkpoint", "engine_meta.json")
    if os.path.exists(garden_meta_path):
        with open(garden_meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        print("\n=== GARDEN ===")
        print(f"  Query count:  {meta.get('query_count', 0)}")
        print(f"  Learn count:  {meta.get('learn_count', 0)}")
    garden_dict_path = os.path.join(CKPT, "garden_checkpoint", "dictionary.json")
    if os.path.exists(garden_dict_path):
        with open(garden_dict_path, "r", encoding="utf-8") as f:
            gdict = json.load(f)
        raw_entries = gdict.get("entries", {})
        # entries can be dict or list
        if isinstance(raw_entries, dict):
            entries = raw_entries
        else:
            entries = {e.get("key", str(i)): e for i, e in enumerate(raw_entries)}
        print(f"  Dictionary entries: {len(entries)}")
        # Count Chinese vs English entries
        zh_count = 0
        for e in entries.values():
            forms = e.get("surface_forms", {})
            if isinstance(forms, dict):
                for sf in forms.values():
                    if any(ord(c) > 0x4E00 for c in str(sf)):
                        zh_count += 1
                        break
            elif isinstance(forms, list):
                for sf in forms:
                    if any(ord(c) > 0x4E00 for c in str(sf)):
                        zh_count += 1
                        break
        print(f"  Chinese entries:    {zh_count}")
        print(f"  English entries:    {len(entries) - zh_count}")
        # Sample entries
        print("\n  Sample entries:")
        for i, (k, v) in enumerate(list(entries.items())[:5]):
            forms = v.get("surface_forms", v.get("surface_form", ""))
            print(f"    {k}: {forms}")

    # Training coordinator
    coord_path = os.path.join(CKPT, "trainer_state.json")
    if os.path.exists(coord_path):
        with open(coord_path, "r", encoding="utf-8") as f:
            coord = json.load(f)
        print("\n=== Training Records ===")
        for domain, record in coord.get("domain_map", {}).items():
            count = record.get("trained_count", 0)
            acc = record.get("accuracy", "N/A")
            print(f"  {domain:15s}: {count:6d} samples, accuracy={acc}")

    # Joint trainer stats
    joint_path = os.path.join(CKPT, "joint_trainer.json")
    if os.path.exists(joint_path):
        with open(joint_path, "r", encoding="utf-8") as f:
            joint = json.load(f)
        print("\n=== JointTrainer ===")
        print(f"  Total steps:  {joint.get('total_steps', 'N/A')}")
        print(f"  Best accuracy: {joint.get('best_accuracy', 'N/A')}")

    # Sequence trainer stats
    seq_path = os.path.join(CKPT, "sequence_trainer.json")
    if os.path.exists(seq_path):
        with open(seq_path, "r", encoding="utf-8") as f:
            seq = json.load(f)
        print("\n=== SequenceTrainer ===")
        print(f"  Total steps:  {seq.get('total_steps', 'N/A')}")
        print(f"  Best accuracy: {seq.get('best_accuracy', 'N/A')}")

if __name__ == "__main__":
    main()
