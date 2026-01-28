from models.data_models import AgentInput, AgentOutput
import time
import re
from typing import List, Dict


class ExtractionAgent:
    """
    Agent 3: Extraction Agent
    
    Responsible for:
    - Extracting relevant passages from search results
    - Creating citations with context
    - Highlighting key information
    - Preparing data for summary generation
    """
    
    def __init__(self):
        self.name = "ExtractionAgent"
        self.description = "Extracts and formats relevant passages with citations"
    
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Extract relevant passages and create citations
        
        Args:
            input_data: Contains search results
            
        Returns:
            AgentOutput with extracted citations
        """
        start_time = time.time()
        
        try:
            data = input_data.data
            has_relevant_content = data.get("has_relevant_content", False)
            question = data.get("question", "")
            paragraph_matches = data.get("paragraph_matches", [])
            sentence_matches = data.get("sentence_matches", [])
            keywords = data.get("keywords", [])
            
            # If no relevant content found
            if not has_relevant_content:
                return AgentOutput(
                    data={
                        "question": question,
                        "has_citations": False,
                        "citations": [],
                        "key_findings": [],
                        "message": "Couldn't fetch data from the given records"
                    },
                    status="success",
                    metadata={"citations_found": 0},
                    processing_time=time.time() - start_time,
                    output_preview="No relevant information found in document"
                )
            
            # Extract citations from matches
            citations = self._create_citations(paragraph_matches, sentence_matches, keywords)
            
            # Extract key findings
            key_findings = self._extract_key_findings(sentence_matches, keywords)
            
            extraction_data = {
                "question": question,
                "has_citations": len(citations) > 0,
                "citations": citations,
                "key_findings": key_findings,
                "keywords_found": keywords,
                "message": None
            }
            
            preview = f"Extracted {len(citations)} citations and {len(key_findings)} key findings"
            
            return AgentOutput(
                data=extraction_data,
                status="success",
                metadata={
                    "citations_found": len(citations),
                    "key_findings_count": len(key_findings)
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
    
    def _create_citations(self, paragraphs: List[Dict], sentences: List[Dict], keywords: List[str]) -> List[Dict]:
        """Create formatted citations from matches"""
        citations = []
        citation_num = 1
        
        # Process top paragraph matches
        for match in paragraphs[:3]:
            text = match.get("text", "")
            highlighted_text = self._highlight_keywords(text, keywords)
            
            citations.append({
                "citation_number": citation_num,
                "type": "paragraph",
                "text": text,
                "highlighted_text": highlighted_text,
                "relevance_score": match.get("score", 0),
                "matched_keywords": match.get("matched_keywords", [])
            })
            citation_num += 1
        
        # Process top sentence matches (avoid duplicates from paragraphs)
        existing_texts = {c["text"] for c in citations}
        
        for match in sentences[:5]:
            text = match.get("text", "")
            if text not in existing_texts and not any(text in p for p in existing_texts):
                highlighted_text = self._highlight_keywords(text, keywords)
                
                citations.append({
                    "citation_number": citation_num,
                    "type": "sentence",
                    "text": text,
                    "highlighted_text": highlighted_text,
                    "relevance_score": match.get("score", 0),
                    "matched_keywords": match.get("matched_keywords", [])
                })
                citation_num += 1
                existing_texts.add(text)
        
        return citations
    
    def _highlight_keywords(self, text: str, keywords: List[str]) -> str:
        """Highlight keywords in text using **bold** markers"""
        highlighted = text
        for keyword in keywords:
            # Case-insensitive replacement with bold markers
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted = pattern.sub(f"**{keyword.upper()}**", highlighted)
        return highlighted
    
    def _extract_key_findings(self, sentences: List[Dict], keywords: List[str]) -> List[str]:
        """Extract key findings from sentence matches"""
        findings = []
        
        for match in sentences[:5]:
            text = match.get("text", "")
            matched_kw = match.get("matched_keywords", [])
            
            if matched_kw:
                finding = f"• {text}"
                findings.append(finding)
        
        return findings
