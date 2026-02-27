from pipeline import *
from generate_schema import generate_schema
from extractDeontic import extractDeontic

p = Pipeline(
    llm="gemini",              # or: vllm, ollama
    model="gemini-2.5-flash",
    logging=True
)


text = """
Car renters typically made car rental booking prior to their arrival to allow the car booking company to arrange with associated garages in advance. Upon arrival, the renters expect to be handed in the exact vehicle class they requested in their booking. If the requested model is unfortunately out of reach, the company shall provide an upgraded model within the same segment in a neutral color. Should no upgraded model be readily accessible, the company shall provide a car of a comparable class in a neutral color, as well as waiving all insurance costs from [trusted Insurer] and offer accessories (e.g., child safety seats) for free. If no compliant vehicle is delivered within 120 minutes, the company will provide a discount on the customer's next rental, calculated proportionally to the duration of the delay.
"""

schema = generate_schema(text, save_to_file=True)

if schema is None:
    print("Failed to generate schema. Exiting.")
    exit(1)

deonticExtractor = extractDeontic(schema, p)
deontic_output = deonticExtractor.extract_deontic_from_data()
deonticExtractor.save_deontic_output(deontic_output)
