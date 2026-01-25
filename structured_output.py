from pydantic import BaseModel, Field
from typing import Literal

class Rephrased(BaseModel):
    rephrased : str

REPHRASE_SYSTEM_PROMPT="""Rephrase the input into a first-order logic style sentence in natural language only if the sentence needs quantification.
If you decide to use quantifier, replace all related entities with a variable (x,y,z).
If ALL entities already use a proper name (person's name, entities started with capital letter), DO NOT ADD QUANTIFIER and keep the sentence unchanged.
Do not over-complicate or add unnecessary words.

Example 1:
Input: Someone who loves books is kind
Answer: { "rephrased" : "For every person x, if x loves books then x is kind"}

Example 2:
Input: Alice sings
Answer:{ "rephrased" : "Alice sings"}

Example 3:
Input: If there is someone who love Ani, Ani is happy
Answer: {"rephrased" : "If there exists x who love Ani, Ani is happy"}

Example 4:
Input: If someone is happy, he will eat more food
Answer: {"rephrased" : "For every person x, if x is happy, x will eat more food"}

Example 5:
Input: John is kind
Answer: {"rephrased" : "John is kind"}

Example 6:
Input: Alice gives John a book
Answer: {"rephrased" : "Alice gives John a book"}

Example 7:
Input: Budi is not happy
Answer: {"rephrased" : "Budi is not happy"}

"""

class ChooseParser(BaseModel):
    answer: Literal["A", "B", "C", "D"]

CHOOSE_PARSER_SYSTEM_PROMPT = """You are an expert on classifying the sentence by its overall structure:
A = An atomic logical statement. (no quantifiers, no logical connectives, no negation)
B = A quantified logical statement when the sentence talks about a general rule that covers many entities.
If the sentence only mentions specific proper names, or an instances of variable (x,y,z), or if quantifiers appear only inside part of the sentence, then it should be classified as A, C, or D instead.
C = A compound logical sentence, where each part is connected with logical connectives such as 'and', 'or', 'if...then', or 'only if'.
D = A statement that contains literal negation of another sentence ('not', 'no', 'dont', 'doesnt'). Only look for a literal negation.


Example 1:
Sentence: 'Alice sings.'
Answer: { "answer" : "A"}

Example 2:
Sentence: 'Every student studies and sleeps.'
Answer: { "answer" : "B"}

Example 3:
Sentence: 'Alice sings and Bob dances.'
Answer: { "answer" : "C"}

Example 4:
Sentence: 'x does not sing.'
Answer: { "answer" : "D"}

Example 5:
Sentence: 'John will be happy.'
Answer: { "answer" : "A"}

Example 6:
Sentence: 'Doe loves to read a book.'
Answer: { "answer" : "A"}

"""

class QuantifiedParser(BaseModel):
    quantifier: Literal['ForAll', 'ThereExists']
    variable: str
    sentence_without_quantifier: str = Field(description="Rewrite the sentence without the quantifier. If there is multiple quantifier, just remove the outermost.")

QUANTIFIED_SYSTEM_PROMPT = """You identified the sentence as a quantified logical statement.

Task:
1. Select the correct quantifier:
   - ForAll (e.g., all, every, each, no one) -> the logical statement applies to ALL entities
   - ThereExists (e.g., some, there is, at least one, a) -> the logical statement appliest to SOME entities

2. Identify the variable (and all reference) being quantified (the noun phrase that follows the quantifier, e.g., "student", "person", "dog") and replace it with a letter like x, y, or z.
3. Rewrite the sentence WIHOUT the quantifier, keeping the variable in place so the sentence is still natural and understandable. Preserve the exact wording and capitalization of all subject and object names. If there is multiple quantifier, just remove the outermost.
4. If the sentence is ambiguous, you should rephrase it so that the next parser will understand whether it is an atomic logical sentence, or logical sentence with connectives, or a quantified logical sentence.

Examples:

Input: "All students study hard."
Output: {"quantifier":"ForAll","variable":"x","sentence_without_quantifier":"x study hard."}

Input: "There exists person who loves books."  
Output: {"quantifier":"ThereExists","variable":"y","sentence_without_quantifier":"y loves books."}

Input: "No one likes being ignored."
Output: {"quantifier":"ForAll","variable":"z","sentence_without_quantifier":"z does not like being ignored."}

Input: "a person loves music."  
Output: {"quantifier":"ThereExists","variable":"x","sentence_without_quantifier":"x loves music."}

Input: "If someone study hard, he will get good score"
Output: {"quantifier":"ForAll","variable":"x","sentence_without_quantifier":"If x study hard, x will get good score"}

"""

class BinaryLogicalParser(BaseModel):
    operator : Literal["And", "Or", "If", "OnlyIf", "IfAndOnlyIf"]
    left_operand : str
    right_operand : str

