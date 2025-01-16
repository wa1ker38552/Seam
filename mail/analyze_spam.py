from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch.nn.functional as F
import torch


def predict_spam(text):
    max_length = model.config.max_position_embeddings
    inputs = tokenizer(
        text, 
        return_tensors="pt", 
        truncation=True,
        padding=True, 
        max_length=max_length
    )

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probabilities = F.softmax(logits, dim=-1)
    predicted_class = torch.argmax(probabilities, dim=-1).item()
    labels = ['not spam', 'spam']
    predicted_label = labels[predicted_class]
    
    return predicted_label

# initialize model
model_name = "mrm8488/bert-tiny-finetuned-sms-spam-detection"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)