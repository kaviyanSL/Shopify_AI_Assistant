import logging
from textblob import TextBlob
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TextPreprocessingService:
    def __init__(self):
        pass

    def prompt_spell_correction(self,prompt):
        corrected_prompt = TextBlob(prompt)
        logging.info(f"prompt spell is corrected:{corrected_prompt}")
        return corrected_prompt