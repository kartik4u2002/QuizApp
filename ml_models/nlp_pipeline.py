import re
import spacy
import spacy.cli
from typing import List, Dict, Any

class NLPPipeline:
    def __init__(self):
        # We use a small spacy model for performance. In production, en_core_web_sm or trf can be used.
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If not downloaded, download it
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def clean_text(self, text: str) -> str:
        """
        Removes HTML tags and extra whitespace from the text.
        """
        # Remove HTML tags
        clean = re.sub(r'<.*?>', '', text)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def extract_sentences(self, text: str) -> List[str]:
        """
        Splits text into sentences using spaCy.
        """
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
        return sentences

    def extract_keywords_ner(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts Named Entities which can be used as answers for questions.
        """
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            # We filter for specific entity types that make good quiz answers
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'LOC', 'DATE', 'EVENT', 'WORK_OF_ART']:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        return entities

    def process_article(self, raw_text: str) -> Dict[str, Any]:
        """
        Full pipeline to process a raw article.
        """
        cleaned = self.clean_text(raw_text)
        sentences = self.extract_sentences(cleaned)
        entities = self.extract_keywords_ner(cleaned)
        
        return {
            "cleaned_text": cleaned,
            "sentences": sentences,
            "entities": entities
        }

# Singleton instance for the service
nlp_pipeline = NLPPipeline()
