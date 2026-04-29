"""
RAG retriever for pet health knowledge base.
Adapted from the DocuBot retrieval pattern (Module 4).
Loads species-specific and common symptom docs, chunks them,
and scores chunks against a query using keyword overlap.
"""

import os
import glob


class HealthRetriever:
    def __init__(self, docs_folder=None):
        if docs_folder is None:
            docs_folder = os.path.join(os.path.dirname(__file__), "pet_health_docs")
        self.docs_folder = docs_folder
        self.documents = self._load_documents()
        self.chunks = self._chunk_documents()

    def _load_documents(self):
        docs = []
        for path in glob.glob(os.path.join(self.docs_folder, "*.md")):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            docs.append((os.path.basename(path), text))
        return docs

    def _chunk_documents(self):
        chunks = []
        for filename, text in self.documents:
            for para in text.split("\n\n"):
                para = para.strip()
                if len(para) > 30:
                    chunks.append((filename, para))
        return chunks

    def _score(self, query, text):
        query_words = set(query.lower().split())
        text_words = text.lower().split()
        return sum(1 for w in text_words if w in query_words)

    def retrieve(self, query, species=None, top_k=4):
        """
        Return top_k chunks ranked by keyword overlap.
        If species is provided ('dog' or 'cat'), boost chunks from
        species-specific docs so they rank above generic ones.
        """
        scored = []
        for filename, chunk in self.chunks:
            score = self._score(query, chunk)
            if score == 0:
                continue
            # boost species-specific docs
            if species:
                if species.lower() in filename.lower():
                    score += 2
            scored.append((score, filename, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(fname, chunk) for _, fname, chunk in scored[:top_k]]

    def get_sources(self, results):
        return list(dict.fromkeys(fname for fname, _ in results))
