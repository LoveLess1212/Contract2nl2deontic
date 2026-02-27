from typing import TypedDict, Literal


class Party(TypedDict):
    """Represents a party involved in the contract"""
    name: str


class Action(TypedDict):
    """Represents an action with its trigger conditions and constraints"""
    description: str  # A concise, high-level summary of the obligation or fallback action. Rephrase for clarity while maintaining intent.
    triggerCond: str  # The specific failure or condition of the PREVIOUS step that triggers this action. Must be self-contained, using specific nouns/parties instead of pronouns.
    note: str  # The verbatim or detailed technical constraints of the rule. Include specific values, timeframes, or 'OR' conditions from the raw text.


class PenaltyRule(TypedDict):
    """Represents a penalty rule in the contract"""
    representor: str  # The party executing this action
    deonticType: Literal["Failing Which", "LCTC"]  # MUST be 'Failing Which' or 'LCTC'
    action: Action


class Contract(TypedDict):
    """Main contract structure"""
    contractName: str
    involvedParties: list[Party]
    penaltyRules: list[PenaltyRule]