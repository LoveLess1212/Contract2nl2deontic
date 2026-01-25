from ast_rl import *
from dotenv import load_dotenv
from ollama import generate
from openai import OpenAI
from structured_output import *

load_dotenv()

class OpenAIWrapper:
    def __init__(self, model):
        self.model = model
        self.client = OpenAI()
    
    def generate(self, text, fmt):
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "user", "content": text}
            ],
            text_format=fmt
        )
        return response.output_parsed

    
class OllamaWrapper:
    def __init__(self, model):
        self.model = model

    def generate(self, text, fmt):
        result = generate(
            model= self.model,
            prompt= text,
            stream=False,
            format=fmt.model_json_schema(),
            options={'temperature': 0}
        )
        return fmt.model_validate_json(result.response)

class VLLMWrapper:
    def __init__(self, model, url="http://0.0.0.0:8000/v1"):
        self.model = model
        self.url = url
    
    def generate(self, text, fmt):
        client = OpenAI(base_url=self.url)
        response = client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "user", "content": text}
            ],
            response_format=fmt,
            temperature=0,
            timeout=60
        )
        client.close()
        return response.choices[0].message.parsed

class Pipeline:
    def __init__(self, llm, model, logging=False, url="http://0.0.0.0:8000/v1"):
        if llm == 'openai':
            self.llm = OpenAIWrapper(model)
        elif llm == 'ollama':
            self.llm = OllamaWrapper(model)
        elif llm == 'vllm':
            self.llm = VLLMWrapper(model,url)
        else: 
            raise ValueError("LLM is not valid")
        self.logging=logging

    def log(self, text):
        if self.logging:
            print(text)
        
    def _rephrase(self, text):
        r = self.llm.generate(
                REPHRASE_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nRephrased: ', 
                Rephrased
            )
        self.log(f"Rephrased '{text}' to '{r.rephrased}'")
        return r.rephrased
    
    def rephrase_and_parse(self, text):
        text = self._rephrase(text)
        return self.parse(text, True, "")
        
    def _parse_relation(self, text, prefix):
        choose_relation = self.llm.generate(
                    CHOOSE_RELATION_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
                    ChooseRelation)
        answer = choose_relation.answer
        if answer == 'A':
            # Adjective
            p = self.llm.generate(
                ADJECTIVE_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
                AdjectiveParser
            )
            self.log(prefix + f"Adjective parser. Adjective: {p.adjective}, Object: {p.obj}")
            return RelationAdjective(obj=Constant(name=p.obj), adjective=p.adjective)
        elif answer == 'B':
            # Intransitive
            p = self.llm.generate(
                INTRANSITIVE_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
                IntransitiveParser
            )
            self.log(prefix + f"Intransitive parser. Verb: {p.verb}, Subject: {p.subject}")
            return RelationIntransitiveVerb(verb=p.verb, subject=Constant(name=p.subject))
        elif answer == 'C':
            # Transitive
            p = self.llm.generate(
                TRANSITIVE_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
                TransitiveParser
            )
            self.log(prefix + f"Transitive parser. Verb: {p.verb}, Subject: {p.subject}, Object: {p.obj}")
            return RelationTransitiveVerb(verb=p.verb, subject=Constant(name=p.subject), obj=Constant(name=p.obj))
        elif answer == 'D':
            # Ditransitive
            p = self.llm.generate(
                DITRANSITIVE_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
                DitransitiveParser
            )
            self.log(prefix + f"Ditransitive parser. Verb: {p.verb}, Subject: {p.subject}, Indirect Object: {p.indirect_obj}, Direct Object: {p.direct_obj}")
            return RelationDitransitiveVerb(verb=p.verb, subject=Constant(name=p.subject), indirect_obj=Constant(name=p.indirect_obj), direct_obj=Constant(name=p.direct_obj))
        else:
            raise ValueError("Invalid relation option")
        
    def _parse_quantified(self, text, prefix):
        p = self.llm.generate(
                QUANTIFIED_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
                QuantifiedParser
            )
        self.log(prefix + f"Quantified parser. Quantifier: {p.quantifier}, Variable: {p.variable}")
        if p.sentence_without_quantifier.lower() == text.lower() or p.sentence_without_quantifier == "":
            return self._parse_relation(text, prefix)
        else:
            s = self.parse(p.sentence_without_quantifier, True, prefix)
            return QuantifiedSentence(quantifier=p.quantifier, variable=Variable(name=p.variable if p.variable != "" else "x"), sentence=s)

    def _parse_binary(self, text, prefix):
        p = self.llm.generate(
                BINARY_LOGICAL_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
                BinaryLogicalParser
            )
        self.log(prefix + f"Binary operator parser. Operator: {p.operator}")
        if p.left_operand.lower() == text.lower() or p.right_operand.lower() == text.lower() or p.left_operand == "" or p.right_operand == "":
            return self._parse_relation(text, prefix)
        else:
            left = self.parse(p.left_operand, False, prefix)
            right = self.parse(p.right_operand, True, prefix)
            return BinaryOperator(operator=p.operator, left=left, right=right)
    
    def _parse_unary(self, text, prefix):
        p = self.llm.generate(
            UNARY_LOGICAL_SYSTEM_PROMPT + 'Now, it is your turn\n\nInput: "' + text + '"\nOutput: ', 
            UnaryLogicalParser
        )
        self.log(prefix + f"Unary operator parser. Operator: {p.operator}")
        for w in ["not", "do not", "dont", "don't", "does not", "doesn't"]:
            if w not in text.lower() and w in p.operand.lower():
                return self._parse_relation(text, prefix)
        if p.operand.lower() == text.lower() or p.operand.lower() == "":
            return self._parse_relation(text, prefix)
        else:
            s = self.parse(p.operand, True, prefix)
            return UnaryOperator(operator=p.operator, sentence=s)

    def parse(self, text, last, prefix):
        if last:
            p = "     "
        else:
            p = "│    "

        if last:
            q = "└────"
        else:
            q = "├────"
        self.log( prefix + q + f"Parsing '{text}'")
        choose_parser =  self.llm.generate(
                    CHOOSE_PARSER_SYSTEM_PROMPT + "Now, classify this\n\nSentence: '" + text + "'\nAnswer: ", 
                    ChooseParser)
        ans = choose_parser.answer
        prefix += p
        self.log( prefix + f"Answer: {ans}")
        if ans == 'A':
            # Relation
            return self._parse_relation(text, prefix)
        elif ans == 'B':
            # Quantified
            return self._parse_quantified(text, prefix)
        elif ans == 'C':
            # Binary operator:
            return self._parse_binary(text, prefix)
        elif ans == 'D':
            # Unary operator
            return self._parse_unary(text, prefix)
        else:
            raise ValueError("Invalid parser option")
        