import json
import os
import argparse


def cal_weighted_score(input_file, output_file, lm_weight):
    """
    Calculate the weighted score for each entry in the input JSON file.
    """
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the JSON data
    with open(input_file, "r") as file:
        data = json.load(file)
    
    results = {}
    
    # Iterate over the data and calculate the weighted score
    for key, value in data.items():
        ASR_score = value["ASR_score"]
        llm_log_score = value["llm_log_score"]
        weighted_score = ASR_score + lm_weight * llm_log_score
        
        # Save the results
        results[key] = {
            "text": value["text"],
            "lm_weight": lm_weight,
            "asr_score": ASR_score,
            "llm_log_score": llm_log_score,
            "weighted_score": weighted_score,
            "token": value["token"],
            "token_int": value["token_int"],
            "temp": value["temp"]
        }

    # Save the results to a new JSON file
    with open(output_file, "w") as file:
        json.dump(results, file, indent=4)
    
    print(f"Results saved to {output_file}")


def process_directory(input_dir, output_dir, lm_weight):
    """
    Process all JSON files in the input directory and save results to the output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(input_dir):
        if file_name.endswith(".json"):
            input_file = os.path.join(input_dir, file_name)
            # Add '_w{lm_weight}' suffix to the output file name
            output_file_name = f"{os.path.splitext(file_name)[0]}_w{lm_weight}.json"
            output_file = os.path.join(output_dir, output_file_name)

            # Process each file
            cal_weighted_score(input_file, output_file, lm_weight)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON files in a directory and calculate weighted scores.") 
    parser.add_argument(
        "--input_dir", 
        type=str, 
        required=True, 
        help="Path to the input directory containing JSON files."
    )
    parser.add_argument(
        "--output_dir", 
        type=str, 
        required=True, 
        help="Path to the output directory for processed JSON files."
    )
    parser.add_argument(
        "--lm_weight", 
        type=float, 
        required=True, 
        help="Weight for the language model score."
    )
    
    args = parser.parse_args()
    process_directory(args.input_dir, args.output_dir, args.lm_weight)
