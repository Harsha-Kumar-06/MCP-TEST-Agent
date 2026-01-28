from models.data_models import AgentInput, AgentOutput
import time
from typing import List, Dict


class SummaryAgent:
    """
    Agent 4: Summary Agent
    
    Responsible for:
    - Generating final summary from extracted data
    - Formatting citations properly
    - Creating the final response for the user
    - Handling "no data found" scenarios
    """
    
    def __init__(self):
        self.name = "SummaryAgent"
        self.description = "Generates final summary and formatted response"
    
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Generate final summary with citations
        
        Args:
            input_data: Contains extracted citations and findings
            
        Returns:
            AgentOutput with formatted summary
        """
        start_time = time.time()
        
        try:
            data = input_data.data
            question = data.get("question", "")
            has_citations = data.get("has_citations", False)
            citations = data.get("citations", [])
            key_findings = data.get("key_findings", [])
            message = data.get("message")
            
            # If no relevant content was found
            if not has_citations or message:
                final_response = {
                    "status": "no_data",
                    "question": question,
                    "answer": "Couldn't fetch data from the given records",
                    "explanation": "The document does not contain information relevant to your research question. Please try with a different question or provide a document that contains related information.",
                    "citations": [],
                    "summary": None
                }
                
                return AgentOutput(
                    data=final_response,
                    status="success",
                    metadata={"result_type": "no_data"},
                    processing_time=time.time() - start_time,
                    output_preview="No relevant data found in document"
                )
            
            # Generate summary
            summary = self._generate_summary(question, citations, key_findings)
            
            # Format citations for display
            formatted_citations = self._format_citations(citations)
            
            final_response = {
                "status": "success",
                "question": question,
                "answer": summary,
                "citations": formatted_citations,
                "key_findings": key_findings,
                "total_citations": len(citations),
                "summary": summary
            }
            
            preview = f"Generated summary with {len(citations)} citations"
            
            return AgentOutput(
                data=final_response,
                status="success",
                metadata={
                    "result_type": "success",
                    "citations_count": len(citations)
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
    
    def _generate_summary(self, question: str, citations: List[Dict], key_findings: List[str]) -> str:
        """Generate a summary based on the citations"""
        if not citations:
            return "No relevant information found."
        
        # Build summary from citations
        summary_parts = []
        
        summary_parts.append(f"Based on the document analysis for your question: \"{question}\"\n")
        summary_parts.append("\n📋 **SUMMARY:**\n")
        
        # Add key points from top citations
        top_citations = citations[:3]
        for i, citation in enumerate(top_citations, 1):
            text = citation.get("text", "")
            # Truncate if too long
            if len(text) > 200:
                text = text[:200] + "..."
            summary_parts.append(f"\n{i}. {text}")
        
        # Add key findings if available
        if key_findings:
            summary_parts.append("\n\n🔍 **KEY FINDINGS:**\n")
            for finding in key_findings[:3]:
                summary_parts.append(f"\n{finding}")
        
        return "".join(summary_parts)
    
    def _format_citations(self, citations: List[Dict]) -> List[Dict]:
        """Format citations for final display"""
        formatted = []
        
        for citation in citations:
            formatted.append({
                "number": citation.get("citation_number"),
                "text": citation.get("text"),
                "highlighted": citation.get("highlighted_text"),
                "type": citation.get("type"),
                "relevance": f"{citation.get('relevance_score', 0):.1%}" if citation.get('relevance_score') else "N/A",
                "keywords_matched": citation.get("matched_keywords", [])
            })
        
        return formatted
