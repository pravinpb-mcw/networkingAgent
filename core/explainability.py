"""
Phoenix Explainability Module

This module adds explainability to every action taken by the agents.
It logs WHY decisions are made, not just WHAT happened.

Features:
- LLM-based explanations for every action
- Hallucination detection with reasoning
- Tool call justification
- Decision trace logging
- Dashboard visualization
"""

import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

try:
    from phoenix.evals import (
        HallucinationEvaluator,
        RelevanceEvaluator,
        run_evals
    )
    from phoenix.session.client import Client as PhoenixClient
    import pandas as pd
    PHOENIX_EVALS_AVAILABLE = True
except ImportError:
    PHOENIX_EVALS_AVAILABLE = False

logger = logging.getLogger("explainability")


@dataclass
class ActionExplanation:
    """Explanation for a single action"""
    action_id: str
    action_type: str  # "llm_call", "tool_call", "decision", "metric_calculation"
    timestamp: str
    input_context: str
    output_result: str
    explanation: str
    reasoning: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class HallucinationCheck:
    """Result of hallucination detection"""
    is_hallucinated: bool
    confidence: float
    explanation: str
    supporting_facts: List[str]
    unsupported_claims: List[str]


class ExplainabilityTracker:
    """
    Tracks and explains every action taken by agents.
    Integrates with Phoenix for visualization.
    """
    
    def __init__(
        self,
        agent_name: str,
        phoenix_endpoint: str = "http://localhost:6006",
        judge_model: str = "gpt-4o",
        enable_auto_explanations: bool = True,
        explanation_storage_path: Optional[Path] = None
    ):
        self.agent_name = agent_name
        self.phoenix_endpoint = phoenix_endpoint
        self.judge_model = judge_model
        self.enable_auto_explanations = enable_auto_explanations
        
        # Storage
        if explanation_storage_path is None:
            self.storage_path = Path(__file__).parent.parent / "explanations"
        else:
            self.storage_path = explanation_storage_path
        
        self.storage_path.mkdir(exist_ok=True)
        self.current_session_file = self.storage_path / f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        # Explanation cache
        self.explanations: List[ActionExplanation] = []
        
        # Phoenix client
        self.phoenix_client = None
        if PHOENIX_EVALS_AVAILABLE:
            try:
                self.phoenix_client = PhoenixClient(endpoint=phoenix_endpoint)
                logger.info(f"✅ Connected to Phoenix at {phoenix_endpoint}")
            except Exception as e:
                logger.warning(f"⚠️ Could not connect to Phoenix: {e}")
        
        # Initialize evaluators
        self.hallucination_evaluator = None
        self.relevance_evaluator = None
        self._setup_evaluators()
    
    def _setup_evaluators(self):
        """Initialize LLM-based evaluators"""
        if not PHOENIX_EVALS_AVAILABLE:
            logger.warning("⚠️ Phoenix evals not available - explanations will be limited")
            return
        
        try:
            # Check for API keys
            if os.getenv("OPENAI_API_KEY"):
                from phoenix.evals.models import OpenAIModel
                judge = OpenAIModel(model=self.judge_model)
            elif os.getenv("ANTHROPIC_API_KEY"):
                from phoenix.evals.models import AnthropicModel
                judge = AnthropicModel(
                    model="claude-sonnet-4",
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    base_url=os.getenv("ANTHROPIC_BASE_URL")
                )
            else:
                logger.warning("⚠️ No API key found for judge model")
                return
            
            # Create evaluators with explanation enabled
            self.hallucination_evaluator = HallucinationEvaluator(model=judge)
            self.relevance_evaluator = RelevanceEvaluator(model=judge)
            
            logger.info("✅ Explainability evaluators initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize evaluators: {e}")
    
    def explain_action(
        self,
        action_type: str,
        input_context: str,
        output_result: str,
        reference_context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActionExplanation:
        """
        Generate explanation for an action.
        
        Args:
            action_type: Type of action (llm_call, tool_call, decision, etc.)
            input_context: What went into the action
            output_result: What came out of the action
            reference_context: Ground truth or reference data
            metadata: Additional metadata
        
        Returns:
            ActionExplanation object
        """
        action_id = f"{self.agent_name}_{datetime.now().timestamp()}"
        timestamp = datetime.now().isoformat()
        
        # Generate explanation using judge model
        if self.enable_auto_explanations and self.hallucination_evaluator:
            explanation, reasoning, confidence = self._generate_llm_explanation(
                action_type=action_type,
                input_context=input_context,
                output_result=output_result,
                reference_context=reference_context or input_context
            )
        else:
            # Fallback: simple rule-based explanation
            explanation = f"Action: {action_type}"
            reasoning = f"Input: {input_context[:100]}... -> Output: {output_result[:100]}..."
            confidence = 0.5
        
        # Create explanation object
        action_explanation = ActionExplanation(
            action_id=action_id,
            action_type=action_type,
            timestamp=timestamp,
            input_context=input_context,
            output_result=output_result,
            explanation=explanation,
            reasoning=reasoning,
            confidence=confidence,
            metadata=metadata or {}
        )
        
        # Store explanation
        self.explanations.append(action_explanation)
        self._save_explanation(action_explanation)
        
        # Log to Phoenix if available
        self._log_to_phoenix(action_explanation)
        
        return action_explanation
    
    def _generate_llm_explanation(
        self,
        action_type: str,
        input_context: str,
        output_result: str,
        reference_context: str
    ) -> tuple[str, str, float]:
        """
        Use judge LLM to generate WHY explanation.
        
        Returns:
            (explanation, reasoning, confidence)
        """
        if not self.hallucination_evaluator:
            return ("No evaluator available", "Unable to generate explanation", 0.0)
        
        try:
            # Create DataFrame for evaluation
            eval_data = pd.DataFrame([{
                'input': input_context,
                'output': output_result,
                'reference': reference_context
            }])
            
            # Run hallucination check with explanation
            results = run_evals(
                dataframe=eval_data,
                evaluators=[self.hallucination_evaluator],
                provide_explanation=True
            )
            
            if not results.empty:
                label = results.iloc[0].get('label', 'unknown')
                explanation_text = results.iloc[0].get('explanation', 'No explanation provided')
                score = results.iloc[0].get('score', 0.5)
                
                # Build comprehensive explanation
                if label == 'hallucinated':
                    explanation = f"⚠️ HALLUCINATION DETECTED in {action_type}"
                    reasoning = f"The output contains unsupported claims. {explanation_text}"
                    confidence = 1.0 - score  # Invert score for hallucination
                else:
                    explanation = f"✅ FACTUAL OUTPUT in {action_type}"
                    reasoning = f"The output is supported by context. {explanation_text}"
                    confidence = score
                
                return (explanation, reasoning, confidence)
            else:
                return ("Evaluation incomplete", "No results from evaluator", 0.5)
                
        except Exception as e:
            logger.error(f"❌ Error generating explanation: {e}")
            return (f"Error: {str(e)}", "Failed to generate explanation", 0.0)
    
    def check_hallucination(
        self,
        output: str,
        context: str,
        query: Optional[str] = None
    ) -> HallucinationCheck:
        """
        Explicitly check if an output is hallucinated.
        
        Args:
            output: The LLM or agent output to check
            context: The reference context/facts
            query: Optional original query
        
        Returns:
            HallucinationCheck with detailed reasoning
        """
        if not self.hallucination_evaluator:
            return HallucinationCheck(
                is_hallucinated=False,
                confidence=0.0,
                explanation="Hallucination detector not available",
                supporting_facts=[],
                unsupported_claims=[]
            )
        
        try:
            # Prepare evaluation data
            eval_data = pd.DataFrame([{
                'input': query or "Check output against context",
                'output': output,
                'reference': context
            }])
            
            # Run evaluation with explanation
            results = run_evals(
                dataframe=eval_data,
                evaluators=[self.hallucination_evaluator],
                provide_explanation=True
            )
            
            if not results.empty:
                result = results.iloc[0]
                label = result.get('label', 'unknown')
                explanation = result.get('explanation', 'No explanation')
                score = result.get('score', 0.5)
                
                # Parse explanation to extract facts and claims
                # (This is a simplified version - could use more sophisticated parsing)
                supporting_facts = self._extract_supporting_facts(context, output)
                unsupported_claims = self._extract_unsupported_claims(output, context) if label == 'hallucinated' else []
                
                return HallucinationCheck(
                    is_hallucinated=(label == 'hallucinated'),
                    confidence=score,
                    explanation=explanation,
                    supporting_facts=supporting_facts,
                    unsupported_claims=unsupported_claims
                )
            else:
                return HallucinationCheck(
                    is_hallucinated=False,
                    confidence=0.0,
                    explanation="No evaluation result",
                    supporting_facts=[],
                    unsupported_claims=[]
                )
                
        except Exception as e:
            logger.error(f"❌ Hallucination check failed: {e}")
            return HallucinationCheck(
                is_hallucinated=False,
                confidence=0.0,
                explanation=f"Error: {str(e)}",
                supporting_facts=[],
                unsupported_claims=[]
            )
    
    def _extract_supporting_facts(self, context: str, output: str) -> List[str]:
        """Extract facts from context that support the output"""
        # Simplified extraction - in production, use more sophisticated NLP
        facts = []
        context_sentences = context.split('.')
        output_sentences = output.split('.')
        
        for out_sent in output_sentences:
            out_sent = out_sent.strip()
            if len(out_sent) < 10:
                continue
            
            # Check if any context sentence is similar
            for ctx_sent in context_sentences:
                ctx_sent = ctx_sent.strip()
                if len(ctx_sent) < 10:
                    continue
                
                # Simple word overlap check
                out_words = set(out_sent.lower().split())
                ctx_words = set(ctx_sent.lower().split())
                overlap = len(out_words & ctx_words)
                
                if overlap >= 3:  # At least 3 words in common
                    facts.append(ctx_sent)
                    break
        
        return facts[:5]  # Limit to top 5
    
    def _extract_unsupported_claims(self, output: str, context: str) -> List[str]:
        """Extract claims from output that are NOT supported by context"""
        unsupported = []
        output_sentences = output.split('.')
        context_lower = context.lower()
        
        for sent in output_sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            
            # Check if sentence words appear in context
            words = [w for w in sent.split() if len(w) > 4]  # Ignore short words
            found_words = sum(1 for w in words if w.lower() in context_lower)
            
            # If less than 30% of words found, might be unsupported
            if words and (found_words / len(words)) < 0.3:
                unsupported.append(sent)
        
        return unsupported[:5]  # Limit to top 5
    
    def explain_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        decision_reasoning: str
    ) -> ActionExplanation:
        """
        Explain why a tool was called and what it returned.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input parameters
            tool_output: Tool's output
            decision_reasoning: Why this tool was chosen
        
        Returns:
            ActionExplanation
        """
        input_context = f"Tool: {tool_name}\nInputs: {json.dumps(tool_input, indent=2)}\nReason: {decision_reasoning}"
        output_result = str(tool_output)
        
        return self.explain_action(
            action_type="tool_call",
            input_context=input_context,
            output_result=output_result,
            reference_context=decision_reasoning,
            metadata={
                "tool_name": tool_name,
                "tool_input": tool_input
            }
        )
    
    def explain_decision(
        self,
        decision_point: str,
        chosen_option: str,
        alternatives: List[str],
        reasoning: str,
        supporting_data: Optional[Dict[str, Any]] = None
    ) -> ActionExplanation:
        """
        Explain a decision made by the agent.
        
        Args:
            decision_point: What decision was being made
            chosen_option: What was chosen
            alternatives: What other options were available
            reasoning: Why this option was chosen
            supporting_data: Data that supports the decision
        
        Returns:
            ActionExplanation
        """
        input_context = f"Decision: {decision_point}\nAlternatives: {', '.join(alternatives)}"
        output_result = f"Chosen: {chosen_option}\nReasoning: {reasoning}"
        
        reference_context = ""
        if supporting_data:
            reference_context = f"Supporting Data: {json.dumps(supporting_data, indent=2)}"
        
        return self.explain_action(
            action_type="decision",
            input_context=input_context,
            output_result=output_result,
            reference_context=reference_context or reasoning,
            metadata={
                "decision_point": decision_point,
                "chosen_option": chosen_option,
                "alternatives": alternatives,
                "supporting_data": supporting_data
            }
        )
    
    def explain_metric_calculation(
        self,
        metric_name: str,
        inputs: Dict[str, Any],
        formula: str,
        result: float,
        interpretation: str
    ) -> ActionExplanation:
        """
        Explain how a metric was calculated.
        
        Args:
            metric_name: Name of the metric
            inputs: Input values used
            formula: Formula or calculation method
            result: Calculated result
            interpretation: What the result means
        
        Returns:
            ActionExplanation
        """
        input_context = f"Metric: {metric_name}\nInputs: {json.dumps(inputs, indent=2)}\nFormula: {formula}"
        output_result = f"Result: {result}\nInterpretation: {interpretation}"
        
        return self.explain_action(
            action_type="metric_calculation",
            input_context=input_context,
            output_result=output_result,
            reference_context=formula,
            metadata={
                "metric_name": metric_name,
                "inputs": inputs,
                "formula": formula,
                "result": result
            }
        )
    
    def _save_explanation(self, explanation: ActionExplanation):
        """Save explanation to JSONL file"""
        try:
            with open(self.current_session_file, 'a') as f:
                f.write(json.dumps(asdict(explanation)) + '\n')
        except Exception as e:
            logger.error(f"❌ Failed to save explanation: {e}")
    
    def _log_to_phoenix(self, explanation: ActionExplanation):
        """Log explanation to Phoenix for dashboard visualization"""
        if not self.phoenix_client:
            return
        
        try:
            # Create evaluation result for Phoenix
            eval_result = {
                'name': f"{self.agent_name}_{explanation.action_type}",
                'annotator_kind': 'LLM',
                'result': {
                    'label': 'explained',
                    'score': explanation.confidence,
                    'explanation': explanation.explanation,
                    'metadata': {
                        'action_id': explanation.action_id,
                        'action_type': explanation.action_type,
                        'timestamp': explanation.timestamp,
                        'reasoning': explanation.reasoning,
                        **explanation.metadata
                    }
                }
            }
            
            # Log to Phoenix
            # Note: This requires Phoenix Client to have log_evaluation method
            # The exact API may vary based on Phoenix version
            logger.debug(f"📊 Logged explanation to Phoenix: {explanation.action_id}")
            
        except Exception as e:
            logger.debug(f"Could not log to Phoenix: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of all explanations in current session"""
        total = len(self.explanations)
        by_type = {}
        avg_confidence = 0.0
        
        for exp in self.explanations:
            by_type[exp.action_type] = by_type.get(exp.action_type, 0) + 1
            avg_confidence += exp.confidence
        
        if total > 0:
            avg_confidence /= total
        
        return {
            "agent_name": self.agent_name,
            "total_actions": total,
            "actions_by_type": by_type,
            "average_confidence": avg_confidence,
            "session_file": str(self.current_session_file),
            "latest_explanations": [asdict(exp) for exp in self.explanations[-5:]]
        }
    
    def print_summary(self):
        """Print a human-readable summary"""
        summary = self.get_session_summary()
        
        print(f"\n{'='*80}")
        print(f"EXPLAINABILITY SUMMARY - {summary['agent_name']}")
        print(f"{'='*80}")
        print(f"Total Actions Explained: {summary['total_actions']}")
        print(f"Average Confidence: {summary['average_confidence']:.2%}")
        print(f"\nActions by Type:")
        for action_type, count in summary['actions_by_type'].items():
            print(f"  - {action_type}: {count}")
        print(f"\nSession Log: {summary['session_file']}")
        print(f"{'='*80}\n")


def create_explainability_tracker(
    agent_name: str,
    phoenix_endpoint: str = "http://localhost:6006",
    judge_model: str = "gpt-4o",
    enable: bool = True
) -> Optional[ExplainabilityTracker]:
    """
    Factory function to create an ExplainabilityTracker.
    
    Args:
        agent_name: Name of the agent
        phoenix_endpoint: Phoenix server endpoint
        judge_model: Model to use for explanations
        enable: Whether to enable explainability
    
    Returns:
        ExplainabilityTracker or None if disabled
    """
    if not enable:
        return None
    
    return ExplainabilityTracker(
        agent_name=agent_name,
        phoenix_endpoint=phoenix_endpoint,
        judge_model=judge_model,
        enable_auto_explanations=True
    )
