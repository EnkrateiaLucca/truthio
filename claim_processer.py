from pydantic import BaseModel, Field
from typing import List, TypedDict
# # Skeleton

# 1. Text input
# 2. ExtractClaims (text: string)
# 3. Plan verification ()
# 4. Execute verification
# 5. Return result

class Claim(BaseModel):
    claim: str = Field(description="The claim to be verified")

class Claims(BaseModel):
    claims: List[Claim] = Field(description="The claims extracted from the text")
    
class VerificationStep(BaseModel):
    step_to_verify: str = Field(description="The step to verify the claim")

class VerificationPlan(BaseModel):
    plan: List[VerificationStep] = Field(description="The plan to verify the claims")

class VerificationResult(BaseModel):
    truthfullness_score: float = Field(description="The truthfullness score of the claim")
    sources: List[str] = Field(description="The sources of the claim")
    explanation: str = Field(description="The explanation of the claim")

class OutputVerificationPlan(TypedDict):
    claim: str
    truthfullness_score: float 
    sources: List[str]
    explanation: str

def claim_extractor(text: str) -> Claims:
    pass

def generate_verification_plan(claim: Claim) -> VerificationPlan:
    pass

def execute_verification_plan(plan: VerificationPlan) -> OutputVerificationPlan:
    pass

def process_claims(text: str) -> List[OutputVerificationPlan]:
    # Extract claims from text
    claims = claim_extractor(text)
    
    # Generate verification plan
    verification_plans = []
    for claim in claims.claims:
        verification_plan = generate_verification_plan(claim)
        verification_plans.append(verification_plan)
    
    # Execute verification plan for each claim
    results = []
    for claim, plan in zip(claims.claims, verification_plans):
        result = execute_verification_plan(VerificationPlan(plan=[plan]))
        results.append(result)
        
    return results



