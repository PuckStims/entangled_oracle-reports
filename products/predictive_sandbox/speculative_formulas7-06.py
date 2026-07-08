"""
predictive_formulas_v0_1.py
Core mathematical and logical implementations for Entangled Oracle Predictive v0.1.
Contains: Semantic Bias, Target Continuity, Structural Shear, and Epistemic Confidence.
"""
from typing import Dict, List, Set, Optional

# --- 1. SEMANTIC VECTOR MATH & ASPECT BIAS ---

def apply_signed_bias(base: float, bias: float, influence: float = 0.35) -> float:
    """
    Applies an asymptotic bias to a base score, preventing it from breaching [0.0, 1.0].
    """
    if bias >= 0:
        return base + influence * bias * (1.0 - base)
    return base + influence * bias * base

def compute_operation_mass(
    signal_magnitude: float, 
    base_profile: Dict[str, float], 
    aspect_bias: Dict[str, float]
) -> Dict[str, float]:
    """
    Computes the final semantic operation vector for a transit.
    """
    operation_mass = {}
    for op in base_profile.keys():
        biased_score = apply_signed_bias(base_profile.get(op, 0.0), aspect_bias.get(op, 0.0))
        operation_mass[op] = signal_magnitude * biased_score
    return operation_mass

# --- 2. TARGET CONTINUITY & RELAY GATE ---

def exact_address_continuity(target_a: str, target_b: str, axis_aliases: Dict[str, List[str]]) -> float:
    if target_a == target_b: return 1.0
    if target_b in axis_aliases.get(target_a, []): return 0.90
    return 0.0

def target_continuity(
    exact_continuity: float, 
    shared_component_weight: float, 
    dynamic_graph_strength: float, 
    typed_pair_prior: float
) -> float:
    """
    Strict max() gate preventing weak priors from stacking into a false narrative bridge.
    """
    return max(exact_continuity, shared_component_weight, dynamic_graph_strength, typed_pair_prior)

def relay_eligible(
    continuity_score: float, 
    semantic_similarity: float, 
    temporal_adjacency: bool, 
    same_macro_field: bool
) -> bool:
    """
    Determines if two peaks constitute a continuous narrative Relay.
    """
    return (
        temporal_adjacency and 
        same_macro_field and 
        semantic_similarity >= 0.85 and 
        continuity_score >= 0.65
    )

# --- 3. STRUCTURAL SHEAR DIAGNOSTIC ---

def structural_shear_eligible(
    semantic_similarity: float,
    temporal_adjacency: float,
    same_macro_field: bool,
    continuity_score: float,
    address_sig_a: float,
    address_sig_b: float,
    is_relay: bool
) -> bool:
    """
    Identifies high operational similarity applied to disjoint foundational nodes.
    Tier 3 Topology Diagnostic - Does NOT directly modify pathway conductance.
    """
    return (
        same_macro_field and
        temporal_adjacency >= 0.70 and
        semantic_similarity >= 0.85 and
        continuity_score < 0.35 and
        min(address_sig_a, address_sig_b) >= 0.65 and
        not is_relay
    )

# --- 4. EPISTEMIC CONFIDENCE (C_i) ---

def compute_epistemic_confidence(
    availability_gate: float, # 0.0 or 1.0
    record_integrity: float,  # [0.0, 1.0]
    calculation_integrity: float, # [0.0, 1.0]
    relation_robustness: float # [0.0, 1.0] based on interval sampling
) -> float:
    """
    Calculates C_i: The epistemic confidence that a specific geometric edge exists.
    """
    return availability_gate * record_integrity * calculation_integrity * relation_robustness

def is_edge_relay_eligible(confidence: float, relation_robustness: float) -> bool:
    """
    Hard constraint: low-confidence paths cannot fabricate a TargetContinuity Relay.
    """
    RELAY_EDGE_CONFIDENCE_MIN = 0.85
    RELAY_RELATION_ROBUSTNESS_MIN = 0.90
    
    return confidence >= RELAY_EDGE_CONFIDENCE_MIN and relation_robustness >= RELAY_RELATION_ROBUSTNESS_MIN

# --- 5. PHASE STATE FSM (Hysteresis) ---

def determine_phase_state(
    current_state: str, 
    orb: float, 
    enter_orb_threshold: float, 
    is_retrograde: bool, 
    prior_exact_hit: bool
) -> str:
    """
    Evaluates phase state utilizing a hysteresis exit orb to prevent boundary flickering.
    """
    exit_orb_threshold = enter_orb_threshold + max(0.10, enter_orb_threshold * 0.08)
    
    if orb > exit_orb_threshold:
        return "residual_field" if current_state in ["resolution", "aftermath"] else "prelude"
        
    if orb <= enter_orb_threshold and current_state == "prelude":
        return "approach"
        
    if orb <= 0.5: # Example exactness orb
        return "exactness"
        
    if is_retrograde and prior_exact_hit and orb <= exit_orb_threshold:
        return "retrograde_review"
        
    if current_state == "exactness" and orb > 0.5:
        return "aftermath"
        
    return current_state