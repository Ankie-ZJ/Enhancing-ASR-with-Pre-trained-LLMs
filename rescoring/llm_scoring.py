import os
import json
import transformers
import torch
import math
from tqdm import tqdm
import argparse

PROMPT = \
"""
Your task is to evaluate the accuracy of the provided ASR transcript sentence on a scale from 0 to 1.

Follow these steps:

1. Analyze the ASR transcript sentence.
2. Provide a score based on its accuracy, ranging from 0 (completely inaccurate) to 1 (completely accurate).

Respond in JSON format as follows:
{
  "score": <your evaluation score>
}

Please only include the JSON object in your response.
"""

USER_INPUT = \
"""
The sentence you need to evaluate is delimited by double backticks:\n "{hyp}"
"""

class LLMScoer:
    def __init__(self, model_id: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"):
        self.HF_TOKEN = os.getenv("HF_TOKEN")
        self.model_id = model_id
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.load_model()
        print("device:", self.device)

    def load_model(self) -> transformers.pipeline:
        """
        Load the LLM pipeline.
        """
        print(f"Loading model: {self.model_id}")
        return transformers.pipeline(
            "text-generation",
            model=self.model_id,
            torch_dtype=torch.float16,
            device=self.device,
            token=self.HF_TOKEN,
        )

    def extract_score(self, outputs: str) -> float:
        """
        Extract the score from the model outputs.
        """
        try:
            # Attempt to load the string as JSON
            data = json.loads(outputs)
            
            # Check if 'score' exists in the parsed JSON
            if 'score' in data:
                return data['score']
            else:
                print("Error: 'score' key not found.", outputs)
                return 0
        except json.JSONDecodeError:
            # Handle invalid JSON
            print("Error: Invalid JSON input.", outputs)
            return 0

    def calculate_log_probability(self, score: float) -> float:
        """
        Calculate the log probability from a given score.
        """
        if not (0 <= score <= 1):
            print('Error: Score must be in the range (0, 1].')

        eps = 1e-10
        log_probability = math.log(max(score, eps)) 
        return log_probability

    def score(self, text: str, max_new_tokens: int = 256, temperature: float = 1.0) -> float:
        """
        Score the given text using the LLM.
        """

        # Create the input messages
        messages = [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": USER_INPUT.format(hyp=text)},
        ]

        # Generate the output
        outputs = self.model(
            messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        
        outputs = outputs[0]["generated_text"][-1]["content"]
        score = self.extract_score(outputs)
        
        log_score = self.calculate_log_probability(score)
        # print(score, log_score)
        return score, log_score

def main():
    parser = argparse.ArgumentParser(description="Evaluate ASR transcript accuracy using a language model.")
    parser.add_argument('--input_dir', type=str, required=True, help="Path to the input directory containing nbest files.")
    parser.add_argument('--output_dir', type=str, required=True, help="Path to the output directory for saving results.")
    parser.add_argument('--temp', type=float, default=1.0, help="Temperature for LLM generation.")

    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir
    temperature = args.temp

    # Initialize the LLM scorer by using the default model ID and device
    scorer = LLMScoer()

    # Create the output directory if it does not exist
    os.makedirs(output_dir, exist_ok=True)

    # Get all the nbest files in the input directory
    nbest_files = [file_name for file_name in os.listdir(input_dir) if file_name.endswith(".json")]

    for file_name in tqdm(nbest_files, desc="Processing nbest files"):
        nbest_file_path = os.path.join(input_dir, file_name)
        with open(nbest_file_path, "r") as f:
            data = json.load(f)

        # Score each object in the data
        for key, value in tqdm(data.items(), desc=f"Scoring objects in {file_name}", leave=False):
            if "text" in value:
                text = value["text"]
                llm_score, llm_log_score = scorer.score(text, temperature=temperature)
                value["llm_score"] = llm_score  
                value["llm_log_score"] = llm_log_score
                value["temp"] = temperature

        # Save the updated data to a new file
        output_file_path = os.path.join(output_dir, file_name)
        with open(output_file_path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Processed and saved: {output_file_path}")

if __name__ == "__main__":
    main()