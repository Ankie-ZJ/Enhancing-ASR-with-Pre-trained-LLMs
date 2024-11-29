# import json
# import os

# # List of input JSON files
# input_files = [
#     "weighted_score_result/test_other/weighted_score_result_1best.json",
#     "weighted_score_result/test_other/weighted_score_result_2best.json",
#     "weighted_score_result/test_other/weighted_score_result_3best.json",
# ]

# # Output text file
# output_file = "result/text_other/text"

# # Dictionary to store the best result for each ID
# best_results = {}

# # Iterate over each input file
# for file in input_files:
#     with open(file, "r") as f:
#         data = json.load(f)
#         for key, value in data.items():
#             transcript_id = key.rsplit("_", 1)[0]  # Extract the common ID
#             weighted_score = value["weighted_score"]
#             # Update the best result if it's the first entry or a higher score
#             if (
#                 transcript_id not in best_results
#                 or weighted_score > best_results[transcript_id]["weighted_score"]
#             ):
#                 best_results[transcript_id] = {
#                     "text": value["text"],
#                     "token": value["token"],
#                     "token_int": value["token_int"],
#                     "weighted_score": weighted_score,
#                 }

# # Write the best results to the output text file
# with open(output_file, "w") as f:
#     for transcript_id, result in best_results.items():
#         f.write(f"{transcript_id} {result['text']}\n")

# print(f"Best transcripts saved to {output_file}")
import os
import json
import argparse

def process_files(input_folder, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Output files
    output_text_file = os.path.join(output_folder, "text")
    output_token_file = os.path.join(output_folder, "token")
    output_token_int_file = os.path.join(output_folder, "token_int")

    # Dict to store the best result for each ID
    best_results = {}

    # Iterate over all JSON files in the input folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".json"):
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

    print(f"Text saved to {output_text_file}")
    print(f"Tokens saved to {output_token_file}")
    print(f"Token int saved to {output_token_int_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process weighted score JSON files.")
    parser.add_argument("--input_dir", type=str, help="Path to the input folder containing JSON files.")
    parser.add_argument("--output_dir", type=str, help="Path to the output folder to save results.")
    args = parser.parse_args()

    process_files(args.input_dir, args.output_dir)
