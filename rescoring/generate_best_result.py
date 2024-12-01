import os
import json
import argparse
import re

def process_files_in_directory(base_input_dir, output_base_dir, num_best):
    # Iterate over all subdirectories in the base input directory
    for folder_name in os.listdir(base_input_dir):
        folder_path = os.path.join(base_input_dir, folder_name)
        if os.path.isdir(folder_path):  # Check if it's a directory
            print(f"Processing folder: {folder_path}")
            process_files(folder_path, output_base_dir, num_best)

def process_files(input_folder, output_base_dir, num_best):
    # Dynamically append the last part of the input folder to the output base directory
    input_folder_name = os.path.basename(os.path.normpath(input_folder))
    output_folder = os.path.join(output_base_dir, f"{input_folder_name}_{num_best}best")
    os.makedirs(output_folder, exist_ok=True)

    # Output files
    output_text_file = os.path.join(output_folder, "text")
    output_token_file = os.path.join(output_folder, "token")
    output_token_int_file = os.path.join(output_folder, "token_int")

    # Dict to store the best result for each ID
    best_results = {}

    # Regex to extract the number before 'best' in file names
    best_file_pattern = re.compile(r"(\d+)best")

    # List all JSON files and sort based on the number before 'best'
    files = [f for f in os.listdir(input_folder) if f.endswith(".json") and best_file_pattern.search(f)]
    files_sorted = sorted(
        files, 
        key=lambda x: int(best_file_pattern.search(x).group(1))  # Sort by the extracted number
    )

    # Print the selected files
    print(f"Files in '{input_folder}' to be processed:")
    for file_name in files_sorted[:num_best]:
        print(f"  {file_name}")

    # Select the top num_best files
    selected_files = files_sorted[:num_best]

    # Process the selected files
    for file_name in selected_files:
        file_path = os.path.join(input_folder, file_name)
        with open(file_path, "r") as f:
            data = json.load(f)
            for key, value in data.items():
                transcript_id = key.rsplit("_", 1)[0]  # Extract the ID
                weighted_score = value["weighted_score"]

                # Update the best result if it's the first entry or a higher score
                if (
                    transcript_id not in best_results
                    or weighted_score > best_results[transcript_id]["weighted_score"]
                ):
                    best_results[transcript_id] = {
                        "text": value["text"],
                        "token": value["token"],
                        "token_int": value["token_int"],
                        "weighted_score": weighted_score,
                    }

    # Write the best results to the output text files
    with open(output_text_file, "w") as text_file, \
         open(output_token_file, "w") as token_file, \
         open(output_token_int_file, "w") as token_int_file:
        for transcript_id, result in best_results.items():
            text_file.write(f"{transcript_id} {result['text']}\n")
            token_file.write(f"{transcript_id} {result['token']}\n")
            token_int_file.write(f"{transcript_id} {result['token_int']}\n")

    print(f"Results saved in folder: {output_folder}")
    print(f"Text saved to {output_text_file}")
    print(f"Tokens saved to {output_token_file}")
    print(f"Token int saved to {output_token_int_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process weighted score JSON files.")
    parser.add_argument("--input_dir", type=str, help="Path to the base input folder containing subdirectories.")
    parser.add_argument("--output_dir", type=str, help="Base path for the output folder.")
    parser.add_argument("--num_best", type=int, default=1, help="Number of top files to process based on their best order.")
    args = parser.parse_args()

    process_files_in_directory(args.input_dir, args.output_dir, args.num_best)
