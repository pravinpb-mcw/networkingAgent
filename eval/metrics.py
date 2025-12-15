"""
Custom DeepEval Metrics for Predictive Telemetry Agent
Evaluates decision quality, tool usage, and alert accuracy
"""

from typing import List, Optional, Dict, Any
from deepeval.metrics import ConversationalGEval
from deepeval.test_case import ConversationalTestCase, Turn

from .custom_model import get_default_model


class DecisionQualityMetric(ConversationalGEval):
    """
    Evaluates the quality of risk classification decisions made by the agent.
    
    Criteria:
    - Correct risk level classification (Stable/Temporary/Sustained/Likely Failure)
    - Appropriate risk score range for the classification
    - Proper trend analysis interpretation
    - Accurate recovery likelihood assessment
    """
    
    def __init__(
        self,
        threshold: float = 0.7,
        model=None
    ):
        super().__init__(
            name="DecisionQuality",
            criteria="""Evaluate the agent's decision quality in network failure prediction:

1. RISK CLASSIFICATION ACCURACY (40%):
   - Is the classification (Stable/Temporary Degradation/Sustained Degradation/Likely Failure) appropriate given the telemetry data?
   - Does the risk score (0-100) align with the classification tier?
   
2. TREND ANALYSIS (30%):
   - Did the agent correctly identify metric trends (improving/stable/worsening)?
   - Did it distinguish between temporary spikes and sustained degradation?
   - Did it check recovery patterns in recent time buckets?
   
3. RECOVERY LIKELIHOOD (20%):
   - Is the recovery assessment (High/Low/None) justified by the data?
   - Does it match the trend direction?
   
4. ACTIONABILITY (10%):
   - Are the recommended actions appropriate for the risk level?
   - Is the switching timeline realistic?

Score 0.0-1.0 based on overall decision quality.""",
            threshold=threshold,
            model=model or get_default_model()
        )


class ToolUsageMetric(ConversationalGEval):
    """
    Evaluates the agent's MCP tool usage effectiveness.
    
    Criteria:
    - Correct tool selection for the task
    - Appropriate arguments passed to tools
    - Efficient use of tools (not redundant calls)
    - Proper tool result interpretation
    """
    
    def __init__(
        self,
        threshold: float = 0.7,
        model=None
    ):
        super().__init__(
            name="ToolUsage",
            criteria="""Evaluate the agent's MCP tool usage for network monitoring:

1. TOOL SELECTION (35%):
   - Did the agent call the appropriate tools (get_wireless_health, get_wireless_latency_history, etc.)?
   - Did it gather topology information for failover recommendations?
   - Did it check client counts on candidate APs?
   
2. ARGUMENT CORRECTNESS (25%):
   - Were the correct network_id and ap_serial passed?
   - Were time ranges appropriate?
   
3. EFFICIENCY (20%):
   - Were there redundant tool calls?
   - Did it gather all needed data in minimal calls?
   
4. RESULT INTERPRETATION (20%):
   - Did the agent correctly parse tool outputs?
   - Were numerical values properly compared to thresholds?
   - Were trends correctly calculated from time-series data?

Score 0.0-1.0 based on overall tool usage quality.""",
            threshold=threshold,
            model=model or get_default_model()
        )


class AlertAccuracyMetric(ConversationalGEval):
    """
    Evaluates the accuracy and appropriateness of alerts sent by the agent.
    
    Criteria:
    - Correct alert severity (info/warning/critical)
    - Complete alert message content
    - Appropriate clients and services mentioned
    - Valid failover recommendations
    """
    
    def __init__(
        self,
        threshold: float = 0.7,
        model=None
    ):
        super().__init__(
            name="AlertAccuracy",
            criteria="""Evaluate the agent's alert generation for network monitoring:

1. SEVERITY CORRECTNESS (40%):
   - Does the alert status (info/warning/critical) match the risk classification?
   - Temporary Degradation (21-40) → info
   - Sustained Degradation (41-70) → warning  
   - Likely Failure (71-100) → critical
   - Stable (0-20) → no alert needed
   
2. MESSAGE COMPLETENESS (30%):
   - Does the alert include risk classification and score?
   - Are telemetry trends included with direction indicators?
   - Is the reason for alert clearly explained?
   - Are connected clients listed?
   
3. FAILOVER RECOMMENDATIONS (20%):
   - Is a recommended AP suggested when appropriate?
   - Are per-client recommendations included?
   - Is expected RSSI/signal quality mentioned?
   
4. SERVICE IMPACT (10%):
   - Are affected services (Teams/Email/SMB/VOIP) identified?
   - Is the impact level (High/Medium/Low) appropriate?

Score 0.0-1.0 based on overall alert quality.""",
            threshold=threshold,
            model=model or get_default_model()
        )


def get_all_metrics(threshold: float = 0.7) -> List[ConversationalGEval]:
    """
    Get all evaluation metrics with the specified threshold.
    
    Args:
        threshold: Minimum score threshold for passing (0.0-1.0)
    
    Returns:
        List of configured metric instances
    """
    model = get_default_model()
    return [
        DecisionQualityMetric(threshold=threshold, model=model),
        ToolUsageMetric(threshold=threshold, model=model),
        AlertAccuracyMetric(threshold=threshold, model=model)
    ]


def create_test_case_from_trace(
    trace_data: Dict[str, Any],
    chatbot_role: str = "a predictive network failure detection agent"
) -> ConversationalTestCase:
    """
    Create a DeepEval ConversationalTestCase from a Langfuse trace.
    
    Args:
        trace_data: Trace data from Langfuse (with observations)
        chatbot_role: Role description for the chatbot
    
    Returns:
        ConversationalTestCase for evaluation
    """
    turns = []
    
    # Extract input as user turn
    if trace_data.get("input"):
        input_content = trace_data["input"]
        if isinstance(input_content, dict):
            input_content = str(input_content)
        turns.append(Turn(role="user", content=input_content))
    
    # Extract output as assistant turn
    if trace_data.get("output"):
        output_content = trace_data["output"]
        if isinstance(output_content, dict):
            output_content = str(output_content)
        turns.append(Turn(role="assistant", content=output_content))
    
    # Create test case
    test_case = ConversationalTestCase(turns=turns)
    test_case.chatbot_role = chatbot_role
    
    return test_case
