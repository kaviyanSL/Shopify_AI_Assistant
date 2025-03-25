from transformers import pipeline
class SentimentService:
    def __init__(self):
        self.model_five_classes = "nlptown/bert-base-multilingual-uncased-sentiment"

    def model_pipline(self):
        model = pipeline("sentiment-analysis", self.model_five_classes)
        return model
    
    def sentiment_analaysis (self,list_of_comments):
        model = self.model_pipline()
        sentiment_results = model(list_of_comments)
        list_results_and_reviews = []
        for reviews,results in zip (list_of_comments,sentiment_results):
            list_results_and_reviews.append(list((reviews,results)))
        return list_results_and_reviews

