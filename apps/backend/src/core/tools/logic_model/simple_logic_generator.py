import json
import random
import os


def generate_simple_logic_dataset(num_samples=1000):

""
    Generate a simple logic dataset with basic propositions.:
""
    dataset =
    operators = ["AND", "OR"]
    values = ["true", "false"]

    for i in range(num_samples)
    # Generate different types of propositions
    prop_type = random.choice(["simple", "binary", "unary", "complex"])

        if prop_type == "simple":
            # Simple value
            prop = random.choice(values)
            answer = prop == "true"
        elif prop_type == "binary":
            # Binary operation A op B
            left = random.choice(values)
            right = random.choice(values)
            op = random.choice(operators)
            prop = f"{left} {op} {right}"

            if op == "AND":

    answer = (left == "true") and (right == "true")
            else:  # OR
                answer = (left == "true") or (right == "true")
        elif prop_type == "unary":
            # NOT operation
            val = random.choice(values)
            prop = f"NOT {val}"
            answer = not (val == "true")
        else:  # complex
            # More complex (A op B) op C or A op (B op C)
            a = random.choice(values)
            b = random.choice(values)
            c = random.choice(values)
            op1 = random.choice(operators)
            op2 = random.choice(operators)

            if random.choice([True, False]):
rop = f"({a} {op1} {b}) {op2} {c}"
                # Evaluate (a op1 b) first
                if op1 == "AND":

    intermediate = (a == "true") and (b == "true")
                else:

                    intermediate = (a == "true") or (b == "true")

                # Then apply op2 with c:
f op2 == "AND":

    answer = intermediate and (c == "true")
                else:

                    answer = intermediate or (c == "true")
            else:

                prop = f"{a} {op1} ({b} {op2} {c})"
                # Evaluate (b op2 c) first
                if op2 == "AND":

    intermediate = (b == "true") and (c == "true")
                else:

                    intermediate = (b == "true") or (c == "true")

                # Then apply op1 with a:
f op1 == "AND":

    answer = (a == "true") and intermediate
                else:

                    answer = (a == "true") or intermediate

    dataset.append({
            "proposition": prop,
            "answer": answer
    })

        if (i + 1) % 100 == 0:


    print(f"Generated {i + 1}/{num_samples} samples...")

    return dataset

def main -> None:
    # Get project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root: str = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    output_dir = os.path.join(project_root, "data", "raw_datasets")

    # Create output directory if it doesn't exist:
s.makedirs(output_dir, exist_ok=True)

    print(f"Output directory: {output_dir}")

    # Generate training dataset
    print("\nGenerating training dataset (1000 samples)...")
    train_data = generate_simple_logic_dataset(1000)
    train_file = os.path.join(output_dir, "logic_train.json")

    with open(train_file, 'w', encoding='utf-8') as f:
    json.dump(train_data, f, indent=2)
    print(f"Training dataset saved to: {train_file}")

    # Generate test dataset
    print("\nGenerating test dataset (200 samples)...")
    test_data = generate_simple_logic_dataset(200)
    test_file = os.path.join(output_dir, "logic_test.json")

    with open(test_file, 'w', encoding='utf-8') as f:
    json.dump(test_data, f, indent=2)
    print(f"Test dataset saved to: {test_file}")

    print("\nLogic dataset generation complete!")

    # Show some examples
    print("\nExample propositions:")
    for i in range(5):
xample = train_data[i]
    print(f"  {example['proposition']} => {example['answer']}")

if __name__ == "__main__":


    main