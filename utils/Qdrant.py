from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models


class Qdrant():

    def __init__(self):
        load_dotenv()
        QDRANT_URL = os.getenv("QDRANT_URL")
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

        self.collection = os.getenv("QDRANT_COLLECTION")
        vs = os.getenv("VECTOR_SIZE")
        self.vector_size: Optional[int] = int(vs) if vs and vs.strip().lower() != "none" else None
        self.top_k: int = int(os.getenv("TOP_K"))
        st = os.getenv("SCORE_THRESHOLD")
        self.score_threshold: Optional[float] = float(st) if st and st.strip().lower() != "none" else None
        self.ef_search: int = int(os.getenv("EF_SEARCH"))

        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        return

    def build_filter(
        self,
        category: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        service_type: Optional[str] = None,
        has_price: Optional[bool] = None,
        kb_id: Optional[str] = None,
        extra_match: Optional[Dict[str, Any]] = None,
    ) -> Optional[models.Filter]:
        must: List[models.FieldCondition] = []

        def eq(key: str, value: Any):
            must.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))

        if category:
            eq("meta.category", category)
        if vehicle_type:
            eq("meta.vehicle_type", vehicle_type)
        if service_type:
            eq("meta.service_type", service_type)
        if has_price is not None:
            eq("meta.price_info", has_price)
        if kb_id:
            eq("kb_id", kb_id)
        if extra_match:
            for k, v in extra_match.items():
                eq(k, v)

        return models.Filter(must=must) if must else None

    def search(
        self,
        vector: List[float],
        *,
        top_k: Optional[int] = None,
        category: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        service_type: Optional[str] = None,
        has_price: Optional[bool] = None,
        kb_id: Optional[str] = None,
        score_threshold: Optional[float] = None,
        include_payload: Optional[List[str]] = None,
    ) -> list[models.ScoredPoint]:
        if self.vector_size is not None and len(vector) != self.vector_size:
            pass  # при желании замените на raise

        flt = self.build_filter(
            category=category,
            vehicle_type=vehicle_type,
            service_type=service_type,
            has_price=has_price,
            kb_id=kb_id,
        )

        with_payload: Any = True
        if include_payload is not None:
            with_payload = {"include": include_payload}

        results =  self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k or self.top_k,
            query_filter=flt,
            search_params=models.SearchParams(hnsw_ef=self.ef_search),
            score_threshold=self.score_threshold if score_threshold is None else score_threshold,
            with_payload=with_payload,
        )

        texts: List[str] = []
        for r in results:
            payload = (r.payload or {})
            t = payload.get("text") or payload.get("title") or ""
            t = str(t).strip()
            if t:
                texts.append(t)

        return "\n\n".join(texts)

