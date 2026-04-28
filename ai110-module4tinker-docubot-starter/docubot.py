"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import re
import glob
import logging

logger = logging.getLogger(__name__)

class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client
        self.idf = {}  # Populated by build_index

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.documents)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, documents):
        """
        Build an inverted index mapping lowercase words to the filenames that contain them.

        Design: strip punctuation, lowercase all tokens, deduplicate per document
        so a word appearing 100 times in one file doesn't skew the index structure.
        """
        index = {}
        for filename, text in documents:
            words = re.sub(r"[^\w\s]", " ", text.lower()).split()
            for word in set(words):  # set() deduplicates — each word listed once per doc
                if word not in index:
                    index[word] = []
                index[word].append(filename)

        # Precompute IDF weights: rare words score higher than common ones
        # IDF = total docs / number of docs containing the word
        total = len(documents)
        self.idf = {word: total / len(filenames) for word, filenames in index.items()}

        logger.info("Built index with %d unique tokens from %d documents", len(index), len(documents))
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        Score a document by counting how many unique query words appear in its text.

        Design: equal weight per matching word — simple, transparent, and sufficient
        for a focused knowledge base where each doc covers one clear topic.
        """
        query_words = set(re.sub(r"[^\w\s]", " ", query.lower()).split())
        text_lower = text.lower()
        # Weight each matching word by its IDF score — rare words contribute more
        return sum(self.idf.get(word, 1.0) for word in query_words if word in text_lower)

    def retrieve(self, query, top_k=3):
        """
        Return the top_k most relevant documents for the given query.

        Design: use the index to pre-filter to candidate docs (only those containing
        at least one query word), then score and rank. Pre-filtering avoids scoring
        every document and ensures zero-match docs never appear in results.
        """
        if not query or not query.strip():
            logger.warning("Empty query passed to retrieve — returning no results")
            return []

        # Expand query to technical terms if LLM client is available
        retrieval_query = query
        if self.llm_client is not None:
            retrieval_query = self.llm_client.expand_query(query)

        query_words = set(re.sub(r"[^\w\s]", " ", retrieval_query.lower()).split())

        # Pre-filter: collect filenames that contain at least one query word
        candidate_filenames = set()
        for word in query_words:
            for filename in self.index.get(word, []):
                candidate_filenames.add(filename)

        if not candidate_filenames:
            logger.warning("No candidate documents found for query: %s", query)
            return []

        # Score only the candidate documents
        doc_lookup = {filename: text for filename, text in self.documents}
        scored = []
        for filename in candidate_filenames:
            text = doc_lookup.get(filename, "")
            score = self.score_document(query, text)
            scored.append((score, filename, text))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [(filename, text) for _, filename, text in scored[:top_k]]
        logger.info("Retrieved %d docs for query: %s — top: %s", len(results), query, [f for f, _ in results])
        return results

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        formatted = []
        for filename, text in snippets:
            formatted.append(f"[{filename}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
