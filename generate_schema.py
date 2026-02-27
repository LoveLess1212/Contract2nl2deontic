import json
import os
from pathlib import Path
from typing import TypedDict, Optional
from google import genai
from google.genai import types
from deontic_gen_types import Contract
# Nhớ bảo mật API Key khi đưa lên GitHub hoặc submit paper nhé anh
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

sys_instruction = """
You are an expert Legal Process Engineer and Academic Researcher specialized in Deontic Logic and BPMN Choreography.
Your task is to parse commercial contract text into a strictly structured JSON representation of Deontic penalty rules for automated process mapping.

### ACADEMIC CONTEXT (DEONTIC LOGIC TO BPMN):
The target system maps these extracted rules into a BPMN Choreography. You MUST classify the sequence of actions using strict Deontic operators:
- "Trigger": The primary obligation that is breached (the condition that initiates the penalty protocol).
- "Failing Which": A sequential compensation action that occurs if the primary obligation or a prior compensation action fails.
- "LCTC" (Last Chance To Compensate): The terminal penalty rule (typically financial, e.g., refund, discount) executed when all other repair/compensation actions fail.

### EXTRACTION RULES & CONSTRAINTS:
1. EXTRACT PARTIES: Identify all involved parties (e.g., Hotel, Customer).
2. EXTRACT TRIGGER: Identify the primary ideal state or obligation.
3. STRICT SEQUENCE: Map out the fallback actions strictly in order of execution. Do NOT create complex branches; flatten the logic into a sequence (Step 1 -> Step 2 -> Step 3). The item index in the array will represent the order of execution.
4. APPLY DEONTIC TYPES: Label every intermediate fallback step EXACTLY as "Failing Which". The absolute final step MUST EXACTLY be labeled "LCTC".
5. HANDLE OPTIONS/NOTES: If an action has alternatives (e.g., "luxury interior OR king-size bed"), do not split them into different rules. Keep them in the "description" and summarize constraints in the "note" field.
6. The triggerCond must be a standalone statement that is fully intelligible without reference to previous steps or external context. Replace all pronouns (e.g., "it," "they," "this") and relative descriptors (e.g., "such," "the aforementioned") with the specific nouns or parties they refer to.

### REQUIRED OUTPUT SCHEMA:
{
  "contractName": "string",
  "involvedParties": [ { "name": "string" } ],
  "penaltyRules": [
    {
      "representor": "string (the party executing this action)",
      "deonticType": "string (MUST be 'Failing Which' or 'LCTC')",
      "action": {
        "description": "string (A concise, high-level summary of the obligation or fallback action. Rephrase for clarity while maintaining intent.)",
        "triggerCond": "string (The specific failure or condition of the PREVIOUS step that triggers this action. Must be self-contained, using specific nouns/parties instead of pronouns.)",
        "note": "string (The verbatim or detailed technical constraints of the rule. Include specific values, timeframes, or 'OR' conditions.)"
      }
    }
  ]
}
"""


def generate_schema(raw_text: str, save_to_file=True) -> Optional[Contract]:
    """
    Generate structured JSON schema from contract text using Gemini AI.
    
    Args:
        raw_text (str): The contract text to parse
        save_to_file (bool): Whether to save the result to a JSON file (default: True)
    
    Returns:
        dict: Parsed contract data with penalty rules, or None if parsing fails
    """
    # Đã bật response_mime_type="application/json" để ép Gemini trả về JSON thuần
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction,
            response_mime_type="application/json",
            temperature=0.0  # Hạ xuống 0.0 để đảm bảo tính Deterministic (luôn ra kết quả nhất quán cho paper)
        )
    )

    try:
        data= json.loads(response.text or "{}")
        if data == {}:
            print("❌ Error: Received empty JSON response")
            print(response.text)
            return None
        print("✅ Extraction Success:")
        dataJson = json.dumps(data, indent=2, ensure_ascii=False)
        print(dataJson)
        
        if save_to_file:
            clean_name = data['contractName'].replace(' ', "_")
            directory = Path("Extracted") / clean_name
            directory.mkdir(parents=True, exist_ok=True)
            filename = directory / f"{clean_name}.json"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(dataJson)
            print(f"💾 Saved to: {filename}")
        
        return data

    except json.JSONDecodeError:
        print("❌ Error: Raw response is not valid JSON")
        print(response.text)
        return None
