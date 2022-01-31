from gui import QuestionCreator

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", type=str, help="GIFT file to open with startup.")
args = parser.parse_args()

QuestionCreator(file=args.file).start()
