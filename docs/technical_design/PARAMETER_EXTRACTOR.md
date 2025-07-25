# Parameter Extractor

The Parameter Extractor is a tool for extracting, mapping, and loading parameters from external models, particularly from the Hugging Face Hub.

## Usage

To use the Parameter Extractor, you need to create an instance of the `ParameterExtractor` class, providing the repository ID of the Hugging Face Hub model you want to use.

```python
from src.tools.parameter_extractor import ParameterExtractor

extractor = ParameterExtractor(repo_id="bert-base-uncased")
```

### Downloading Model Parameters

You can download model parameters from the Hugging Face Hub using the `download_model_parameters` method.

```python
model_path = extractor.download_model_parameters(filename="pytorch_model.bin")
```

### Mapping Parameters

You can map the downloaded parameters to a local model using the `map_parameters` method. This method requires a dictionary of mapping rules, where the keys are the names of the parameters in the source model and the values are the names of the parameters in the target model.

```python
mapping_rules = {
    "bert.embeddings.word_embeddings.weight": "embeddings.weight",
    "bert.pooler.dense.weight": "pooler.weight",
    "bert.pooler.dense.bias": "pooler.bias",
}

mapped_params = extractor.map_parameters(source_params, mapping_rules)
```

### Loading Parameters into a Model

You can load the mapped parameters into a local model using the `load_parameters_to_model` method.

```python
local_model = SimpleBert()
extractor.load_parameters_to_model(local_model, mapped_params)
```

## Example

For a complete example of how to use the Parameter Extractor, see the `scripts/run_parameter_extractor_example.py` script.
