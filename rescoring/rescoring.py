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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON file and calculate weighted scores.") 
    parser.add_argument(
        "--input_file", 
        type=str, 
        required=True, 
        help="Path to the input JSON file."
    )
    parser.add_argument(
        "--output_file", 
        type=str, 
        required=True, 
        help="Path to the output JSON file."
    )
    parser.add_argument(
        "--lm_weight", 
        type=float, 
        required=True, 
        help="Weight for the language model score."
    )
    
    args = parser.parse_args()
    cal_weighted_score(args.input_file, args.output_file, args.lm_weight)


