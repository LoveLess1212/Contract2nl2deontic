# Deontic Logic Extraction from Legal Contracts

This repository extends the NL2Logic framework to extract and formalize deontic logic from legal contracts. Given a contract text, it identifies penalty rules, obligations, and trigger conditions, then translates them into formal first-order logic representations using AST-guided parsing. This enables automated contract analysis and verification of legal obligations.

## Base Framework

This work builds upon **NL2Logic**: AST-Guided Translation of Natural Language into First-Order Logic with Large Language Models. For details on the underlying framework, see the [original NL2Logic repository](https://github.com/peng-gao-lab/nl2logic).

## Usage

```python
from pipeline import Pipeline
from generate_schema import generate_schema
from extractDeontic import extractDeontic

# Initialize the NL2Logic pipeline
p = Pipeline(
    llm="gemini",
    model="gemini-2.5-flash",
    logging=True
)

# Example contract text
contract_text = """
Car renters expect to receive the exact vehicle class they booked.
If the requested model is unavailable, the company shall provide an
upgraded model within the same segment in a neutral color...
"""

# Generate contract schema and extract deontic logic
schema = generate_schema(contract_text, save_to_file=True)
deontic_extractor = extractDeontic(schema, p)
deontic_output = deontic_extractor.extract_deontic_from_data()
deontic_extractor.save_deontic_output(deontic_output)
```

## Installation

```bash
pip install -r requirements.txt
```

Set your Google Gemini API key in a `.env` file:

```
GEMINI_API_KEY=your-api-key
```
