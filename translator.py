import pandas as pd
import os
from pathlib import Path
from typing import Tuple
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect


class Translator:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
        self.model = MarianMTModel.from_pretrained(self.model_name)

    def translate_text(self, text: str) -> str:
        if detect(text) != 'en':
            tokenized_text = self.tokenizer.prepare_seq2seq_batch([text], return_tensors="pt")
            translated_output = self.model.generate(**tokenized_text)
            return self.tokenizer.batch_decode(translated_output, skip_special_tokens=True)[0]
        else:
            return text

    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        data['translated_text'] = data['text'].apply(self.translate_text)
        return data

    def save_data_to_csv(self, data: pd.DataFrame, output_csv: str):
        data.to_csv(output_csv, index=False)


def get_latest_file(dir_path: str) -> str:
    dir = Path(dir_path)
    return max(dir.glob("*.csv"), key=os.path.getctime)


def main(input_csv: str, output_csv: str):
    data = pd.read_csv(input_csv)
    processor = Translator(model_name="Helsinki-NLP/opus-mt-{}-en")
    processed_data = processor.process_data(data)
    processor.save_data_to_csv(processed_data, output_csv)


if __name__ == "__main__":
    input_file = get_latest_file("scraper_output")
    output_file = f"translated_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    main(input_file, output_file)

