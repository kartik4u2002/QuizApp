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

    def generate_distractors(self, answer: str, context: str) -> List[str]:
        """
        Generates plausible distractors. 
        For a production system, this can use a masked LM (BERT) or WordNet.
        Here we use a simple BERT mask filling approach if time permits, or mock it with variations.
        """
        # A simple fallback distractor generator based on the answer
        distractors = [
            f"Not {answer}",
            f"Alternative to {answer}",
            f"Fake {answer}"
        ]
        
        # Attempt to use BERT unmasking to find distractors if we load a fill-mask pipeline
        try:
            self.load_model()
            if self.fill_mask:
                masked_context = context.replace(answer, "[MASK]", 1)
                if "[MASK]" in masked_context:
                    results = self.fill_mask(masked_context, top_k=10)
                generated = []
                for res in results:
                    token = res['token_str']
                    if token.lower() != answer.lower() and len(token) > 2 and token.isalpha():
                        generated.append(token.title() if answer.istitle() else token)
                
                # Filter unique and take top 3
                unique_distractors = list(set(generated))
                if len(unique_distractors) >= 3:
                    return random.sample(unique_distractors, 3)
        except Exception:
            pass
            
        return distractors

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
                
            distractors = self.generate_distractors(answer, context)
            
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
