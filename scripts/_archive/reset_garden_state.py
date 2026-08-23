import json

path = r"D:\Projects\Unified-AI-Project\data\checkpoints\training_state.json"
with open(path) as f:
    state = json.load(f)

# Keep step 4 (ED3N done), remove 5 and 6 (GARDEN)
state["completed_steps"] = [4]
state["garden_batch_done"] = 0
state["garden_samples"] = 0

with open(path, "w") as f:
    json.dump(state, f, indent=2)

print("Reset: completed_steps=[4], garden_batch_done=0")
print("ED3N preserved: epochs=%s, samples=%s" % (state.get("ed3n_epochs_done"), state.get("ed3n_samples")))
