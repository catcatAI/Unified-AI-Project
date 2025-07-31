import yaml
import toml

def generate_pyproject_deps():
    """
    Reads dependency_config.yaml and updates pyproject.toml
    with the optional dependencies.
    """
    with open("dependency_config.yaml", "r") as f:
        dep_config = yaml.safe_load(f)

    with open("pyproject.toml", "r") as f:
        pyproject_data = toml.load(f)

    optional_deps = {}
    for group, details in dep_config.get("installation", {}).items():
        optional_deps[group] = details.get("packages", [])

    pyproject_data["project"]["optional-dependencies"] = optional_deps

    with open("pyproject.toml", "w") as f:
        toml.dump(pyproject_data, f)

    print("pyproject.toml has been updated with dependencies from dependency_config.yaml")

if __name__ == "__main__":
    generate_pyproject_deps()
