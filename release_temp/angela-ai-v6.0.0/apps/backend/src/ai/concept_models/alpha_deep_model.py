import asyncio
import datetime
import logging
from typing import Any

import numpy as np
import tensorflow as tf
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


class AlphaDeepModel:
    """Implements the Alpha Deep Model for data compression and learning mechanisms.
    The compression part is now implemented using PCA.
    """

    def __init__(self, n_components: int = 2):
        """Initializes the AlphaDeepModel."""
        self.model_state: dict[str, Any] = {"version": "1.0", "parameters": {}}
        # Dummy model for the 'learn' part
        self.dummy_model = tf.keras.Sequential(
            [tf.keras.layers.Dense(1, input_shape=(10,))],
        )
        # Real model for the 'compress' part
        self.compressor = PCA(n_components=n_components)
        self.is_compressor_trained = False
        logger.info(
            f"AlphaDeepModel initialized with a dummy TensorFlow model and a PCA compressor (n_components={n_components}).",
        )

    async def learn(self, data: dict[str, Any]) -> dict[str, Any]:
        """Simulates the learning process using a dummy TensorFlow model."""
        logger.info(
            f"AlphaDeepModel learning from data (type: {data.get('type', 'N/A')}) using TensorFlow (simplified).",
        )
        await asyncio.sleep(0.2)  # Keep simulating async operation

        # Simulate some data processing for TensorFlow
        if "vector_data" in data:
            try:
                input_data = tf.constant(data["vector_data"], dtype=tf.float32)
                input_data = tf.reshape(input_data, (1, -1))
                _ = self.dummy_model(input_data)
                learning_output = {
                    "model_processed": True,
                    "input_shape": input_data.shape,
                }
            except Exception as e:
                learning_output = {"model_processed": False, "error": str(e)}
                logger.error(f"TensorFlow dummy learning failed: {e}", exc_info=True)
        else:
            learning_output = {
                "model_processed": False,
                "reason": "No 'vector_data' for dummy TF model.",
            }

        self.model_state["parameters"]["last_update"] = (
            datetime.datetime.now().isoformat()
        )
        self.model_state["parameters"]["learning_progress"] = 1.0  # Dummy value for now
        return {
            "status": "learned",
            "model_state": self.model_state,
            "learning_output": learning_output,
        }

    async def train_compressor(self, dataset: np.ndarray):
        """Trains the PCA compressor on a given dataset.

        Args:
            dataset (np.ndarray): A 2D numpy array where rows are samples and columns are features.

        """
        logger.info(f"Training PCA compressor on dataset with shape {dataset.shape}...")
        # PCA fitting is CPU-bound, so we run it in a thread to be non-blocking.
        await asyncio.to_thread(self.compressor.fit, dataset)
        self.is_compressor_trained = True
        logger.info("PCA compressor trained successfully.")

    async def compress(self, data_vector: np.ndarray) -> dict[str, Any]:
        """Compresses a data vector using the trained PCA model.

        Args:
            data_vector (np.ndarray): The 1D data vector to compress.

        Returns:
            Dict[str, Any]: A dictionary containing the compression status and the compressed data.

        """
        if not self.is_compressor_trained:
            return {"status": "failed", "error": "Compressor has not been trained yet."}

        logger.info(f"Compressing data vector of shape {data_vector.shape}")
        # Reshape 1D array to 2D array for the transformer
        if data_vector.ndim == 1:
            data_vector = data_vector.reshape(1, -1)

        compressed_vector = await asyncio.to_thread(
            self.compressor.transform,
            data_vector,
        )
        return {"status": "compressed", "data": compressed_vector.flatten().tolist()}

    async def reconstruct(self, compressed_vector: np.ndarray) -> dict[str, Any]:
        """Reconstructs the original data from a compressed vector.

        Args:
            compressed_vector (np.ndarray): The 1D compressed vector.

        Returns:
            Dict[str, Any]: A dictionary containing the reconstruction status and the reconstructed data.

        """
        if not self.is_compressor_trained:
            return {"status": "failed", "error": "Compressor has not been trained yet."}

        logger.info(
            f"Reconstructing from data vector of shape {compressed_vector.shape}",
        )
        # Reshape 1D array to 2D array for the transformer
        if compressed_vector.ndim == 1:
            compressed_vector = compressed_vector.reshape(1, -1)

        reconstructed_vector = await asyncio.to_thread(
            self.compressor.inverse_transform,
            compressed_vector,
        )
        return {
            "status": "reconstructed",
            "data": reconstructed_vector.flatten().tolist(),
        }


if __name__ == "__main__":
    import asyncio

    import numpy as np

    async def main():
        # --- Part 1: Test Learning (unchanged) ---
        model = AlphaDeepModel(n_components=2)
        print("\n--- Test Learning ---")
        training_data = {
            "type": "text_corpus",
            "vector_data": np.random.rand(10).tolist(),
        }
        learning_result = await model.learn(training_data)
        print(f"Learning Result: {learning_result}")

        # --- Part 2: Test new Compression/Reconstruction cycle ---
        print("\n--- Test Compression & Reconstruction ---")
        # Create a sample dataset where data is correlated, so PCA makes sense
        np.random.seed(0)
        dataset = np.random.rand(100, 4) * [1, 0.1, 3, 0.2]  # 100 samples, 4 features

        # Train the compressor
        await model.train_compressor(dataset)

        # Take a single data point to test
        original_point = dataset[0]
        print(f"\nOriginal data point: {np.round(original_point, 4)}")

        # Compress it
        compressed_result = await model.compress(original_point)
        print(f"Compressed result:   {np.round(compressed_result.get('data', []), 4)}")

        # Reconstruct it
        reconstructed_result = await model.reconstruct(
            np.array(compressed_result.get("data")),
        )
        print(
            f"Reconstructed data:  {np.round(reconstructed_result.get('data', []), 4)}",
        )

        # Calculate reconstruction error
        error = np.sum((original_point - reconstructed_result.get("data")) ** 2)
        print(f"Reconstruction Error (Sum of Squared Differences): {error:.4f}")

    asyncio.run(main())
