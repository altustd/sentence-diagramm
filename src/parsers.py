import spacy

class BaseParser:
    def __init__(self, model_name: str):
        self.nlp = spacy.load(model_name)
    
    def parse(self, sentence: str):
        return self.nlp(sentence)
    
    def to_text_diagram(self, doc) -> str:
        lines = []
        for token in doc:
            lines.append(f"{token.text} --{token.dep_}--> {token.head.text} ({token.pos_})")
        return "\n".join(lines)

class EnglishParser(BaseParser):
    def __init__(self):
        super().__init__("en_core_web_sm")

class GermanParser(BaseParser):
    def __init__(self):
        super().__init__("de_core_news_sm")

def get_parser(language: str):
    if language.lower() in ["english", "en"]:
        return EnglishParser()
    elif language.lower() in ["german", "de"]:
        return GermanParser()
    else:
        raise ValueError(f"Unsupported language: {language}")
