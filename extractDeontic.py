import json
from pathlib import Path
from deontic_gen_types import *

class extractDeontic:
  def __init__(self, data: Contract, pipeline):
    self.data = data
    self.pipeline = pipeline

  def extract_deontic_from_data(self):
    deontic_output = ""
    rules = self.data['penaltyRules'] # array of rule
    for rule in rules:
      triggerCond = rule.get('action', {}).get('triggerCond')
      try:
        print(f'trying {triggerCond}')
        deonticRule = self.pipeline.rephrase_and_parse(triggerCond)
        deontic_output += str(deonticRule) + "\n"
        print(deonticRule)
      except Exception as e:
        print(e)
      
    return deontic_output

  def save_deontic_output(self, deontic_output):
    # save it to Extracted/{contractName}
    clean_name = self.data['contractName'].replace(' ', '_')
    directory = Path("Extracted") / clean_name
    outputfile = directory / f"{clean_name}.txt"
    directory.mkdir(parents=True, exist_ok=True)

    with open(outputfile, "w", encoding="utf-8") as f:
        f.write(str(deontic_output))