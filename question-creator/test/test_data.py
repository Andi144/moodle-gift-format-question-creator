from creator.data import Category, Question, Answer
import unittest


class TestCategoryMethods(unittest.TestCase):
    
    def test_from_str(self):
        name = "some category name"
        c = Category.from_str(f"{Category.PATTERN}{name}")
        self.assertEqual(Category(name), c)
    
    def test_from_str_empty(self):
        name = ""
        c = Category.from_str(f"{Category.PATTERN}{name}")
        self.assertEqual(Category(name), c)
    
    def test_from_str_invalid(self):
        self.assertRaises(ValueError, Category.from_str, "invalid")


class TestQuestionMethods(unittest.TestCase):
    
    def test_from_str(self):
        # all of these should result in the same question object
        strings = [
            # normal
            """Question text.{
    =Correct
    ~Incorrect
    ~Incorrect
}""",
            # question text on new line and new line after '}' (+ more indents)
            """
        Question text.{
            =Correct
            ~Incorrect
            ~Incorrect
        }
        """,
            # empty line between question text and '{'
            """Question text.
            
            {
                =Correct
                ~Incorrect
                ~Incorrect
            }""",
            # empty line after answer text
            """Question text.{
                =Correct
                
                ~Incorrect
                ~Incorrect
            }""",
            # empty line before first answer
            """Question text.{
            
                =Correct
                ~Incorrect
                ~Incorrect
            }""",
            # empty line after last answer
            """Question text.{
                =Correct
                ~Incorrect
                ~Incorrect
                
            }""",
            # no indents
            """Question text.{
=Correct
~Incorrect
~Incorrect
}""",
            # whitespace after answer token '='
            """Question text.{
                = Correct
                ~Incorrect
                ~Incorrect
            }""",
            # arbitrary new lines, whitespaces and indents
            """
            
            Question text.    {
            
            
                =  Correct
        ~       Incorrect
        
        
                  ~       Incorrect
            
    }
    
    """
        ]
        for s in strings:
            self.assertEqualQuestion(
                question=Question.from_str(s),
                category=None,
                title="",
                text="Question text.",
                answers=[Answer("Correct", True), Answer("Incorrect", False), Answer("Incorrect", False)],
                mode=Question.MODE_SINGLE
            )
    
    def assertEqualQuestion(self, question: Question, category, title, text, answers, mode):
        self.assertEqual(category, question.category)
        self.assertEqual(title, question.title)
        self.assertEqual(text, question.text)
        self.assertEqual(len(answers), len(question.answers))
        for expected_a, actual_a in zip(answers, question.answers):
            self.assertEqual(expected_a.text, actual_a.text)
            self.assertEqual(expected_a.correct, actual_a.correct)
        self.assertEqual(mode, question.mode)
