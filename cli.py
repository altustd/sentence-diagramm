import argparse
from src.parsers import get_parser

parser = argparse.ArgumentParser(description="Sentence diagramming CLI")
parser.add_argument("--lang", choices=["en", "de", "es"], default="en", help="Language code")
parser.add_argument("sentence", nargs="+", help="The sentence to parse")
args = parser.parse_args()

lang_map = {"en": "English", "de": "German", "es": "Spanish"}
parser = get_parser(lang_map[args.lang])
sent = " ".join(args.sentence)
doc = parser.parse(sent)
print(parser.to_text_diagram(doc))
