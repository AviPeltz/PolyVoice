from transformers import pipeline


class QAModel:

    def __init__(self):
        self.nlp = pipeline("question-answering", model="deepset/electra-base-squad2")

    def answer_question(self, question: str, context: str):
        result = self.nlp(question=question, context=context)

        return result


def main():
    context = "Cal Poly has one of the largest college campuses in the United States. It owns 9,178 acres and is the second largest land-holding university in California. The lands are used for student education and include the main campus, two nearby agricultural lands, and two properties in Santa Cruz County. Part of the Cal Poly property is the Swanton Pacific Ranch, a 3,200-acre (1,300 ha) ranch located in Santa Cruz County, California, outside the town of Davenport. The ranch provides educational and research opportunities, encompasses rangeland, livestock, and forestry operations for the College of Agriculture, Food, and Environmental sciences, and fosters Cal Poly's Learn by Doing teaching philosophy of with emphasis on sustainable management of agricultural practices with a mix of laboratory experiments."

    model = QAModel()

    questions = [
        "How much land does Cal Poly own?",
        "What is the Swanton Pacific Ranch?",
        "What is Cal Poly's teaching philosophy?",
        "What is Swanton Pacific Ranch used for?"
    ]
    for question in questions:
        print(model.answer_question(question, context))


if __name__ == "__main__":
    main()
