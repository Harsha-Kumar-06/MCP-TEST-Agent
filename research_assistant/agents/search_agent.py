from models.data_models import AgentInput, AgentOutput
import time
import re
from typing import List, Tuple


class SearchAgent:
    """
    Agent 2: Search Agent
    
    Responsible for:
    - Analyzing the research question to extract keywords
    - Searching through document chunks for relevant information
    - Ranking results by relevance
    - Identifying if information exists in the document
    """
    
    def __init__(self):
        self.name = "SearchAgent"
        self.description = "Searches document for relevant information"
    
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Search for relevant information in the document
        
        Args:
            input_data: Contains processed document and question
            
        Returns:
            AgentOutput with search results
        """
        start_time = time.time()
        
        try:
            data = input_data.data
            question = data.get("question", "")
            paragraphs = data.get("paragraphs", [])
            sentences = data.get("sentences", [])
            
            # Extract keywords from question
            keywords = self._extract_keywords(question)
            
            # Search paragraphs
            paragraph_results = self._search_content(paragraphs, keywords)
            
            # Search sentences for more precise matches
            sentence_results = self._search_content(sentences, keywords)
            
            # Determine if relevant content was found
            has_results = len(paragraph_results) > 0 or len(sentence_results) > 0
            
            search_data = {
                "question": question,
                "keywords": keywords,
                "paragraph_matches": paragraph_results[:5],  # Top 5 paragraphs
                "sentence_matches": sentence_results[:10],   # Top 10 sentences
                "has_relevant_content": has_results,
                "total_matches": len(paragraph_results) + len(sentence_results),
                "original_document": data.get("original_document", "")
            }
            
            if has_results:
                preview = f"Found {len(paragraph_results)} relevant paragraphs, {len(sentence_results)} relevant sentences"
            else:
                preview = "No relevant information found for the given question"
            
            return AgentOutput(
                data=search_data,
                status="success",
                metadata={
                    "keywords_used": keywords,
                    "paragraphs_matched": len(paragraph_results),
                    "sentences_matched": len(sentence_results),
                    "has_results": has_results
                },
                processing_time=time.time() - start_time,
                output_preview=preview
            )
            
        except Exception as e:
            return AgentOutput(
                data=None,
                status="error",
                errors=[str(e)],
                processing_time=time.time() - start_time,
                output_preview=f"Error: {str(e)}"
            )
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract important keywords from the research question"""
        # Common stop words to ignore
        stop_words = {
            'what', 'where', 'when', 'why', 'how', 'who', 'which',
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did',
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'into',
            'about', 'can', 'could', 'would', 'should', 'will',
            'this', 'that', 'these', 'those', 'it', 'its',
            'me', 'my', 'i', 'you', 'your', 'we', 'our', 'they', 'their',
            'tell', 'find', 'give', 'show', 'explain', 'describe'
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Also include important phrases (bigrams)
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in stop_words or words[i+1] not in stop_words:
                bigrams.append(f"{words[i]} {words[i+1]}")
        
        return list(set(keywords + bigrams[:3]))
    
    def _search_content(self, content_list: List[str], keywords: List[str]) -> List[Tuple[str, float]]:
        """Search content and return matches with relevance scores"""
        results = []
        
        for content in content_list:
            score = self._calculate_relevance(content, keywords)
            if score > 0:
                results.append({
                    "text": content,
                    "score": score,
                    "matched_keywords": self._get_matched_keywords(content, keywords)
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results
    
    def _calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matches"""
        text_lower = text.lower()
        score = 0
        
        for keyword in keywords:
            # Count occurrences
            count = text_lower.count(keyword.lower())
            if count > 0:
                # Weight by keyword length (longer = more specific)
                score += count * (1 + len(keyword) / 10)
        
        # Normalize by text length to avoid bias toward longer texts
        if len(text) > 0:
            score = score / (len(text.split()) / 10)
        
        return round(score, 3)
    
    def _get_matched_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Get list of keywords that matched in the text"""
        text_lower = text.lower()
        return [kw for kw in keywords if kw.lower() in text_lower]
