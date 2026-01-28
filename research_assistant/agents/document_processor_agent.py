from models.data_models import AgentInput, AgentOutput
import time
import re
from typing import Dict, List


class DocumentProcessorAgent:
    """
    Agent 1: Document Processor
    
    Responsible for:
    - Receiving the document and research question
    - Parsing and cleaning the document text
    - Breaking document into searchable chunks/paragraphs with location tracking
    - Validating input data
    - Tracking page/line numbers for precise references
    """
    
    def __init__(self):
        self.name = "DocumentProcessorAgent"
        self.description = "Processes and parses the input document with location tracking"
    
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Process the input document
        
        Args:
            input_data: Contains document text and research question
            
        Returns:
            AgentOutput with parsed document chunks
        """
        start_time = time.time()
        
        try:
            data = input_data.data
            document = data.get("document", "").strip()
            question = data.get("question", "").strip()
            
            # Validate inputs
            if not document:
                return AgentOutput(
                    data=None,
                    status="error",
                    errors=["No document provided"],
                    processing_time=time.time() - start_time,
                    output_preview="Error: Empty document"
                )
            
            if not question:
                return AgentOutput(
                    data=None,
                    status="error",
                    errors=["No research question provided"],
                    processing_time=time.time() - start_time,
                    output_preview="Error: No question"
                )
            
            # Clean the document
            cleaned_document = self._clean_text(document)
            
            # Split into paragraphs/chunks with location tracking
            paragraphs_with_locations = self._split_into_paragraphs_with_locations(cleaned_document)
            
            # Create sentences for more granular search
            sentences = self._split_into_sentences(cleaned_document)
            
            # Create indexed document for AI analysis
            indexed_document = self._create_indexed_document(paragraphs_with_locations)
            
            processed_data = {
                "question": question,
                "original_document": document,
                "cleaned_document": cleaned_document,
                "indexed_document": indexed_document,
                "paragraphs": [p["text"] for p in paragraphs_with_locations],
                "paragraphs_with_locations": paragraphs_with_locations,
                "sentences": sentences,
                "word_count": len(cleaned_document.split()),
                "paragraph_count": len(paragraphs_with_locations),
                "sentence_count": len(sentences)
            }
            
            preview = f"Processed document: {len(paragraphs)} paragraphs, {len(sentences)} sentences, {processed_data['word_count']} words"
            
            return AgentOutput(
                data=processed_data,
                status="success",
                metadata={
                    "paragraphs": len(paragraphs),
                    "sentences": len(sentences),
                    "words": processed_data['word_count']
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
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
        return text.strip()
    
    def _split_into_paragraphs(self, text: str) -> list:
        """Split text into paragraphs (legacy method for backward compatibility)"""
        # Split by double newlines or single newlines
        paragraphs = re.split(r'\n\n+|\n', text)
        # Filter empty paragraphs and strip whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20]
        
        # If no paragraphs found, treat whole text as one
        if not paragraphs:
            paragraphs = [text]
        
        return paragraphs
    
    def _split_into_paragraphs_with_locations(self, text: str) -> List[Dict]:
        """
        Split text into paragraphs with location tracking
        Returns list of dicts with text, paragraph number, and line range
        """
        lines = text.split('\n')
        paragraphs_with_locations = []
        current_paragraph_lines = []
        paragraph_start_line = 1
        current_line = 1
        paragraph_num = 1
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check if this is a paragraph break (empty line or significant whitespace change)
            if not stripped_line:
                # Save accumulated paragraph
                if current_paragraph_lines:
                    paragraph_text = ' '.join(current_paragraph_lines)
                    if len(paragraph_text) > 20:  # Only include substantial paragraphs
                        paragraphs_with_locations.append({
                            "text": paragraph_text,
                            "paragraph_number": paragraph_num,
                            "start_line": paragraph_start_line,
                            "end_line": current_line - 1,
                            "location_ref": f"P{paragraph_num}:L{paragraph_start_line}-{current_line-1}"
                        })
                        paragraph_num += 1
                    current_paragraph_lines = []
                    paragraph_start_line = current_line + 1
            else:
                current_paragraph_lines.append(stripped_line)
            
            current_line += 1
        
        # Don't forget the last paragraph
        if current_paragraph_lines:
            paragraph_text = ' '.join(current_paragraph_lines)
            if len(paragraph_text) > 20:
                paragraphs_with_locations.append({
                    "text": paragraph_text,
                    "paragraph_number": paragraph_num,
                    "start_line": paragraph_start_line,
                    "end_line": current_line - 1,
                    "location_ref": f"P{paragraph_num}:L{paragraph_start_line}-{current_line-1}"
                })
        
        # If no paragraphs found, treat whole text as one
        if not paragraphs_with_locations:
            paragraphs_with_locations = [{
                "text": text,
                "paragraph_number": 1,
                "start_line": 1,
                "end_line": len(lines),
                "location_ref": f"P1:L1-{len(lines)}"
            }]
        
        return paragraphs_with_locations
    
    def _create_indexed_document(self, paragraphs_with_locations: List[Dict]) -> str:
        """
        Create a document with location markers for AI analysis
        Format: [P#:L#-#] paragraph text
        """
        indexed_parts = []
        for para in paragraphs_with_locations:
            indexed_parts.append(f"[{para['location_ref']}] {para['text']}")
        
        return '\n\n'.join(indexed_parts)
    
    def _split_into_sentences(self, text: str) -> list:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return sentences
