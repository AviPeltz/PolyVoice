from transformers import pipeline

nlp = pipeline('question-answering')
question = "How much land does Cal Poly own?"
context = r"""
    Cal Poly has one of the largest college campuses in the United States.
    [22] It owns 9,178 acres and is the second largest land-holding university
     in California.[6] The lands are used for student education and include 
     the main campus, two nearby agricultural lands, and two properties in 
     Santa Cruz County. Part of the Cal Poly property is the Swanton Pacific
      Ranch, a 3,200-acre (1,300 ha) ranch located in Santa Cruz County, 
      California, outside the town of Davenport. The ranch provides 
      educational and research opportunities, encompasses rangeland, 
      livestock, and forestry operations for the College of Agriculture, 
      Food, and Environmental sciences, and fosters Cal Poly's Learn by Doing
       teaching philosophy of with emphasis on sustainable management of 
       agricultural practices with a mix of laboratory experiments.
       """

result = nlp(question=question, context=context)
print(f"Answer: '{result['answer']}', score: {round(result['score'], 4)}, start: {result['start']}, end: {result['end']}")


