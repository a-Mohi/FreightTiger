import chromadb
import pandas as pd

_model = None


def embed(texts):
    """Embed a list of texts."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(texts, normalize_embeddings=True).tolist()


def build_note_database(notes_csv):
    """Build an in-memory vector database from the notes."""
    notes = pd.read_csv(notes_csv)
    client = chromadb.EphemeralClient()
    try:
        client.delete_collection("notes")
    except Exception:
        pass
    collection = client.create_collection("notes", metadata={"hnsw:space": "cosine"})

    texts = [f"{row.applies_to}: {row.note}" for row in notes.itertuples()]
    collection.add(
        ids=list(notes["note_id"]),
        documents=list(notes["note"]),
        embeddings=embed(texts),
        metadatas=[{"applies_to": row.applies_to, "date": row.date} for row in notes.itertuples()],
    )
    return collection


def find_notes(collection, route, week_of, how_many=4):
    """Retrieve notes related to a route and week."""
    question = f"Why did freight cost rise on the {route} route in the week of {week_of:%Y-%m-%d}?"
    result = collection.query(
        query_embeddings=embed([question]),
        n_results=how_many,
        where={"applies_to": {"$in": [route, "All Routes"]}},
    )
    notes = []
    for i in range(len(result["ids"][0])):
        notes.append({
            "note_id": result["ids"][0][i],
            "text": result["documents"][0][i],
            "date": pd.Timestamp(result["metadatas"][0][i]["date"]),
            "applies_to": result["metadatas"][0][i]["applies_to"],
        })
    return notes
