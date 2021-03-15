from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch
'''
# Initializing a RoBERTa configuration
configuration = RobertaConfig()

# Initializing a model from the configuration
model = RobertaModel(configuration)

# Accessing the model configuration
configuration = model.config
'''


# Question answering using a model and tokenizer process:
#
# 1. Instantiate a tokenizer and a model from the checkpoint name.
#    The model is identified as a BERT model and loads it with the weights
#    stored in the checkpoint.

#tokenizer = AutoTokenizer.from_pretrained("roberta-base")
#model = AutoModelForQuestionAnswering.from_pretrained('roberta-base')
tokenizer = AutoTokenizer.from_pretrained("deepset/roberta-base-squad2")
model = AutoModelForQuestionAnswering.from_pretrained("deepset/roberta-base-squad2")

# Define a context and a few questions
context = "Cal Poly has one of the largest college campuses in the United States.[22] It owns 9,178 acres and is the second largest land-holding university in California.[6] The lands are used for student education and include the main campus, two nearby agricultural lands, and two properties in Santa Cruz County. Part of the Cal Poly property is the Swanton Pacific Ranch, a 3,200-acre (1,300 ha) ranch located in Santa Cruz County, California, outside the town of Davenport. The ranch provides educational and research opportunities, encompasses rangeland, livestock, and forestry operations for the College of Agriculture, Food, and Environmental sciences, and fosters Cal Poly's Learn by Doing teaching philosophy of with emphasis on sustainable management of agricultural practices with a mix of laboratory experiments."
questions = [
    "How much land does Cal Poly own?",
    "What is the Swanton Pacific Ranch?",
    "What is Cal Poly's teaching philosophy?",
]
'''
# roberta
for question in questions:
    inputs = tokenizer(question, context, return_tensors="pt")
    start_positions = torch.tensor([1])
    end_positions = torch.tensor([3])

    outputs = model(**inputs, start_positions=start_positions, end_positions=end_positions)
    loss = outputs.loss
    start_scores = outputs.start_logits
    end_scores = outputs.end_logits
'''

'''
    context_tokens = tokenizer.convert_ids_to_tokens(input_ids)
    outputs = model(**inputs)
    answer_start_scores = outputs.start_logits
    answer_end_scores = outputs.end_logits

    # Get the most likely beginning of answer with the argmax of the score
    answer_start = torch.argmax(
        answer_start_scores
    )
    # Get the most likely end of answer with the argmax of the score
    answer_end = torch.argmax(answer_end_scores) + 1

    answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(input_ids[answer_start:answer_end]))

    print(f"Question: {question}")
    print(f"Answer: {answer}")
    '''


# bert-large-uncased...
for question in questions:
    inputs = tokenizer(question, context, add_special_tokens=True, return_tensors="pt")
    input_ids = inputs["input_ids"].tolist()[0]

    context_tokens = tokenizer.convert_ids_to_tokens(input_ids)
    outputs = model(**inputs)
    answer_start_scores = outputs.start_logits
    answer_end_scores = outputs.end_logits

    # Get the most likely beginning of answer with the argmax of the score
    answer_start = torch.argmax(
        answer_start_scores
    )
    # Get the most likely end of answer with the argmax of the score
    answer_end = torch.argmax(answer_end_scores) + 1

    answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(input_ids[answer_start:answer_end]))

    print(f"Question: {question}")
    print(f"Answer: {answer}")
