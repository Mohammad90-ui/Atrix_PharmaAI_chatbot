"""
Retrieval Module
Implements semantic search using sentence transformers and FAISS.
"""
from fastembed import TextEmbedding

import numpy as np
from typing import List, Dict, Tuple
import re


import os

class Retriever:
    """Handles embedding generation and semantic search."""
    
    def __init__(self, model_name: str = 'BAAI/bge-small-en-v1.5'):
        """Initialize with a FastEmbed model (ONNX based, lightweight)."""
        # FastEmbed handles model download
        # For Vercel/Serverless, we must use /tmp for writing files
        cache_dir = None
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            cache_dir = "/tmp/fastembed_cache"
            os.makedirs(cache_dir, exist_ok=True)
            
        self.model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)
        self.doc_embeddings = None
        self.excel_embeddings = None
        self.doc_chunks = []
        self.excel_chunks = []
        
    def build_index(self, doc_chunks: List[Dict], excel_chunks: List[Dict]):
        """Build Numpy-based indices for both sources."""
        # Build doc index
        if doc_chunks:
            doc_texts = [chunk['content'] for chunk in doc_chunks]
            # FastEmbed returns a generator, convert to numpy array
            self.doc_embeddings = np.array(list(self.model.embed(doc_texts)))
            self.doc_chunks = doc_chunks
        
        # Build excel index
        if excel_chunks:
            excel_texts = [chunk['content'] for chunk in excel_chunks]
            self.excel_embeddings = np.array(list(self.model.embed(excel_texts)))
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
        Search for relevant chunks using Numpy (L2 distance).
        Returns: (doc_results, excel_results)
        """
        query_embedding = list(self.model.embed([query]))[0]
        
        doc_results = []
        excel_results = []
        
        # Search doc if needed
        if source_preference in ['doc', 'both'] and self.doc_embeddings is not None and len(self.doc_embeddings) > 0:
            # L2 Distance: sum((a-b)^2)
            dists = np.sum((self.doc_embeddings - query_embedding)**2, axis=1)
            # Get top k indices (smallest distance)
            indices = np.argsort(dists)[:top_k]
            
            for idx in indices:
                result = self.doc_chunks[idx].copy()
                result['score'] = float(dists[idx])
                doc_results.append(result)
        
        # Search excel if needed
        if source_preference in ['excel', 'both'] and self.excel_embeddings is not None and len(self.excel_embeddings) > 0:
            dists = np.sum((self.excel_embeddings - query_embedding)**2, axis=1)
            indices = np.argsort(dists)[:top_k]
            
            for idx in indices:
                result = self.excel_chunks[idx].copy()
                result['score'] = float(dists[idx])
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
