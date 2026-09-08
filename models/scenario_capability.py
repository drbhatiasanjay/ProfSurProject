from dataclasses import dataclass, field
import pandas as pd
from typing import Dict, Any, List
from .analytical_contracts import AnalyticalRequest, CapabilityResult, AnalysisRunEnvelope

@dataclass
class ScenarioCapability:
    baseline: str
    interventions: Dict[str, float]
    held_constant: List[str]
    model: str
    prediction: str = ""
    uncertainty: str = ""
    comparison: str = ""
    provenance: str = "Wave 5 Scenario Engine"

class ScenarioAdapter:
    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        df = request.dataset.copy()
        
        # In a real app, interventions come from the parsed request
        # Example: scenario add tax -5%
        # Here we mock a basic intervention on the dataset
        interventions = request.options.get("interventions", {})
        
        if not interventions:
            return CapabilityResult(request_id=request.id, success=False, error="Scenario requires at least one intervention (e.g. tax -0.05).")
            
        messages = ["Scenario interventions applied:"]
        for col, shift in interventions.items():
            if col in df.columns:
                df[col] = df[col] + shift
                messages.append(f" - {col} shifted by {shift}")
                
        # Typically scenario then calls a predict on a previously fit model.
        # For simplicity, we just return the dataset snapshot ref update.
        # This will be passed back to the UI.
        
        # We wrap this in ScenarioCapability metadata
        scen_cap = ScenarioCapability(
            baseline="Current Dataset",
            interventions=interventions,
            held_constant=[c for c in df.columns if c not in interventions],
            model="None (Intervention Only)"
        )
        
        return CapabilityResult(
            request_id=request.id,
            success=True,
            display_tables={"Scenario Summary": pd.DataFrame([scen_cap.__dict__])},
            run_envelope=run_envelope,
            messages=messages,
            internal_data={"scenario_metadata": scen_cap}
        )
