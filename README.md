# Claim Verification System

This system processes and verifies claims from text input through a multi-step pipeline.

## Core Components

### Data Models

- `Claim`: Represents a single claim to be verified
- `Claims`: Collection of extracted claims
- `VerificationStep`: Individual step in verifying a claim
- `VerificationPlan`: Sequence of steps to verify claims
- `VerificationResult`: Results of verification including truthfulness score, sources and explanation
- `OutputVerificationPlan`: Final output format for verification results

### Processing Pipeline

1. **Claim Extraction** (`claim_extractor`)
   - Input: Raw text
   - Output: Structured Claims object containing extracted claims
   - Purpose: Parses input text to identify distinct claims

2. **Verification Planning** (`generate_verification_plan`) 
   - Input: Single Claim
   - Output: VerificationPlan with steps
   - Purpose: Creates a structured plan to verify each claim

3. **Plan Execution** (`execute_verification_plan`)
   - Input: VerificationPlan
   - Output: OutputVerificationPlan with results
   - Purpose: Executes verification steps and produces final results

4. **Overall Process** (`process_claims`)
   - Orchestrates the entire pipeline:
     1. Extracts claims from input text
     2. Generates verification plans for each claim
     3. Executes plans and collects results
   - Returns list of verification results for all claims

## Usage

The system takes text input containing claims and returns structured verification results including:
- Truthfulness scores (0-1)
- Supporting sources
- Detailed explanations

This modular design allows for flexible implementation of each component while maintaining a consistent data flow through the verification pipeline.
