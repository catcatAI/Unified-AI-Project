"""Verify training results against architecture expectations."""
import json
import os

def main():
    print("=" * 60)
    print("  TRAINING RESULTS VERIFICATION")
    print("=" * 60)

    # 1. ED3N network
    ed3n = json.load(open("data/checkpoints/ed3n_full.json", "r", encoding="utf-8"))
    groups = ed3n.get("network", {}).get("groups", {})
    total_neurons = sum(len(g.get("neurons", {})) for g in groups.values())
    total_conns = sum(
        sum(len(n.get("connections", {})) for n in g.get("neurons", {}).values())
        for g in groups.values()
    )
    reflex_patterns = ed3n.get("reflex_patterns", [])
    print("\n1. ED3N Network:")
    print(f"   Neurons:   {total_neurons}")
    print(f"   Edges:     {total_conns}")
    print(f"   Reflexes:  {len(reflex_patterns)}")
    print(f"   Status:    {'PASS' if total_neurons > 0 else 'FAIL'}")

    # 2. GARDEN dictionary
    garden_dict = json.load(open("data/checkpoints/garden_checkpoint/dictionary.json", "r", encoding="utf-8"))
    raw = garden_dict.get("entries", {})
    entry_count = len(raw) if isinstance(raw, list) else len(raw.values())
    print("\n2. GARDEN Dictionary:")
    print(f"   Entries:   {entry_count}")
    print("   Limit:     10000")
    print(f"   Status:    {'PASS' if entry_count <= 10000 else 'FAIL'}")

    # 3. GARDEN SNN size
    snn_path = "data/checkpoints/garden_checkpoint/snn.pt.npy"
    if os.path.exists(snn_path):
        size_mb = os.path.getsize(snn_path) / 1024 / 1024
        print("\n3. GARDEN SNN:")
        print(f"   Size:      {size_mb:.1f} MB")
        print(f"   Status:    {'PASS' if size_mb < 500 else 'FAIL'}")
    else:
        print("\n3. GARDEN SNN: not found")

    # 4. Coordinator persistence
    coord = json.load(open("data/checkpoints/coordinator_state.json", "r", encoding="utf-8"))
    domains = list(coord.get("domain_map", {}).keys())
    print("\n4. Training Coordinator:")
    print(f"   Domains:   {domains}")
    for d, r in coord.get("domain_map", {}).items():
        print(f"     {d}: {r['trained_count']} samples, acc={r['accuracy']:.4f}")
    print(f"   Status:    {'PASS' if len(domains) >= 2 else 'FAIL'}")

    # 5. Training report
    report = json.load(open("data/checkpoints/training_report.json", "r", encoding="utf-8"))
    print("\n5. Training Report:")
    print(f"   Samples:   {report.get('samples_loaded', 0)}")
    print(f"   ED3N:      {report.get('ed3n_trained', 0)} trained")
    print(f"   GARDEN:    {report.get('garden_trained', 0)} trained")
    print(f"   Dict size: {report.get('dictionary_size', 0)}")

    # 6. JointTrainer / SequenceTrainer
    joint_path = "data/checkpoints/joint_trainer.json"
    seq_path = "data/checkpoints/sequence_trainer.json"
    if os.path.exists(joint_path):
        joint = json.load(open(joint_path, "r", encoding="utf-8"))
        history = joint.get("history", [])
        print("\n6. JointTrainer:")
        print(f"   History:   {len(history)} entries")
        if history:
            last = history[-1]
            print(f"   Last loss: {last.get('loss', 'N/A')}")
            print(f"   Last acc:  {last.get('accuracy', 'N/A')}")
    if os.path.exists(seq_path):
        seq = json.load(open(seq_path, "r", encoding="utf-8"))
        print("\n7. SequenceTrainer:")
        print(f"   History:   {len(seq.get('history', []))} entries")

    # 7. ED3N file sizes
    ed3n_size = os.path.getsize("data/checkpoints/ed3n_full.json") / 1024
    print("\n8. Checkpoint Sizes:")
    print(f"   ED3N:      {ed3n_size:.1f} KB")
    garden_total = sum(
        os.path.getsize(os.path.join("data/checkpoints/garden_checkpoint", f))
        for f in os.listdir("data/checkpoints/garden_checkpoint")
        if os.path.isfile(os.path.join("data/checkpoints/garden_checkpoint", f))
    )
    print(f"   GARDEN:    {garden_total/1024/1024:.1f} MB")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