BINARY_LOGICAL_SYSTEM_PROMPT = """You parse a sentence into its OUTERMOST (top-level) logical operator and its two operands.

Always choose the operator that governs the entire sentence (outermost scope). 
Do not parse nested or inner operators here.
Each operand, left and right, are a standalone and complete sentence, not just a phrase, meaning it has at least subject and verb/to be.
If the operand(s) are ambiguous, you should rephrase it so that the next parser will understand whether it is an atomic logical sentence, or logical sentence with connectives, or a quantified logical sentence.
You should also resolve any co-reference in left and right operand, so that the next parser is not confused.

Output JSON matching:
operator : one of ["Not","And","Or","If","OnlyIf","IfAndOnlyIf"]
left_operand : rewrite the left part as a clean, standalone clause. Preserve the exact wording and capitalization of all subject and object names. But, resolve co-reference such as she, he, it, etc.
right_operand: rewrite the left part as a clean, standalone clause. Preserve the exact wording and capitalization of all subject and object names. But, resolve co-reference such as she, he, it, etc.

Decide by the main structure of the whole sentence:
- And: two clauses joined by and.
- Or: two clauses joined by or / either ... or.
- If: conditional “if … then …” (antecedent = left, consequent = right).
- OnlyIf: “P only if Q” (left = P, right = Q; Q is required for P).
- IfAndOnlyIf: “iff / if and only if / exactly when / just in case”.

Examples:

Input: "Alice sings and dances."
Output: {"operator": "And", "left_operand": "Alice sings", "right_operand": "Alice dances"}

Input: "Either John runs or Mary walks."
Output: {"operator": "Or", "left_operand": "John runs", "right_operand": "Mary walks"}

Input: "If it rains, the ground gets wet."
Output: {"operator": "If", "left_operand": "it rains", "right_operand": "the ground gets wet"}

Input: "A number is even only if it is divisible by two."
Output: {"operator": "OnlyIf", "left_operand": "A number is even", "right_operand": "it is divisible by two"}

Input: "You may enter if and only if you have a ticket."
Output: {"operator": "IfAndOnlyIf", "left_operand": "You may enter", "right_operand": "You have a ticket"}

Input: "If all persons are kind, peace and happiness happen."
Output: {"operator": "If", "left_operand": "all persons are kind", "right_operand": "peace and happiness happen"}

Input: "If John sings and Mary dances, then Alice claps."
Output: {"operator": "If", "left_operand": "John sings and Mary dances", "right_operand": "Alice claps"}
"""

class UnaryLogicalParser(BaseModel):
    operator : Literal["Not"]
    operand : str = Field(description="Rewrite the original sentence without the negation. If there is multiple negation, just remove the outermost. Preserve the exact wording and capitalization of all subject and object names.")

UNARY_LOGICAL_SYSTEM_PROMPT = """You parse a sentence whose top-level operator is unary negation.

Output JSON matching:
operator : always "Not"
operand  : rewrite the sentence without the outermost negation

Guidelines:
- Always set operator = "Not".
- For the operand, remove only the **outermost** negation. 
- If there are multiple negations, strip just the outermost one and keep the inner ones.
- Rewrite the operand as a natural, grammatical sentence.
- Do not add explanations or extra words.
- Return JSON only.

Examples:

Input: "It is not raining."
Output: {"operator": "Not", "operand": "It is raining"}

Input: "No student is absent."
Output: {"operator": "Not", "operand": "a student is absent"}

Input: "It is not true that John is not guilty."
Output: {"operator": "Not", "operand": "John is not guilty"}

Input: "Nobody loves me."
Output: {"operator": "Not", "operand": "Somebody loves me"}

"""

class ChooseRelation(BaseModel):
    answer : Literal["A","B","C","D"]

CHOOSE_RELATION_SYSTEM_PROMPT = """You classify an ATOMIC natural-language predicate into one of:
A = Adjective/property
B = Intransitive verb (takes no object)
C = Transitive verb (takes exactly one object)
D = Ditransitive verb (takes two objects)

Examples:

Input: "Alice is tall."
Output: {"answer":"A"}

Input: "Alice is a student."
Output: {"answer":"A"}

Input: "Alice runs."
Output: {"answer":"B"}

Input: "The baby sleeps."
Output: {"answer":"B"}

Input: "Alice loves Bob."
Output: {"answer":"C"}

Input: "The dog looked at the cat."
Output: {"answer":"C"}

Input: "John gave Mary a book."
Output: {"answer":"D"}

Input: "John sent a message to Mary."
Output: {"answer":"D"}

Input: "Mary was given a book (by John)."
Output: {"answer":"D"}

Input: "Bob was loved by Alice."
Output: {"answer":"C"}

Input: "David hates to wake up early"
Output: {"answer":"C" }

"""

class AdjectiveParser(BaseModel):
    adjective : str
    obj : str

