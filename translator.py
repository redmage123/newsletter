import os
import pandas as pd
from langdetect import detect
from transformers import MarianMTModel, MarianTokenizer
import sys
import glob
import datetime

class Translator:
    """
    Translator class for translating text using MarianMT models.
    """

    def __init__(self, models_root="models"):
        """
        Initializes the Translator class.

        Args:
            models_root (str, optional): The root directory containing the translation models. Defaults to "models".
        """
        self.models_root = models_root

    def translate_text(self, text, source_language):

        """
        Translates the given text to English.

        Args:
        text (str): The text to be translated.
        source_language (str): The source language code.

        Returns:
        str: The translated text in English.
        """

        cache_dir = "/home/bbrelin/src/repos/newsletter/.cache"

        if source_language == 'en':
            return text
        elif source_language in {'es', 'pt'}:
            model_name = "Helsinki-NLP/opus-mt-romance-en"
        else:
            try:
                model_name = f"Helsinki-NLP/opus-mt-{source_language}-en"
                model = MarianMTModel.from_pretrained(model_name,cache_dir = cache_dir)
                tokenizer = MarianTokenizer.from_pretrained(model_name)
            except OSError:
                model_name = "Helsinki-NLP/opus-mt-mul-en"
                model = MarianMTModel.from_pretrained(model_name,cache_dir = cache_dir)
                tokenizer = MarianTokenizer.from_pretrained(model_name)

            inputs = tokenizer(text, return_tensors="pt")
            translated = model.generate(**inputs)
            return tokenizer.decode(translated[0], skip_special_tokens=True)



    def process_data(self, data):

        """
        Processes the input DataFrame by translating the 'Content' column to English.

        Args:
            data (pd.DataFrame): The input DataFrame with a 'Content' column.


        Returns:
            pd.DataFrame: The output DataFrame with an additional 'translated_text' column containing the translated content in English.
        """
        data['translated_text'] = None

        def safe_translation(text):
           try:
               lang = detect(text)
               return self.translate_text(text, lang)
           except Exception as e:
               print(f"Error while translating text: {e}")
            # Default to a specific model or skip translation
               return text  # or self.translate_text(text, 'en')

        data['translated_text'] = data['Content'].apply(safe_translation)
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
