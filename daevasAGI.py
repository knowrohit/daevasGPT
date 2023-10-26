import re
import torch
import json
from transformers import PreTrainedTokenizerFast
from transformers import (AutoModel, AutoTokenizer, AutoModelForSequenceClassification, 
                          MarianMTModel, MarianTokenizer, DistilBertForSequenceClassification, 
                          DistilBertTokenizer, DistilBertConfig, AutoModelForSeq2SeqLM)

class DaevasAGI:
    def __init__(self):
        # Load models and tokenizers
        self.chat_tokenizer = AutoTokenizer.from_pretrained("/Users/rohittiwari/Desktop/bernard/tokenizers/GLM_tokenizer", trust_remote_code=True)
        self.chat_model = AutoModel.from_pretrained("/Users/rohittiwari/Desktop/bernard/tokenizers/GLM_MODEL", trust_remote_code=True).half().cuda()
        self.chat_model.eval()

        self.sentiment_tokenizer = DistilBertTokenizer.from_pretrained("tokenizers/distilbert_sentiment_tokenizer")
        sentiment_config = DistilBertConfig.from_pretrained("configs/distilbert_sentiment_config")
        self.sentiment_model = DistilBertForSequenceClassification(sentiment_config)
        self.sentiment_model.load_state_dict(torch.load("models/distilbert_sentiment.pt"))

        self.enghi_tokenizer = AutoTokenizer.from_pretrained("tokenizers/enghitokenizer")
        self.enghi_model = AutoModelForSeq2SeqLM.from_pretrained("models/enghimodel")

        self.hieng_tokenizer = AutoTokenizer.from_pretrained("tokenizers/hiengtokenizer")
        self.hieng_model = AutoModelForSeq2SeqLM.from_pretrained("models/hiengmodel")

    def predict(self, input_text, history=None):
        if history is None:
            history = []
        response, _ = self.chat_model.chat(self.chat_tokenizer, input_text, history)
        history.append({"role": "system", "content": "User: " + input_text})
        history.append({"role": "system", "content": "ChatGLM-6B: " + response})
        return history

    def summarize_text(self, text):
        prompt = f"Summarize: {text}"
        history = self.predict(prompt)
        summary = history[-1]["content"].replace("ChatGLM-6B: ", "")
        return summary

    def analyze_sentiment(self, text):
        inputs = self.sentiment_tokenizer.encode(text, return_tensors="pt")
        outputs = self.sentiment_model(inputs)
        sentiment = torch.argmax(outputs.logits, dim=1).item()
        return "positive" if sentiment == 1 else "negative"

    def translate_text_between_languages(self, text, source_language, target_language):
        if source_language == 'en' and target_language == 'hi':
            tokenizer = self.enghi_tokenizer
            model = self.enghi_model
        elif source_language == 'hi' and target_language == 'en':
            tokenizer = self.hieng_tokenizer
            model = self.hieng_model
        else:
            raise ValueError("Invalid language pair")

        batch = tokenizer([text], return_tensors="pt")
        generated_ids = model.generate(**batch)
        translation = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return translation

    def chatbot(self, prompt):
        prompt_lower = prompt.lower()

        if "?" in prompt:
            history = self.predict(prompt)
            response = history[-1]["content"].replace("ChatGLM-6B: ", "")

        elif "summarize" in prompt_lower:
            text_to_summarize = prompt.replace("summarize", "").strip()
            response = self.summarize_text(text_to_summarize)

        elif "write code" in prompt_lower:
            history = self.predict(prompt)
            response = history[-1]["content"].replace("ChatGLM-6B: ", "")

        elif "translate to hindi" in prompt_lower:
            text_to_translate = re.sub(r"translate to hindi\W+", "", prompt, flags=re.IGNORECASE).strip()
            response = self.translate_text_between_languages(text_to_translate, 'en', 'hi')

        elif "translate to english" in prompt_lower:
            text_to_translate = re.sub(r"translate to english\W+", "", prompt, flags=re.IGNORECASE).strip()
            response = self.translate_text_between_languages(text_to_translate, 'hi', 'en')

        elif "sentiment" in prompt_lower:
            text_to_analyze = prompt.replace("sentiment", "").strip()
            response = self.analyze_sentiment(text_to_analyze)

        else:
            history = self.predict(prompt)
            response = history[-1]["content"].replace("ChatGLM-6B: ", "")

        return response

if __name__ == "__main__":
    daevas = DaevasAGI()

    prompts = [
    "What is the capital of Vatican city?",
    "Summarize: We’ve designed the first universal framework and methodology for connecting a global semantic context for any data item with the computational cost to produce it - a design pattern that encodes symbolic information and compute cost into unique IDs, removing the need for cloud platform based measurement and analytics approaches for intelligent control systems. Instead, systems architects can rely on a game theoretic approach to network design, aggregating information from competing data service providers. This ensures that dynamic, resilient systems can be created today to withstand the extreme environments of network fragmentation in 2030.",
    "write code to convert my chatbot.py to flask application. here is my python script : import re import torch from transformers import (AutoModel, AutoTokenizer, AutoModelForSequenceClassification, MarianMTModel, MarianTokenizer, DistilBertForSequenceClassification class DaevasAGI: def __init__(self): self.chat_tokenizer = AutoTokenizer.from_pretrained(/content/drive/MyDrive/bernard/chatglmmodel_tokenizer, trust_remote_code=True) self.chat_model = AutoModel.from_pretrained(/content/drive/MyDrive/bernard/chatglmmodel, trust_remote_code=True).half().cuda() self.chat_model.eval()  ",
    "translate to hindi: Hello, how are you",
    "translate to english: मेरा नाम रोहित है और मैं बर्लिन में रहता हूँ",
    "Sentiment: When it come to chicks, I never be the one to save,Keep on throwing ones, I'm with Mustard and we talkin' Lambo' talk (Skrrt, skrrt). Virgil dropped some Louis, I want everything he made and I'm just tryna relax. They always come off cool but in the end they come out wack. Her boyfriend getting mad, I told her he could take you back"
]


    for prompt in prompts:
        response = daevas.chatbot(prompt)
        print(f"User: {prompt}\nDaevasAGI: {response}\n")