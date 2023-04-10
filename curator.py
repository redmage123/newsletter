import os
import glob
import pandas as pd
from datetime import datetime
from transformers import pipeline
from typing import Tuple


class RelevanceClassifier:
    def __init__(self):
        self.classifier = pipeline("zero-shot-classification")

    def classify_relevance(self, text: str) -> str:
        categories = ["High Relevance", "Low Relevance"]
        result = self.classifier(text, categories)
        return categories[result["labels"].index(result["scores"][0])]

    def process_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        data["relevance"] = data["translated_text"].apply(self.classify_relevance)
        high_relevance_data = data[data["relevance"] == "High Relevance"]
        low_relevance_data = data[data["relevance"] == "Low Relevance"]
        return high_relevance_data, low_relevance_data

    def save_data_to_csv(self, high_relevance_data: pd.DataFrame, low_relevance_data: pd.DataFrame):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        high_relevance_data.to_csv(f"high_relevance_{timestamp}.csv", index=False)
        low_relevance_data.to_csv(f"low_relevance_{timestamp}.csv", index=False)


def main(input_dir: str):
    list_of_files = glob.glob(os.path.join(input_dir, '*.csv'))
    latest_file = max(list_of_files, key=os.path.getctime)
    data = pd.read_csv(latest_file)
    classifier = RelevanceClassifier()
    high_relevance_data, low_relevance_data = classifier.process_data(data)
    classifier.save_data_to_csv(high_relevance_data, low_relevance_data)


if __name__ == "__main__":
    input_directory = "translator_output"
    main(input_directory)

