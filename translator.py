import os
import pandas as pd
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from transformers import MarianMTModel, MarianTokenizer
import sys
import glob
import datetime
from tqdm import tqdm
from typing import List


class Translator:
    def __init__(self):
        pass

    def translate_batch(self, texts: List[str], source_language: str) -> List[str]:

        """
        Translates a batch of texts to English.

        Args:
            texts (List[str]): A list of texts to be translated.
            source_language (str): The source language code.

        Returns:
            List[str]: A list of translated texts in English.
        """

        cache_dir = "/home/bbrelin/src/repos/newsletter/.cache"

        if source_language == 'en':
            return texts
        elif source_language in {'es', 'pt'}:
            model_name = "Helsinki-NLP/opus-mt-romance-en"
        else:
            model_name = f"Helsinki-NLP/opus-mt-{source_language}-en"

        try:
            model = MarianMTModel.from_pretrained(model_name, cache_dir=cache_dir)
            tokenizer = MarianTokenizer.from_pretrained(model_name)
        except OSError:
            model_name = "Helsinki-NLP/opus-mt-mul-en"
            model = MarianMTModel.from_pretrained(model_name, cache_dir=cache_dir)
            tokenizer = MarianTokenizer.from_pretrained(model_name)

        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        translated = model.generate(**inputs)
        return [tokenizer.decode(t, skip_special_tokens=True) for t in translated]

    def process_data(self, data: pd.DataFrame, batch_size: int = 10) -> pd.DataFrame:
        """
        Processes the input DataFrame by translating the 'Content' column to English.

        Args:
            data (pd.DataFrame): The input DataFrame with a 'Content' column.
            batch_size (int, optional): The number of texts to be translated in a batch. Defaults to 10.

        Returns:
            pd.DataFrame: The output DataFrame with an additional 'translated_text' column containing the translated content in English.
        """
        data['translated_text'] = None

        def safe_translation(texts, source_language):
            try:
                return self.translate_batch(texts, source_language)
            except Exception as e:
                print(f"Error while translating text: {e}")
                return texts

        texts = data['Content'].tolist()
        translated_texts = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Translating"):
            batch = texts[i:i + batch_size]
            source_languages = [detect(text) for text in batch]
            batch_translations = [safe_translation([text], lang) for text, lang in zip(batch, source_languages)]
            translated_texts.extend(batch_translations)

        data['translated_text'] = translated_texts
        return data

def main(scraper_output_directory="/home/bbrelin/src/repos/newsletter/scraper_output"):

    """
    Reads data from the latest input CSV file in the scraper_output_directory, translates the content to English.

    Args:
        scraper_output_directory (str, optional): The directory containing the scraper output CSV files. Defaults to "/home/bbrelin/src/repos/newsletter/scraper_output".
    """


    list_of_files = glob.glob(os.path.join(scraper_output_directory, "scrape_results_*.csv"))
    latest_file = max(list_of_files, key=os.path.getmtime)

    input_file_path = latest_file
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file_name = f"translated_{os.path.basename(latest_file).split('_', 1)[1].split('.', 1)[0]}_{current_time}.csv"
    output_file_path = os.path.join(os.getcwd(), "translated_output", output_file_name)

    data = pd.read_csv(input_file_path)
    processor = Translator()
    processed_data = processor.process_data(data)
    processed_data.to_csv(output_file_path, index=False)

if __name__ == "__main__":

    if len(sys.argv) == 2:
        scraper_output_directory = sys.argv[1]
    else:
        scraper_output_directory = "/home/bbrelin/src/repos/newsletter/scraper_output"

    main(scraper_output_directory)
