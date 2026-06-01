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
        Removes HTML tags, decodes HTML entities, strips NewsAPI truncation markers,
        and cleans up extra whitespaces.
        """
        import html
        # Decode HTML entities like &amp; &quot;
        text = html.unescape(text)
        # Remove HTML tags
        clean = re.sub(r'<.*?>', '', text)
        # Strip NewsAPI truncation markers like "… [+1511 chars]" or "[+123 chars]"
        clean = re.sub(r'\s*[…\.]*\s*\[\+\d+\s+chars\]', '', clean)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def extract_sentences(self, text: str) -> List[str]:
        """
        Splits text into sentences using spaCy, filtering out common web/cookie disclaimers.
        """
        doc = self.nlp(text)
        
        # Boilerplate indicators to filter out cookie/GDPR disclaimers
        boilerplate_keywords = [
            "accept all", "cookie policy", "privacy policy", "consent framework", 
            "iab transparency", "store and/or access", "personal data", "click accept",
            "geolocation data", "select 'manage settings'", "advertise with us", 
            "subscribe to our newsletter", "all rights reserved"
        ]
        
        sentences = []
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if len(sent_text) <= 20:
                continue
                
            # Check if this sentence is cookie consent or boilerplate
            is_boilerplate = False
            lower_sent = sent_text.lower()
            for kw in boilerplate_keywords:
                if kw in lower_sent:
                    is_boilerplate = True
                    break
            
            if not is_boilerplate:
                sentences.append(sent_text)
                
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
