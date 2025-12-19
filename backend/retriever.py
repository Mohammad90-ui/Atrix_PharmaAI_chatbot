"""
Retrieval Module
Implements semantic search using sentence transformers and FAISS.
"""
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Dict, Tuple
import re


class Retriever:
    """Handles embedding generation and semantic search."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize with a sentence transformer model."""
        self.model = SentenceTransformer(model_name)
        self.doc_index = None
        self.excel_index = None
        self.doc_chunks = []
        self.excel_chunks = []
        
    def build_index(self, doc_chunks: List[Dict], excel_chunks: List[Dict]):
        """Build FAISS indices for both sources."""
        # Build doc index
        if doc_chunks:
            doc_texts = [chunk['content'] for chunk in doc_chunks]
            doc_embeddings = self.model.encode(doc_texts, show_progress_bar=False)
            
            dimension = doc_embeddings.shape[1]
            self.doc_index = faiss.IndexFlatL2(dimension)
            self.doc_index.add(doc_embeddings.astype('float32'))
            self.doc_chunks = doc_chunks
        
        # Build excel index
        if excel_chunks:
            excel_texts = [chunk['content'] for chunk in excel_chunks]
            excel_embeddings = self.model.encode(excel_texts, show_progress_bar=False)
            
            dimension = excel_embeddings.shape[1]
            self.excel_index = faiss.IndexFlatL2(dimension)
            self.excel_index.add(excel_embeddings.astype('float32'))
            self.excel_chunks = excel_chunks
    
    def classify_query(self, query: str) -> str:
        """Determine which source to prioritize based on query type."""
        query_lower = query.lower()
        
        # Excel indicators - structured data queries
        excel_keywords = [
            'dose', 'dosing', 'dosage', 'mg', 'frequency',
            'adverse event', 'ae', 'aes', 'side effect',
            'severity', 'severe', 'moderate', 'mild',
            'outcome', 'resolved', 'ongoing',
            'indication', 'population', 'reported'
        ]
        
        # Doc indicators - narrative and label cautions
        doc_keywords = [
            'caution', 'label', 'note', 'guidance', 'monitoring',
            'warning', 'recommendation', 'context', 'trial summary',
            'background', 'description'
        ]
        
        excel_score = sum(1 for kw in excel_keywords if kw in query_lower)
        doc_score = sum(1 for kw in doc_keywords if kw in query_lower)
        
        if doc_score > excel_score:
            return 'doc'
        elif excel_score > doc_score:
            return 'excel'
        else:
            return 'both'
    
    def needs_clarification(self, query: str) -> Tuple[bool, str]:
        """Check if query needs clarification (e.g., missing drug name)."""
        query_lower = query.lower()
        
        # Check for dosing/AE/severity queries without drug name
        needs_drug_keywords = [
            'dose', 'dosing', 'dosage', 'adverse event', 'ae', 'aes',
            'severity', 'outcome', 'caution', 'side effect'
        ]
        
        # Common drug names to check against
        drug_list = [
            'imatinib', 'pembrolizumab', 'metformin', 'nivolumab',
            'trastuzumab', 'atezolizumab', 'durvalumab', 'osimertinib'
        ]
        
        # Check if query has drug-specific keywords but no drug name
        has_drug_keyword = any(kw in query_lower for kw in needs_drug_keywords)
        has_drug_name = any(drug in query_lower for drug in drug_list)
        
        # Also check for indication-based queries
        has_indication = any(ind in query_lower for ind in [
            'melanoma', 'nsclc', 'diabetes', 'breast cancer', 'cml'
        ])
        
        # Exception for general safety/medical queries that should be handled by guardrails
        # e.g. "dosage adjustment for renal impairment" should go to safety check, not clarification
        is_general_medical = any(term in query_lower for term in ['renal', 'kidney', 'hepatic', 'liver', 'impairment'])
        
        if has_drug_keyword and not (has_drug_name or has_indication) and not is_general_medical:
            return True, "Could you specify the drug name to help me answer accurately?"
        
        return False, ""
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        source_preference: str = 'both'
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Search for relevant chunks.
        Returns: (doc_results, excel_results)
        """
        query_embedding = self.model.encode([query]).astype('float32')
        
        doc_results = []
        excel_results = []
        
        # Search doc if needed
        if source_preference in ['doc', 'both'] and self.doc_index:
            distances, indices = self.doc_index.search(query_embedding, top_k)
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.doc_chunks):
                    result = self.doc_chunks[idx].copy()
                    result['score'] = float(dist)
                    doc_results.append(result)
        
        # Search excel if needed
        if source_preference in ['excel', 'both'] and self.excel_index:
            distances, indices = self.excel_index.search(query_embedding, top_k)
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.excel_chunks):
                    result = self.excel_chunks[idx].copy()
                    result['score'] = float(dist)
                    excel_results.append(result)
        
        return doc_results, excel_results
    
    def get_best_results(
        self,
        doc_results: List[Dict],
        excel_results: List[Dict],
        max_results: int = 3
    ) -> Tuple[List[Dict], str]:
        """
        Select the best results and determine primary source.
        Returns: (selected_results, primary_source)
        """
        # Combine and sort by score
        all_results = []
        for res in doc_results:
            res['source_type'] = 'doc'
            all_results.append(res)
        for res in excel_results:
            res['source_type'] = 'excel'
            all_results.append(res)
        
        # Sort by score (lower is better for L2 distance)
        all_results.sort(key=lambda x: x['score'])
        
        # Take top results
        selected = all_results[:max_results]
        
        # Determine primary source
        if not selected:
            return [], 'none'
        
        doc_count = sum(1 for r in selected if r['source_type'] == 'doc')
        excel_count = sum(1 for r in selected if r['source_type'] == 'excel')
        
        if doc_count > 0 and excel_count > 0:
            primary_source = 'both'
        elif doc_count > 0:
            primary_source = 'doc'
        else:
            primary_source = 'excel'
        
        return selected, primary_source
