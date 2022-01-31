import re

from data import Question, Category


def read_gift(file, encoding="utf8"):
    with open(file, encoding=encoding) as f:
        content = f.read()
    questions = []
    # TODO: currently relies on blocks being separated by newline characters
    blocks = re.split(r"^\n+", content, flags=re.MULTILINE)
    category = None
    for block in blocks:
        # skip empty blocks (e.g., due to empty lines at the end of the file)
        if not block:
            continue
        if Category.PATTERN in block:
            category = Category.from_str(block)
        else:
            # assume it is a text block containing a question
            q = Question.from_str(block)
            q.category = category
            questions.append(q)
    return questions


def write_gift(file, questions: list[Question], encoding="utf8"):
    if len(questions) == 0:
        raise ValueError("There must at least be one question.")
    # first sort the questions according to their categories then only print the category
    # once and all question from this category afterwards (until the next category); the
    # empty string is just for sorting a missing category (None); this will put questions
    # without category at the top of the file and without any corresponding category header
    questions = sorted(questions, key=lambda q: "" if q.category is None else q.category.name)
    category = None
    with open(file, "w", encoding=encoding) as f:
        for question in questions:
            if category != question.category:
                category = question.category
                print(category.to_gift_format(), file=f, end="\n\n")
            print(question.to_gift_format(), file=f, end="\n\n")
