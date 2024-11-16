from pydantic import BaseModel, Field, model_validator
from typing import List, TypedDict
import re
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
import os
from serpapi import GoogleSearch
from langchain.tools import tool
from langchain import hub
import tiktoken

client = OpenAI()
# # Skeleton

# 1. Text input
# 2. ExtractClaims (text: string)
# 3. Plan verification ()
# 4. Execute verification
# 5. Return result





def get_num_tokens(prompt, model="gpt-4o-mini"):
    """Calculates the number of tokens in a text prompt"""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))

class Claim(BaseModel):
    claim: str = Field()

    @model_validator(mode="after")
    def validate_sources(self) -> "Claim":
        # Assuming text_chunk is provided during initialization
        text_chunks = getattr(self, "text_chunk", None)
        if text_chunks:
            spans = list(self.get_spans(text_chunks))
            self.substring_quote = [text_chunks[span[0]:span[1]] for span in spans]
        return self

    def get_spans(self, context):
        for quote in self.substring_quote:
            yield from self._get_span(quote, context)

    def _get_span(self, quote, context):
        for match in re.finditer(re.escape(quote), context):
            yield match.span()

class VerifiableClaim(Claim):
    verifiable: bool = Field(description="A boolean indicating whether the claim is verifiable or not.")

class Claims(BaseModel):
    claims: List[Claim] = Field(default_factory=list, description="The claims extracted from the text or an empty list if there are no VERIFIABLE claims in the text.")

class VerificationStep(BaseModel):
    step_to_verify: str = Field(description="The step to verify the claim")

class VerificationPlan(BaseModel):
    plan: List[VerificationStep] = Field(description="The plan to verify the claims")

class VerificationResult(BaseModel):
    truthfullness_score: int = Field(description="The truthfullness score of the claim as a number between 1 (false) and 10 (true).")
    sources: List[str] = Field(description="The url sources used to validate or nulify the claim.")
    explanation: str = Field(description="The explanation of the score given to the claim as a concise 1 or 2 sentence phrase.")

class OutputVerificationPlan(TypedDict):
    claim: str
    truthfullness_score: float 
    sources: List[str]
    explanation: str


def get_token_usage(response) -> int:
    """Extract token usage from OpenAI response"""
    if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
        return response.usage.total_tokens
    return 0

def claim_extractor(text: str) -> tuple[Claims, int]:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful researcher, and you extract claims from the text if there are claims in the text, if not you output an empty list."},
                  {"role": "user", "content": text}],
        response_format=Claims
    )
    tokens_used = get_token_usage(response)
    return response.choices[0].message.parsed, tokens_used

def is_claim_verifiable(claim_str: str) -> bool:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful researcher, and you determine if a claim can be verified or not through a web search."},
                  {"role": "user", "content": claim_str}],
        response_format=VerifiableClaim
    )
    tokens_used = get_token_usage(response)
    return response.choices[0].message.parsed, tokens_used

@tool
def web_search(query: str) -> str:
    """
    Finds general knowledge information using Google search. Can also be used
    to augment more 'general' knowledge to a previous specialist query.
    """
    serpapi_params = {
    "engine": "google",
    "api_key": os.environ["SERPAPI_KEY"]
}
    search = GoogleSearch({**serpapi_params, "q":query, "n": 3})
    try:
        results = search.get_dict()["organic_results"]
        print("RESULTS:")
        print(results)
    except Exception as e:
        print(e)
        results = []
        return "No results found"
    
    try:    
        contexts = "\n---\n".join(
             ["\n".join([x["title"], x["snippet"], x["link"]]) for x in results]
        )
    except Exception as e:
        print(e)
        return "No results found"
    
    return contexts

def generate_verification_plan(claim: Claim) -> tuple[VerificationPlan, int]:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful research, and you generate a verification plan with 1 to 3 steps for the claim."},
                  {"role": "user", "content": claim.claim}],
        response_format=VerificationPlan
    )
    tokens_used = get_token_usage(response)
    return response.choices[0].message.parsed, tokens_used

def execute_verification_plan(claim: str, plan: VerificationPlan) -> tuple[OutputVerificationPlan, int]:
    llm = ChatOpenAI(model="gpt-4o-mini")
    tools = [web_search]
    prompt = hub.pull("hwchase17/openai-tools-agent")
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    research_output = ""
    agent_tokens_used = 0
    for step in plan.plan:
        agent_prompt = f"Verify this claim: {claim} by executing this step: {step.step_to_verify}. Perform at most 3 web searches and return a concise and clear response."
        result = agent_executor.invoke({
            "input": agent_prompt,
            "agent_scratchpad": []
        })
        research_output += result["output"]
        research_output += "\n---\n"
        agent_tokens_used += get_num_tokens(agent_prompt)
    
    agent_tokens_used += get_num_tokens(research_output)
    # Parse the final analysis into the required format
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Parse the analysis from the research made into these fields: truthfullness_score, sources, justification"},
                 {"role": "user", "content": research_output}],
        response_format=VerificationResult
    )
    
    tokens_used  = get_token_usage(response)
    
    total_tokens_used = tokens_used + agent_tokens_used
    
    result = response.choices[0].message.parsed 
    
    return OutputVerificationPlan(
        claim=claim,
        truthfullness_score=result.truthfullness_score,
        sources=result.sources,
        explanation=result.explanation
    ), total_tokens_used


def process_claims(text: str) -> tuple[List[OutputVerificationPlan], dict]:
    token_counts = {
        'claim_extraction': 0,
        'verification_planning': 0,
        'verification_execution': 0
    }
    
    # Extract claims from text    
    claims, tokens = claim_extractor(text)
    if len(claims.claims) == 0:
        return [OutputVerificationPlan(
            claim="",
            truthfullness_score=0,
            sources=[],
            explanation="No verifiable claims were found in the provided text."
        )], token_counts
    
    token_counts['claim_extraction'] = tokens
    
    results = []
    for claim in claims.claims:
        claim_verifiable, verifiable_tokens = is_claim_verifiable(claim.claim)  
        token_counts['verification_planning'] += verifiable_tokens
        if claim_verifiable.verifiable:
            plan, plan_tokens = generate_verification_plan(claim)
            token_counts['verification_planning'] += plan_tokens
            
            result, exec_tokens = execute_verification_plan(claim, plan)
            token_counts['verification_execution'] += exec_tokens
            results.append(result)
        else:
            results.append(OutputVerificationPlan(
                claim=claim,
                truthfullness_score=0,
                sources=[],
                explanation="The claim is not verifiable."
            ))
    print("Token usage breakdown:", token_counts)
    print(f"Total tokens used: {sum(token_counts.values())}")
        
    return results, token_counts

def main():
    expression_with_statement = """
    The world war 2 was started by the US.
    """
    # Remove the global declaration since we're using module-level token_tracker
    results = process_claims(expression_with_statement)
    print(results)
    


if __name__ == "__main__":
    main()