import random
import logging
from typing import List, Dict, Any
from transformers import pipeline, T5ForConditionalGeneration, T5Tokenizer
import torch

logger = logging.getLogger(__name__)

class QuizEngine:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.qg_tokenizer = None
        self.qg_model = None
        self.fill_mask = None
        self._model_loaded = False

    def load_model(self):
        if self._model_loaded:
            return
            
        logger.info("Lazy loading T5 QG model...")
        try:
            model_name = "mrm8488/t5-base-finetuned-question-generation-ap"
            self.qg_tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)
            self.qg_model = T5ForConditionalGeneration.from_pretrained(model_name)
            if self.device == 0:
                self.qg_model = self.qg_model.to('cuda')
            logger.info("T5 Model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading T5 model: {e}")
            self.qg_model = None
            
        logger.info("Lazy loading BERT fill-mask model...")
        try:
            self.fill_mask = pipeline("fill-mask", model="bert-base-uncased", device=self.device)
            logger.info("BERT fill-mask model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading BERT model: {e}")
            self.fill_mask = None
            
        self._model_loaded = True

    def generate_question(self, context: str, answer: str) -> str:
        """
        Generates a question using T5 given a context sentence and the target answer.
        """
        self.load_model()
        
        if not self.qg_model:
            return f"What is the significance of {answer}?"

        input_text = f"answer: {answer}  context: {context} </s>"
        input_ids = self.qg_tokenizer.encode(input_text, return_tensors="pt")
        if self.device == 0:
            input_ids = input_ids.to('cuda')

        outputs = self.qg_model.generate(input_ids, max_length=64, num_beams=4, early_stopping=True)
        question = self.qg_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up 'question: ' prefix if present
        if question.lower().startswith("question:"):
            question = question[9:].strip()
            
        return question

    def generate_distractors(self, answer: str, context: str, label: str = None, all_entities: List[Dict[str, Any]] = None) -> List[str]:
        """
        Generates plausible distractors using intra-article entities, pre-defined pools,
        filtered BERT mask-filling, and smart numeric/linguistic variations.
        """
        import re
        distractors = []

        # Helper: Generate numeric variations (e.g. 2024 -> 2023, 2025, 2022)
        def get_numeric_variations(text: str) -> List[str]:
            match = re.search(r'\d+', text)
            if not match:
                return []
            num_str = match.group()
            try:
                val = int(num_str)
                offsets = [-1, 1, -2, 2, -5, 5, -10, 10]
                random.shuffle(offsets)
                variations = []
                for offset in offsets:
                    new_val = val + offset
                    if new_val > 0:
                        new_text = text.replace(num_str, str(new_val), 1)
                        if new_text.lower() != text.lower() and new_text not in variations:
                            variations.append(new_text)
                        if len(variations) >= 3:
                            break
                return variations
            except ValueError:
                return []

        # 1. Intra-Article Entity Distractors (Excellent quality)
        if label and all_entities:
            same_label_ents = []
            for ent in all_entities:
                ent_text = ent.get('text', '')
                if ent.get('label') == label and ent_text.lower() != answer.lower():
                    # Exclude substring overlaps to prevent redundant choices
                    if ent_text.lower() not in answer.lower() and answer.lower() not in ent_text.lower():
                        same_label_ents.append(ent_text)
            
            # Remove duplicates preserving some variety
            same_label_ents = list(set(same_label_ents))
            random.shuffle(same_label_ents)
            for item in same_label_ents:
                if item not in distractors:
                    distractors.append(item)
                if len(distractors) >= 3:
                    return distractors[:3]

        # 2. Try BERT Mask Filling (Filtered to avoid verbs/stopwords/vague fillers)
        try:
            self.load_model()
            if self.fill_mask and len(distractors) < 3:
                masked_context = context.replace(answer, "[MASK]", 1)
                if "[MASK]" in masked_context:
                    results = self.fill_mask(masked_context, top_k=15)
                    
                    # Stopwords, auxiliary verbs, and pronouns we must exclude
                    stopwords = {
                        'had', 'has', 'also', 'is', 'was', 'were', 'are', 'been', 'have', 
                        'do', 'does', 'did', 'the', 'a', 'an', 'and', 'but', 'or', 'of', 
                        'in', 'on', 'at', 'to', 'for', 'with', 'by', 'this', 'that', 'these', 
                        'those', 'it', 'they', 'he', 'she', 'we', 'you', 'me', 'him', 'her', 
                        'them', 'us', 'i', 'my', 'your', 'his', 'its', 'their', 'our', 'who', 
                        'whom', 'which', 'what', 'why', 'how', 'when', 'where', 'not', 'already', 
                        'recently', 'previously', 'then', 'so', 'if', 'than', 'as', 'will', 
                        'would', 'should', 'can', 'could', 'may', 'might', 'must', 'about', 
                        'more', 'some', 'any', 'other', 'another', 'such', 'very', 'too', 'just'
                    }
                    
                    generated = []
                    for res in results:
                        token = res['token_str'].strip()
                        if (token.lower() != answer.lower() and 
                            len(token) > 2 and 
                            token.isalpha() and 
                            token.lower() not in stopwords):
                            # Maintain title-case matching if the original was capitalized
                            formatted_token = token.title() if answer.istitle() else token
                            if formatted_token not in generated and formatted_token.lower() not in answer.lower():
                                generated.append(formatted_token)
                    
                    for token in generated:
                        if token not in distractors:
                            distractors.append(token)
                        if len(distractors) >= 3:
                            return distractors[:3]
        except Exception as e:
            logger.warning(f"BERT distractor extraction failed: {e}")

        # 3. Numeric variation fallback (e.g. dates, percentages, amounts)
        numeric_vars = get_numeric_variations(answer)
        for val in numeric_vars:
            if val not in distractors:
                distractors.append(val)
            if len(distractors) >= 3:
                return distractors[:3]

        # 4. Category-specific Pool Fallbacks
        LABEL_POOLS = {
            'DATE': [
                "last week", "earlier this month", "last month", "late last year", 
                "recently", "during the previous session", "in the coming weeks", 
                "at the start of the year", "last quarter", "next fiscal year"
            ],
            'PERSON': [
                "the spokesperson", "the agency head", "a committee representative", 
                "the cabinet secretary", "external advisors", "the program director",
                "the lead inspector", "department representatives"
            ],
            'ORG': [
                "the executive council", "the state department", "the governing committee", 
                "the regulatory body", "the oversight commission", "the national agency",
                "an independent audit team", "the board of directors"
            ],
            'GPE': [
                "the capital city", "neighboring regions", "the local municipality", 
                "state departments", "regional offices", "provincial headquarters",
                "the federal district", "neighboring territories"
            ],
            'LOC': [
                "neighboring regions", "the local district", "regional hubs", 
                "provincial zones", "coastal areas", "the metropolitan area"
            ],
            'EVENT': [
                "the annual review", "the general session", "the press conference", 
                "the official hearing", "the policy briefing", "the summit meeting",
                "the regulatory debate", "the public forum"
            ],
            'WORK_OF_ART': [
                "the new guidelines", "the official directive", "the published report", 
                "the strategic plan", "the regulatory draft", "the executive decree",
                "the procedural manual", "the operational standard"
            ]
        }

        pool = LABEL_POOLS.get(label, LABEL_POOLS['ORG'])
        random.shuffle(pool)
        for item in pool:
            # Format the fallback item matching original answer title case
            formatted_item = item.title() if answer.istitle() else item
            if formatted_item not in distractors:
                distractors.append(formatted_item)
            if len(distractors) >= 3:
                return distractors[:3]

        # 5. Last resort smart linguistic fallback (avoid vague 'Not {answer}')
        fallbacks = [
            f"An alternative to {answer}",
            f"A related context to {answer}",
            f"A different aspect of {answer}"
        ]
        for fb in fallbacks:
            if fb not in distractors:
                distractors.append(fb)
            if len(distractors) >= 3:
                break

        return distractors[:3]

    def create_quiz_from_article(self, article_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes processed article data (with sentences and entities) and generates MCQ items.
        """
        sentences = article_data.get("sentences", [])
        entities = article_data.get("entities", [])
        
        quiz_items = []
        used_answers = set()
        
        # We will attempt to create a question for up to 5 entities
        random.shuffle(entities)
        
        for ent in entities:
            answer = ent['text']
            if answer.lower() in used_answers or len(answer) < 3:
                continue
                
            # Find the sentence containing the entity
            context = None
            for sent in sentences:
                if answer in sent:
                    context = sent
                    break
            
            if not context:
                continue
                
            question = self.generate_question(context, answer)
            
            if len(question) < 10:
                continue
                
            distractors = self.generate_distractors(answer, context, ent.get('label'), entities)
            
            options = distractors + [answer]
            random.shuffle(options)
            
            quiz_items.append({
                "question": question,
                "options": options,
                "correct_answer": answer,
                "context": context
            })
            
            used_answers.add(answer.lower())
            
            if len(quiz_items) >= 5: # Limit to 5 questions per article
                break
                
        return quiz_items

quiz_engine = QuizEngine()
