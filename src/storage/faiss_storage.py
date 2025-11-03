"""FAISS vector storage for semantic search and retrieval."""

import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer


class FAISSStorage:
    """Vector storage backend using FAISS."""

    def __init__(
        self,
        index_path: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
        dimension: Optional[int] = None,
    ):
        """Initialize FAISS storage.

        Args:
            index_path: Directory path for storing FAISS index
            embedding_model: Name of the sentence-transformers model
            dimension: Vector dimension (auto-detected if not provided)
        """
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        self.encoder = SentenceTransformer(embedding_model)

        # Get dimension from model if not provided
        if dimension is None:
            dimension = self.encoder.get_sentence_embedding_dimension()

        self.dimension = dimension

        # Initialize or load FAISS index
        self.index_file = self.index_path / "index.faiss"
        self.metadata_file = self.index_path / "metadata.pkl"

        if self.index_file.exists():
            self.index = faiss.read_index(str(self.index_file))
            with open(self.metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            # Create a new index (using Inner Product for cosine similarity)
            self.index = faiss.IndexFlatIP(dimension)
            self.metadata = []

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity.

        Args:
            vectors: Input vectors

        Returns:
            Normalized vectors
        """
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / norms

    def add_texts(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        """Add texts to the vector store.

        Args:
            texts: List of text strings to add
            metadata: Optional metadata for each text

        Returns:
            List of IDs for the added texts
        """
        # Generate embeddings
        embeddings = self.encoder.encode(texts, convert_to_numpy=True)
        embeddings = self._normalize_vectors(embeddings)

        # Get current size for IDs
        start_id = self.index.ntotal

        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))

        # Add metadata
        if metadata is None:
            metadata = [{} for _ in texts]

        for i, (text, meta) in enumerate(zip(texts, metadata)):
            self.metadata.append({
                'id': start_id + i,
                'text': text,
                **meta
            })

        # Save index and metadata
        self.save()

        return list(range(start_id, start_id + len(texts)))

    def search(
        self,
        query: str,
        k: int = 5,
        filter_fn: Optional[callable] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Search for similar texts.

        Args:
            query: Query text
            k: Number of results to return
            filter_fn: Optional function to filter results

        Returns:
            List of (score, metadata) tuples
        """
        # Generate query embedding
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        query_embedding = self._normalize_vectors(query_embedding)

        # Search in FAISS
        scores, indices = self.index.search(query_embedding.astype('float32'), k * 2)

        # Apply filter if provided
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]

            if filter_fn is None or filter_fn(meta):
                results.append((float(score), meta))

            if len(results) >= k:
                break

        return results

    def search_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search by metadata fields.

        Args:
            metadata_filter: Dictionary of metadata key-value pairs to match
            k: Optional limit on number of results

        Returns:
            List of matching metadata dictionaries
        """
        results = []
        for meta in self.metadata:
            # Check if all filter criteria match
            if all(meta.get(key) == value for key, value in metadata_filter.items()):
                results.append(meta)

            if k and len(results) >= k:
                break

        return results

    def delete_by_ids(self, ids: List[int]) -> None:
        """Delete items by their IDs.

        Note: FAISS doesn't support deletion, so we rebuild the index.

        Args:
            ids: List of IDs to delete
        """
        ids_set = set(ids)

        # Filter metadata
        new_metadata = [m for m in self.metadata if m['id'] not in ids_set]

        # Rebuild index
        if new_metadata:
            texts = [m['text'] for m in new_metadata]
            embeddings = self.encoder.encode(texts, convert_to_numpy=True)
            embeddings = self._normalize_vectors(embeddings)

            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index.add(embeddings.astype('float32'))

            # Update IDs
            for i, meta in enumerate(new_metadata):
                meta['id'] = i

            self.metadata = new_metadata
        else:
            # Empty index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []

        self.save()

    def save(self) -> None:
        """Save the FAISS index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_file))
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)

    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Get all stored metadata.

        Returns:
            List of all metadata dictionaries
        """
        return self.metadata.copy()

    def count(self) -> int:
        """Get the number of items in the index.

        Returns:
            Number of items
        """
        return self.index.ntotal

    def clear(self) -> None:
        """Clear all data from the index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self.save()
