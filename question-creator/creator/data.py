import re


class Category:
    # expected format: "$CATEGORY: $course$/top/<category name>"
    PATTERN = "$CATEGORY: $course$/top/"
    
    def __init__(self, name: str):
        self.name = name
    
    @staticmethod
    def from_str(s: str) -> "Category":
        parts = s.split(Category.PATTERN)
        if len(parts) != 2:
            raise ValueError(f"Category block must contain '{Category.PATTERN}' exactly once.\n\n{s}")
        name = parts[1].split("\n", maxsplit=1)[0]
        return Category(name.strip())
    
    def to_gift_format(self):
        return f"{Category.PATTERN}{self.name}"
    
    def __str__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, Category):
            return self.name == other.name
        return NotImplemented


class Answer:
    
    def __init__(self, text: str, correct: bool):
        self.text = text
        self.correct = correct
    
    def to_gift_format(self):
        return escape_special_gift_chars(self.text)
    
    def __str__(self):
        return f"[{'x' if self.correct else ' '}] {self.text}"


class Question:
    
    MODE_SINGLE = "single"
    MODE_MULTI = "multi"
    MODES = (MODE_SINGLE, MODE_MULTI)
    
    def __init__(self, category: Category = None, title: str = "", text: str = "",
                 answers: list[Answer] = None, mode: str = ""):
        # TODO: convert to properties to integrate checks also when attributes are set afterwards
        if not answers:
            raise ValueError(f"At least one answer must be provided.\n\n{title}\n\n{text}")
        if not text:
            raise ValueError(f"Main question text must not be empty.\n\n{title}\n\n" +
                             "\n".join(str(a) for a in answers))
        if mode == Question.MODE_SINGLE and len([a for a in answers if a.correct]) != 1:
            raise ValueError(f"Exactly one answer must be set as correct if mode is '{mode}'." +
                             f"\n\n{title}\n\n{text}\n\n" + "\n".join(str(a) for a in answers))
        self.category = category
        self.title = title
        self.text = text
        self.answers = answers
        self.mode = mode
    
    @staticmethod
    def from_str(s: str) -> "Question":
        # ensure that the question contains opening and closing braces
        open_brace = re.search(r"(?<!\\){\n", s)
        close_brace = re.search(r"(?<!\\)}\n", s)
        if not open_brace or not close_brace:
            raise ValueError("Invalid GIFT question format (must include '{' and '}').\n\n" +
                             f"Question text block:\n{s}")
        
        # title handling
        match = re.search("::.+::", s)
        title = match.group() if match else ""
        if title:
            # skip the (optional) title so only the main question remains
            s = s.split(title, maxsplit=1)[1]
            # remove the double colons in ::<title>::
            title = title[2:-2]
        
        # processing of optional [html] start of a question text
        if s.startswith("[html]"):
            s = s[6:]
        
        # splitting question into text and answers based on opening and closing braces
        parts = re.split(open_brace.re.pattern, s)
        if len(parts) != 2:
            raise ValueError(r"More than one '{' without preceding escape character '\'." + "\n\n" +
                             f"Question text block:\n{s}")
        text, answers_block = parts
        text = extract_special_gift_chars(text)
        parts = re.split(close_brace.re.pattern, answers_block)
        if len(parts) != 2:
            raise ValueError(r"more than one '}' without preceding escape character '\'" + "\n\n" +
                             f"Question text block:\n{s}")
        modes_and_answers = [Question._extract_mode_and_answer(a) for a in parts[0].split("\n") if a]
        
        # infer question mode from answers; if the returned mode is None --> True, if the
        # returned mode is not None (e.g., %<percentage>%) --> False
        # TODO: very simple heuristic
        is_single = {mode is None for mode, _ in modes_and_answers}
        if len(is_single) != 1:
            raise ValueError("Answers have mixed modes but all answer modes must be the same.\n\n" +
                             f"Question text block:\n{s}")
        # the single element in "is_single" is either True (--> mode=single) or not (--> mode=multi)
        mode = Question.MODE_SINGLE if is_single.pop() else Question.MODE_MULTI
        answers = [answer for _, answer in modes_and_answers]
        
        # do not use the title if it is the same as the text
        return Question(title="" if title == text else title.strip(), text=text.strip(), answers=answers, mode=mode)
    
    @staticmethod
    def _extract_mode_and_answer(s):
        # TODO: very simple heuristic
        match = re.search(r"[=~](%.+%)?(\[moodle])?", s)
        if not match:
            raise ValueError("Invalid GIFT answer format (expected '=' or '~' at start).\n\n" +
                             f"Answer text block:\n{s}")
        mode = match.group()
        # skip the mode so only the main answer remains
        text = s.split(mode, maxsplit=1)[1]
        text = extract_special_gift_chars(text)
        # TODO: very simple heuristic
        # group(1) yields the %<percentage>% part if it is there, None otherwise
        correct = "=" in mode or (match.group(1) is not None and "-" not in mode)
        return match.group(1), Answer(text.strip(), correct)
    
    def to_gift_format(self):
        gift = f"::{self.title}::" if self.title else ""
        gift += "[html]"
        gift += escape_special_gift_chars(self.text)
        gift += "{\n"
        for a in self.answers:
            if self.mode == Question.MODE_SINGLE:
                mode = "=" if a.correct else "~"
            elif self.mode == Question.MODE_MULTI:
                percentage = self._get_percentage(a)
                percentage_str = str(round(percentage, ndigits=5)).rstrip("0")
                if percentage_str.endswith("."):
                    percentage_str = percentage_str[:-1]
                mode = f"~%{percentage_str}%"
            else:
                raise ValueError(f"Unknown question mode: '{self.mode}'\n\n{self}")
            gift += f"\t{mode}{a.to_gift_format()}\n"
        gift += "}"
        return gift
    
    def _get_percentage(self, answer: Answer):
        n = len(self.answers)
        n_correct = len([a for a in self.answers if a.correct])
        n_wrong = n - n_correct
        assert n_wrong == len([a for a in self.answers if not a.correct])
        return 100 / n_correct if answer.correct else -100 / n_wrong
    
    def __str__(self):
        answers = "\n".join(str(a) for a in self.answers)
        return f"[{self.category}] [{self.mode}] Title: {self.title}\n\n{self.text}\n\n{answers}"


def escape_special_gift_chars(s: str):
    return handle_special_gift_chars(s, True)


def extract_special_gift_chars(s: str):
    return handle_special_gift_chars(s, False)


def handle_special_gift_chars(s: str, escape: bool):
    if escape:
        # first, backslash escaping and then newline char (otherwise, manual
        # newline chars would be mapped to "<br>" as well)
        s = s.replace("\\", "\\\\")
        s = s.replace("\n", "<br>")
    else:  # extract
        # first, newline char extraction (once for "\n" and once for "<br>")
        # and then backslash extraction (otherwise, we could not distinguish
        # between true newline chars and manual newline chars)
        s = re.sub(r"(?<!\\)\\n", "\n", s)
        s = s.replace("<br>", "\n")
        s = s.replace("\\\\", "\\")
    chars = {"~", "=", "#", "{", "}", ":"}
    for c in chars:
        if escape:
            s = s.replace(c, rf"\{c}")
        else:  # extract
            s = s.replace(rf"\{c}", c)
    return s
