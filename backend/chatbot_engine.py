"""
Chatbot Module
Implements grounded response generation with safety guardrails.
"""
from typing import List, Dict, Tuple, Optional
import re
from datetime import datetime


class ChatbotEngine:
    """Generates grounded responses based on retrieved context."""
    
    def __init__(self):
        self.conversation_history = {}  # session_id -> list of turns
        self.max_history = 5  # Keep last 5 turns for context
        
    def _get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        return self.conversation_history[session_id]
    
    def _add_to_history(self, session_id: str, user_msg: str, assistant_msg: str, sources_used: str):
        """Add a turn to conversation history."""
        history = self._get_history(session_id)
        history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_msg,
            'assistant_message': assistant_msg,
            'sources_used': sources_used
        })
        # Keep only last N turns
        if len(history) > self.max_history:
            history.pop(0)
    
    def _extract_context_from_history(self, session_id: str) -> str:
        """Extract relevant context from recent conversation."""
        history = self._get_history(session_id)
        if not history:
            return ""
        
        # Get the last turn to understand context
        last_turn = history[-1]
        context_info = []
        
        # Extract drug names and topics mentioned
        last_user_msg = last_turn['user_message'].lower()
        last_assistant_msg = last_turn['assistant_message'].lower()
        
        # Common drug names
        drugs = ['imatinib', 'pembrolizumab', 'metformin', 'nivolumab', 
                'trastuzumab', 'atezolizumab', 'durvalumab', 'osimertinib']
        
        for drug in drugs:
            if drug in last_user_msg or drug in last_assistant_msg:
                context_info.append(f"Previously discussed drug: {drug}")
        
        return " | ".join(context_info)
    
    def _resolve_pronouns(self, query: str, session_id: str) -> str:
        """Resolve pronouns like 'that', 'it' using conversation history."""
        history = self._get_history(session_id)
        if not history:
            return query
        
        query_lower = query.lower()
        
        # Check for pronouns
        pronouns = ['that', 'it', 'this', 'them']
        has_pronoun = any(pronoun in query_lower.split() for pronoun in pronouns)
        
        if has_pronoun and history:
            # Get last mentioned drug
            last_turn = history[-1]
            last_msg = last_turn['user_message'] + " " + last_turn['assistant_message']
            
            drugs = ['imatinib', 'pembrolizumab', 'metformin', 'nivolumab', 
                    'trastuzumab', 'atezolizumab', 'durvalumab', 'osimertinib']
            
            for drug in drugs:
                if drug.lower() in last_msg.lower():
                    # Replace pronoun with drug name
                    enhanced_query = query + f" (referring to {drug})"
                    return enhanced_query
        
        return query
    
    def _check_safety_guardrails(self, query: str) -> Tuple[bool, Optional[str]]:
        """Check if query violates safety guidelines."""
        query_lower = query.lower()
        
        # Medical advice indicators
        medical_advice_keywords = [
            'should i take', 'can i take', 'prescribe', 'recommend taking',
            'what should i do', 'treatment plan', 'medical advice',
            'diagnose', 'can i stop', 'should i stop'
        ]
        
        # Clinical decision keywords - refined to allow grounded lookup
        clinical_decision_keywords = [
            'change my dose', 'switch to', 'should i stop'
        ]
        
        # Harmful / Inappropriate keywords
        harmful_keywords = [
            'bomb', 'suicide', 'kill', 'murder', 'illegal', 'hack', 'poison',
            'weapon', 'terror', 'drug abuse', 'high', 'recreational'
        ]
        
        for keyword in medical_advice_keywords + clinical_decision_keywords:
            if keyword in query_lower:
                return True, (
                    "I cannot provide medical advice or prescriptive recommendations. "
                    "Please consult the official drug label documentation or a qualified "
                    "healthcare professional for clinical decisions."
                )
        
        for keyword in harmful_keywords:
             if keyword in query_lower:
                 return True, "I cannot fulfill this request as it violates safety policies."
        
        return False, None
    
    def _is_relevant(self, query: str, result: Dict) -> bool:
        """Check if result is relevant using strict ratio matching."""
        # Clean and tokenize query
        # Minimal stop words to ensure important terms (dose, adjustment) are counted
        stop_words = {
            'what', 'is', 'the', 'for', 'in', 'of', 'a', 'an', 'to', 'and', 'or', 'are', 
            'about', 'tell', 'me', 'please', 'provide', 'give', 'how', 'much', 'can', 'i', 
            'take', 'should', 'with', 'my', 'does', 'have', 'any', 'list', 'show', 'details',
            'information', 'regarding', 'suggest', 'describe', 'explain', 'check',
            'mentioned', 'mention', 'guidance', 'guide', 'label', 'discussed', 'discuss',
            'reference', 'notes', 'note', 'described', 'finding', 'findings'
        }
        
        # Extract terms
        query_terms = re.findall(r'\w+', query.lower())
        key_terms = {t for t in query_terms if t not in stop_words}
        
        # If no key terms, rely on semantic search score only (pass-through)
        if not key_terms:
            return True
            
        # Check against result content and metadata
        content = result.get('content', '').lower()
        data = result.get('structured_data', {})
        
        # Construct a representation of the result
        result_text = content + " " + str(data.get('drug_name', '')) + " " + \
                      str(data.get('indication', '')) + " " + str(data.get('ae_terms', '')) + " " + \
                      str(data.get('dose', '')) + " " + str(data.get('severity', ''))
        result_text = result_text.lower()
        
        # Synonym Mapping to fix vocabulary mismatch
        synonyms = {
            'side': ['adverse', 'events', 'ae', 'reaction', 'toxicity', 'safety'],
            'effect': ['adverse', 'events', 'ae', 'reaction', 'outcome', 'efficacy'],
            'effects': ['adverse', 'events', 'ae', 'reaction', 'outcomes'],
            'adverse': ['side', 'effect', 'toxicity', 'safety'],
            'renal': ['kidney', 'nephro', 'crcl', 'creatinine', 'gfr'],
            'kidney': ['renal', 'nephro'],
            'hepatic': ['liver', 'bilirubin', 'alt', 'ast'],
            'liver': ['hepatic'],
            'dose': ['dosage', 'dosing', 'schedule', 'amount', 'administer', 'administration'],
            'dosage': ['dose', 'dosing', 'schedule', 'amount', 'administration'],
            'guidance': ['recommendation', 'instruction', 'protocol', 'note', 'label', 'prescribing'],
            'monitoring': ['check', 'assess', 'measure', 'test', 'exam'],
            'label': ['prescribing', 'guidance', 'smpc', 'uspi', 'package'],
            'indication': ['usage', 'treat', 'diagnosis', 'condition', 'disease'],
        }

        # Calculate matching ratio
        matches = 0
        matched_terms = set()
        
        for term in key_terms:
            term_matched = False
            # 1. Direct match
            if term in result_text: 
                matches += 1
                matched_terms.add(term)
                continue
            
            # 2. Plural/Singular
            if term.endswith('s') and term[:-1] in result_text:
                matches += 1
                matched_terms.add(term)
                continue
            if term + 's' in result_text:
                matches += 1
                matched_terms.add(term)
                continue
                
            # 3. Synonym match
            if term in synonyms:
                for syn in synonyms[term]:
                    if syn in result_text:
                        matches += 1
                        matched_terms.add(term) # Count the term as matched
                        term_matched = True
                        break
            if term_matched:
                continue
                
        # Calculate ratio
        # RELAXED LOGIC: We just need significant overlap.
        # If ANY important medical term matches (e.g. drug name, condition), we accept it.
        # Preventing "Space" -> "Trastuzumab" (0 matches).
        
        if len(key_terms) == 0:
            return True
            
        ratio = matches / len(key_terms)
        
        # Threshold: Just require AT LEAST ONE meaningful match (Ratio > 0)
        # But if query is long (>3 terms), require slightly more confidence?
        # Actually, "Any Match" is safest for "False Negatives", provided stop words are aggressive.
        # "Space" (1 term) -> 0 match -> Fail.
        # "Cardio monitoring" (2 terms) -> "Monitoring" match -> Pass.
        
        return matches > 0

    def _is_greeting(self, query: str) -> bool:
        """Check if the query is a simple greeting."""
        greetings = {'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'thanks', 'thank you'}
        cleaned = re.sub(r'[^\w\s]', '', query.lower()).strip()
        return cleaned in greetings

    def _extract_relevant_snippet(self, content: str, query: str) -> str:
        """Extract the most relevant window of text containing query terms."""
        content_lower = content.lower()
        query_terms = [t for t in re.findall(r'\w+', query.lower()) if len(t) > 3] # Ignora short words
        
        if not query_terms:
            return content[:500]
            
        # Find best window
        best_window = content[:500]
        max_density = 0
        
        # Split content into sentences or chunks of 200 chars
        sentences = content.split('. ')
        
        for i in range(len(sentences)):
            # Create a window of 3 sentences
            window_slice = sentences[i:i+3]
            window_text = ". ".join(window_slice)
            
            # Count term density
            count = sum(1 for t in query_terms if t in window_text.lower())
            
            if count > max_density:
                max_density = count
                best_window = window_text
        
        # If we found a good window, return it (cleaned)
        if max_density > 0:
            return "..." + best_window + "..."
            
        return content[:500]

    def generate_response(
        self,
        query: str,
        retrieved_results: List[Dict],
        primary_source: str,
        session_id: str
    ) -> Tuple[str, str]:
        """
        Generate a grounded response based on retrieved context.
        Returns: (response, source_citation)
        """
        # Check safety guardrails
        is_unsafe, safety_msg = self._check_safety_guardrails(query)
        if is_unsafe:
            self._add_to_history(session_id, query, safety_msg, "none")
            return safety_msg, "none"
            
        # Check if greeting
        if self._is_greeting(query):
            response = "Hello! I am your Clinical Trial Assistant. How can I help you regarding drug dosages, adverse events, or clinical contexts?"
            self._add_to_history(session_id, query, response, "none")
            return response, "none"
        
        # RELEVANCE FILTERING
        # 1. Score Filter (exclude very distant semantic matches)
        score_filtered = [r for r in retrieved_results if r.get('score', 0) < 1.4]
        
        # 2. Keyword Relevance Filter
        relevant_results = [r for r in score_filtered if self._is_relevant(query, r)]
        
        # If no relevant results after filtering
        if not relevant_results:
            response = "I apologize, but I couldn't find relevant information regarding your query in the provided clinical trial documents."
            self._add_to_history(session_id, query, response, "none")
            return response, "none"
            
        # Use filtered results
        retrieved_results = relevant_results

        # Build response from retrieved context
        response_parts = []
        sources_used = set()
        
        # Group results by source
        doc_results = [r for r in retrieved_results if r['source_type'] == 'doc']
        excel_results = [r for r in retrieved_results if r['source_type'] == 'excel']
        
        # Generate response based on source type
        if excel_results:
            response_parts.extend(self._format_excel_results(excel_results, query))
            sources_used.add("Pharma_Clinical_Trial_AllDrugs.xlsx")
        
        if doc_results:
            response_parts.extend(self._format_doc_results(doc_results, query))
            sources_used.add("Pharma_Clinical_Trial_Notes.docx")
        
        # Combine response
        if response_parts:
            response = "\n\n".join(response_parts)
        else:
            response = "I don't know based on the available data."
            sources_used = set()
        
        # Format source citation
        if sources_used:
            source_citation = ", ".join(sorted(sources_used))
        else:
            source_citation = "none"
        
        # Add to history
        self._add_to_history(session_id, query, response, source_citation)
        
        return response, source_citation
    
    def _format_excel_results(self, results: List[Dict], query: str) -> List[str]:
        """Format Excel results into readable text."""
        formatted = []
        query_lower = query.lower()
        
        # Determine what information to extract
        show_dose = 'dose' in query_lower or 'dosing' in query_lower or 'dosage' in query_lower
        show_ae = any(kw in query_lower for kw in ['ae', 'adverse', 'side effect'])
        show_severity = 'severity' in query_lower or 'severe' in query_lower
        show_outcome = 'outcome' in query_lower or 'resolved' in query_lower
        
        # Group by drug
        drug_data = {}
        for result in results[:3]:  # Top 3 results
            data = result.get('structured_data', {})
            drug = data.get('drug_name', 'Unknown')
            
            if drug not in drug_data:
                drug_data[drug] = []
            drug_data[drug].append(data)
        
        # Format each drug's information
        for drug, records in drug_data.items():
            parts = [f"**{drug}**:"]
            
            # Collect unique values
            indications = set()
            doses = set()
            aes = set()
            severities = set()
            outcomes = set()
            
            for rec in records:
                if rec.get('indication'):
                    indications.add(rec['indication'])
                if rec.get('dose'):
                    doses.add(rec['dose'])
                if rec.get('ae_terms'):
                    aes.add(rec['ae_terms'])
                if rec.get('severity'):
                    severities.add(rec['severity'])
                if rec.get('outcome'):
                    outcomes.add(rec['outcome'])
            
            # Add relevant information
            if indications:
                parts.append(f"- Indication: {', '.join(indications)}")
            
            if doses and show_dose:
                parts.append(f"- Dose: {', '.join(doses)}")
            
            if aes and show_ae:
                parts.append(f"- Adverse Events: {', '.join(aes)}")
            
            if severities and show_severity:
                parts.append(f"- Severity: {', '.join(severities)}")
            
            if outcomes and show_outcome:
                parts.append(f"- Outcome: {', '.join(outcomes)}")
            
            # If no specific fields requested, show all
            if not (show_dose or show_ae or show_severity or show_outcome):
                if doses:
                    parts.append(f"- Dose: {', '.join(doses)}")
                if aes:
                    parts.append(f"- Adverse Events: {', '.join(aes)}")
                if severities:
                    parts.append(f"- Severity: {', '.join(severities)}")
            
            formatted.append("\n".join(parts))
        
        return formatted
    
    def _format_doc_results(self, results: List[Dict], query: str) -> List[str]:
        """Format Doc results into readable text."""
        formatted = []
        
        for result in results[:2]:  # Top 2 doc results
            content = result.get('content', '')
            
            # For table data, format nicely
            if result.get('type') == 'table':
                structured = result.get('structured_data', {})
                if structured:
                    parts = []
                    for key, value in structured.items():
                        if value:
                            parts.append(f"**{key}**: {value}")
                    if parts:
                        formatted.append("\n".join(parts))
            else:
                # For paragraphs, SMART SNIPPET EXTRACTION
                if content:
                    snippet = self._extract_relevant_snippet(content, query)
                    formatted.append(snippet)
        
        return formatted
