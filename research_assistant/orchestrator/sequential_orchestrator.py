from typing import List, Any
from models.data_models import AgentInput, AgentOutput, PipelineState
from agents.document_processor_agent import DocumentProcessorAgent
from agents.search_agent import SearchAgent
from agents.extraction_agent import ExtractionAgent
from agents.summary_agent import SummaryAgent
import time


class SequentialOrchestrator:
    """
    Orchestrates the sequential execution of Research Assistant agents.
    
    Pipeline Flow:
    1. DocumentProcessorAgent - Parse and chunk the document
    2. SearchAgent - Search for relevant information
    3. ExtractionAgent - Extract citations and key findings
    4. SummaryAgent - Generate final summary
    
    This orchestrator follows the Sequential Design Pattern where:
    - Agents execute in a predefined, linear order
    - Output from one agent serves as input for the next
    - No LLM is used for orchestration logic (predefined workflow)
    """
    
    def __init__(self):
        self.name = "ResearchAssistantOrchestrator"
        
        # Initialize agents in execution order
        self.agents = [
            DocumentProcessorAgent(),
            SearchAgent(),
            ExtractionAgent(),
            SummaryAgent()
        ]
        
        self.pipeline_state = PipelineState(total_steps=len(self.agents))
    
    async def run_pipeline(self, initial_input: Any) -> PipelineState:
        """
        Execute the complete sequential pipeline
        
        Args:
            initial_input: Contains document and research question
            
        Returns:
            PipelineState with complete execution history
        """
        print(f"\n{'='*60}")
        print(f"🔬 Starting Research Assistant Pipeline")
        print(f"{'='*60}\n")
        
        pipeline_start = time.time()
        current_input = AgentInput(data=initial_input)
        output = None
        
        for idx, agent in enumerate(self.agents):
            step_num = idx + 1
            self.pipeline_state.current_step = step_num
            
            print(f"[Step {step_num}/{len(self.agents)}] Executing: {agent.name}")
            print(f"{'-'*40}")
            
            # Execute agent
            output = await agent.execute(current_input)
            
            # Log step result
            step_record = {
                "step": step_num,
                "agent": agent.name,
                "status": output.status,
                "processing_time": output.processing_time,
                "metadata": output.metadata,
                "errors": output.errors,
                "output_preview": output.output_preview
            }
            self.pipeline_state.history.append(step_record)
            
            print(f"  Status: {output.status}")
            print(f"  Processing Time: {output.processing_time:.4f}s")
            print(f"  Preview: {output.output_preview}")
            
            # Check for errors - stop pipeline if critical
            if output.status == "error":
                print(f"\n❌ Pipeline stopped due to error in {agent.name}")
                print(f"   Errors: {output.errors}")
                break
            
            # Prepare input for next agent
            current_input = AgentInput(
                data=output.data,
                metadata={
                    "previous_agent": agent.name,
                    "step": step_num
                }
            )
            
            print()
        
        # Finalize pipeline state
        self.pipeline_state.final_output = output.data if output else None
        total_time = time.time() - pipeline_start
        
        print(f"{'='*60}")
        print(f"✅ Pipeline Execution Complete")
        print(f"Total Time: {total_time:.4f}s")
        print(f"Steps Completed: {self.pipeline_state.current_step}/{len(self.agents)}")
        print(f"{'='*60}\n")
        
        return self.pipeline_state
    
    def get_pipeline_summary(self) -> dict:
        """Get a summary of the pipeline execution"""
        total_processing_time = sum(
            step.get("processing_time", 0) or 0
            for step in self.pipeline_state.history
        )
        
        return {
            "total_steps": len(self.agents),
            "completed_steps": self.pipeline_state.current_step,
            "total_processing_time": total_processing_time,
            "step_details": self.pipeline_state.history,
            "success": all(
                step.get("status") == "success" 
                for step in self.pipeline_state.history
            )
        }
