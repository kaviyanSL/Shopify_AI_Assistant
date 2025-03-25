from transformers import pipeline
from src.main.service.GarbageCollectorServicec import GarbageCollectorServicec
import torch
class SentimentService:
    def __init__(self):
        self.model_five_classes = "nlptown/bert-base-multilingual-uncased-sentiment"
        self.device = 0 if torch.cuda.is_available() else -1

    def model_pipline(self):
        model = pipeline("sentiment-analysis", self.model_five_classes, device = self.device)
        return model
    
    def sentiment_analaysis (self,list_of_comments):
        try:
            model = self.model_pipline()
            sentiment_results = model(list_of_comments)
            list_results_and_reviews = []
            for reviews,results in zip (list_of_comments,sentiment_results):
                list_results_and_reviews.append(list((reviews,results)))
        finally:
                gc = GarbageCollectorServicec(sentiment_results)
                gc.garbage_collecting()
        return list_results_and_reviews

