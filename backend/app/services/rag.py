import os
from typing import List, Dict, Any

# Gracefully catch chromadb import errors to bypass C++ Build Tools dependency
try:
    import chromadb
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
    CHROMA_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    CHROMA_AVAILABLE = False

# Simple mock collection to emulate ChromaDB when not installed
class MockCollection:
    def __init__(self, name: str):
        self.name = name
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.ids: List[str] = []

    def count(self) -> int:
        return len(self.documents)

    def add(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)

    def query(self, query_texts: List[str], n_results: int = 2) -> Dict[str, Any]:
        # Simple keyword matching search fallback
        query = query_texts[0].lower()
        matches = []
        for doc in self.documents:
            # Score match by word overlap
            score = sum(1 for word in query.split() if word in doc.lower())
            matches.append((score, doc))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        top_docs = [m[1] for m in matches[:n_results]]
        
        return {"documents": [top_docs]}

if CHROMA_AVAILABLE:
    class LocalMockEmbeddingFunction(EmbeddingFunction):
        def __call__(self, input: Documents) -> Embeddings:
            embeddings = []
            for text in input:
                val = abs(hash(text)) % 1000
                vector = [float((val + i) % 10) / 10.0 for i in range(1536)]
                embeddings.append(vector)
            return embeddings

class RAGService:
    def __init__(self):
        if CHROMA_AVAILABLE:
            try:
                os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
                self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
                self.embedding_fn = LocalMockEmbeddingFunction()
                self.rules_col = self.client.get_or_create_collection(
                    name="cricket_rules", 
                    embedding_function=self.embedding_fn
                )
                self.matches_col = self.client.get_or_create_collection(
                    name="match_summaries", 
                    embedding_function=self.embedding_fn
                )
            except Exception:
                # If something fails inside persistent storage connection, fallback to mock collections
                self._init_mocks()
        else:
            self._init_mocks()
            
        self._seed_collections()

    def _init_mocks(self):
        self.rules_col = MockCollection("cricket_rules")
        self.matches_col = MockCollection("match_summaries")

    def _seed_collections(self):
        # Seed rules
        if self.rules_col.count() == 0:
            self.rules_col.add(
                documents=[
                    "Leg Before Wicket (LBW) is a method of dismissing a batsman. If the ball hits the batsman's body (usually leg) without touching the bat first, and in the umpire's judgment, the ball would have gone on to hit the wickets, the batsman is out LBW.",
                    "A Super Over is used to break a tie in limited-overs matches. Each team bats for one over (six balls), and the team scoring the most runs wins. Wickets are limited to two.",
                    "Powerplays are fielding restrictions in limited-overs matches. In ODIs, the first 10 overs have max 2 fielders outside the 30-yard circle. In T20Is, the first 6 overs have the same restriction."
                ],
                metadatas=[{"topic": "lbw"}, {"topic": "super_over"}, {"topic": "powerplay"}],
                ids=["rule_lbw", "rule_super_over", "rule_powerplay"]
            )

        # Seed matches
        if self.matches_col.count() == 0:
            self.matches_col.add(
                documents=[
                    "The 2019 ICC Cricket World Cup Final was played at Lord's on 14 July 2019. The match ended in a tie, and the subsequent Super Over also ended in a tie. England won on the boundary countback rule.",
                    "The 2021 World Test Championship (WTC) Final was won by New Zealand, who defeated India by 8 wickets at the Rose Bowl, Southampton.",
                    "The 2007 T20 World Cup Final saw India defeat Pakistan by 5 runs in Johannesburg, marking the birth of the global T20 revolution."
                ],
                metadatas=[{"year": 2019}, {"year": 2021}, {"year": 2007}],
                ids=["match_wc_2019", "match_wtc_2021", "match_t20_2007"]
            )

    def query_rules(self, query: str, limit: int = 2) -> List[str]:
        results = self.rules_col.query(query_texts=[query], n_results=limit)
        docs = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
        return docs

    def query_matches(self, query: str, limit: int = 2) -> List[str]:
        results = self.matches_col.query(query_texts=[query], n_results=limit)
        docs = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
        return docs

# Avoid import dependency issues in config
from app.config import settings

rag_service = RAGService()