ADJECTIVE_SYSTEM_PROMPT = """You extract the object and its adjective property from a simple atomic sentence.

Output JSON matching:
adjective : the describing word or phrase. use the base form with no modifier
obj   : the entity being described (keep wording and capitalization verbatim). use the base form with no modifier

Rules:
- Handle only atomic adjective/property sentences (e.g., "Alice is tall", "The dog is happy").
- Subjects must be individual names or noun phrases without quantifiers ("all", "every", "some", "no").
- Adjective may be single word or short phrase (e.g., "absent", "very tall").
- Do not paraphrase or change casing; copy terms exactly.
- Ignore tense/negation; just extract subject and adjective.

Examples:

Input: "Alice is tall."
Output: {"adjective": "tall", "obj": "Alice"}

Input: "student is awesome."
Output: {"adjective": "awesome", "obj": "student"}

Input: "Bob is very tired."
Output: {"adjective": "very tired", "obj": "Bob"}

"""

class IntransitiveParser(BaseModel):
    verb : str
    subject : str

INTRANSITIVE_SYSTEM_PROMPT = """You extract the subject and the main intransitive verb from a simple atomic sentence.

Output JSON matching:
verb    : the main intransitive verb (copy exactly as in the input). use the verb base form
subject : the entity performing the action (keep wording and capitalization verbatim)

Rules:
- Handle only atomic intransitive sentences (a subject + intransitive verb, with no object, no quantifier, no negation).
- Subject is a proper name or noun phrase (e.g., "Alice", "The student").
- Verb must appear exactly as written in the sentence (respect tense/aspect: "runs", "is running", "slept").
- Do not paraphrase or alter capitalization.
- Sentences with objects, quantifiers, or negation are out of scope.

Examples:

Input: "Alice runs."
Output: {"verb": "run", "subject": "Alice"}

Input: "The student sleeps."
Output: {"verb": "sleep", "subject": "The student"}

Input: "Bob is running."
Output: {"verb": "run", "subject": "Bob"}

Input: "Alice swam."
Output: {"verb": "swim", "subject": "Alice"}

"""

class TransitiveParser(BaseModel):
    subject : str
    verb : str
    obj : str

TRANSITIVE_SYSTEM_PROMPT = """You extract the subject, the main transitive verb, and its single object from a simple atomic sentence.

Output JSON matching:
subject : the entity performing the action (copy wording and capitalization verbatim)
verb    : the main transitive verb. use the verb base form
obj     : the object of the verb (copy wording and capitalization verbatim). use the base form in infinitive form

Rules:
- Handle only atomic transitive sentences (subject + verb + one object).
- No quantifiers (all, every, some, no).
- No negation.
- Subject and object must be copied exactly as they appear (keep capitalization).
- Verb must be copied exactly (respect tense/aspect: "loves", "is reading", "wrote").
- Ignore determiners only if they are not part of the noun phrase; otherwise keep them (e.g., "the book", "a student").
- Sentences with two objects (ditransitives) are out of scope.

Examples:

Input: "Alice loves Bob."
Output: {"subject": "Alice", "verb": "love", "obj": "Bob"}

Input: "The student reads a book."
Output: {"subject": "The student", "verb": "read", "obj": "a book"}

Input: "Bob is watching TV."
Output: {"subject": "Bob", "verb": "watch", "obj": "TV"}

Input: "Mary wrote a letter."
Output: {"subject": "Mary", "verb": "write", "obj": "a letter"}

Input: "John loves swimming."
Output: {"subject": "John", "verb": "love", "obj": "to swim"}

Input: "Doe likes to read a book"
Output: {"subject": "Doe", "verb": "like", "obj": "to read a book"}

"""

class DitransitiveParser(BaseModel):
    subject : str
    verb : str
    indirect_obj : str
    direct_obj : str

DITRANSITIVE_SYSTEM_PROMPT = """You extract the subject, the main ditransitive verb, its indirect object, and its direct object from a simple atomic sentence.

Output JSON matching:
subject      : the entity performing the action (copy wording and capitalization verbatim)
verb         : the main ditransitive verb. use the base verb form
indirect_obj : the recipient/beneficiary of the action (copy wording and capitalization verbatim). use the infinivive form if needed
direct_obj   : the thing being given/sent/shown/etc. (copy wording and capitalization verbatim). use the infinivive form if needed

Examples:

Input: "John gave Mary a book."
Output: {"subject": "John", "verb": "give", "indirect_obj": "Mary", "direct_obj": "a book"}

Input: "Alice sent Bob a letter."
Output: {"subject": "Alice", "verb": "send", "indirect_obj": "Bob", "direct_obj": "a letter"}

Input: "The teacher showed the students a picture."
Output: {"subject": "The teacher", "verb": "show", "indirect_obj": "the students", "direct_obj": "a picture"}

Input: "John gave a book to Mary."
Output: {"subject": "John", "verb": "give", "indirect_obj": "Mary", "direct_obj": "a book"}

Input: "Mary wrote a letter for her friend."
Output: {"subject": "Mary", "verb": "write", "indirect_obj": "her friend", "direct_obj": "a letter"}

Input: "Mary teaches John to swim"
Output: {"subject": "Mary", "verb": "teach", "indirect_obj": "John", "direct_obj": "to swim"}

"""