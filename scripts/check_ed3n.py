import json
d = json.load(open('data/checkpoints/ed3n_full.json', 'r', encoding='utf-8'))
net = d.get('network', {})
groups = net.get('groups', {})
print("Network groups:", list(groups.keys()))
for g, grp in groups.items():
    neurons = grp.get('neurons', {})
    total_conns = sum(len(n.get('connections', {})) for n in neurons.values())
    print(f"  {g}: {len(neurons)} neurons, {total_conns} connections")

# Check reflex patterns structure
rp = d.get('reflex_patterns', {})
print(f"\nReflex patterns: {len(rp)} total")
if rp:
    sample = list(rp.items())[:3]
    for k, v in sample:
        print(f"  {k}: {type(v).__name__}")
