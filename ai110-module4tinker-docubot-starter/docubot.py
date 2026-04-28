import os
import re
import glob
import logging

logger = logging.getLogger(__name__)


class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        self.docs_folder = docs_folder
        self.llm_client = llm_client
        self.idf = {}
        self.documents = self.load_documents()
        self.index = self.build_index(self.documents)

    def load_documents(self):
        docs = []
        for path in glob.glob(os.path.join(self.docs_folder, "*.*")):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    docs.append((os.path.basename(path), f.read()))
        return docs

    def build_index(self, documents):
        index = {}
        for filename, text in documents:
            for word in set(re.sub(r"[^\w\s]", " ", text.lower()).split()):
                index.setdefault(word, []).append(filename)

        total = len(documents)
        self.idf = {word: total / len(files) for word, files in index.items()}
        logger.info("Built index: %d tokens from %d documents", len(index), total)
        return index

    def score_document(self, query, text):
        query_words = set(re.sub(r"[^\w\s]", " ", query.lower()).split())
        text_lower = text.lower()
        return sum(self.idf.get(w, 1.0) for w in query_words if w in text_lower)

    def retrieve(self, query, top_k=3):
        if not query or not query.strip():
            logger.warning("Empty query — returning no results")
            return []

        retrieval_query = self.llm_client.expand_query(query) if self.llm_client else query
        query_words = set(re.sub(r"[^\w\s]", " ", retrieval_query.lower()).split())

        candidates = set(
            fname
            for word in query_words
            for fname in self.index.get(word, [])
        )

        if not candidates:
            logger.warning("No candidates found for: %s", query)
            return []

        doc_lookup = dict(self.documents)
        scored = sorted(
            [(self.score_document(retrieval_query, doc_lookup[f]), f, doc_lookup[f]) for f in candidates],
            reverse=True
        )

        results = [(f, t) for _, f, t in scored[:top_k]]
        logger.info("Retrieved %d docs — top: %s", len(results), [f for f, _ in results])
        return results

    def answer_retrieval_only(self, query, top_k=3):
        snippets = self.retrieve(query, top_k=top_k)
        if not snippets:
            return "I do not know based on these docs."
        return "\n---\n".join(f"[{fname}]\n{text}\n" for fname, text in snippets)

    def answer_rag(self, query, top_k=3):
        if self.llm_client is None:
            raise RuntimeError("RAG mode requires an LLM client.")
        snippets = self.retrieve(query, top_k=top_k)
        if not snippets:
            return "I do not know based on these docs."
        return self.llm_client.answer_from_snippets(query, snippets)

    def full_corpus_text(self):
        return "\n\n".join(text for _, text in self.documents)
