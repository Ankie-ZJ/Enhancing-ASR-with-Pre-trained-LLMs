import os
import json
import argparse

def parse_asr_result(base_dir: str) -> dict:
    """
    Parse the ASR result from running the ESPnet recipe, which could be found under the `exp` directory.
    e.g. exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_other/logdir/output.1
    """
    results_by_nbest = {}

    # Iterate over each folder in the directory
    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)

        # Check if the current path is a directory
        if os.path.isdir(folder_path):
            
            score_file = os.path.join(folder_path, "score")
            text_file = os.path.join(folder_path, "text")
            token_file = os.path.join(folder_path, "token")
            token_int_file = os.path.join(folder_path, "token_int")
            
            # Read those files
            if os.path.exists(score_file) and os.path.exists(text_file):
                with open(score_file, "r") as sf, open(text_file, "r") as tf, open(token_file, "r") as tof, open(token_int_file, "r") as tif:
                    score_lines = sf.readlines()
                    text_lines = tf.readlines()
                    token_lines = tof.readlines()
                    token_int_lines = tif.readlines()
                    
                # Parse the files and classify by nbest
                for score_line, text_line, token_lines, token_int_lines in zip(score_lines, text_lines, token_lines, token_int_lines):
                    score_parts = score_line.strip().split()
                    text_parts = text_line.strip().split(maxsplit=1)
                    token_parts = token_lines.strip().split(maxsplit=1)
                    token_int_parts = token_int_lines.strip().split(maxsplit=1)

                    # Check if the parts are valid
                    if len(score_parts) == 2 and len(text_parts) == 2 and len(token_parts) == 2 and len(token_int_parts) == 2:
                        # Extract ID, score, and text
                        id_key = f"{score_parts[0]}_{folder.split('_')[0]}"
                        asr_score = float(score_parts[1].replace("tensor(", "").replace(")", ""))
                        asr_text = text_parts[1]
                        token = token_parts[1]
                        token_int = token_int_parts[1]

                        # Extract nbest value from folder name
                        nbest_key = folder.split("_")[0]

                        # Initialize the nbest dictionary
                        if nbest_key not in results_by_nbest:
                            results_by_nbest[nbest_key] = {}

                        # Add the parsed result to the corresponding nbest dictionary
                        results_by_nbest[nbest_key][id_key] = {
                            "ASR_score": asr_score,
                            "text": asr_text,
                            "token": token,
                            "token_int": token_int
                        }
                    else:
                        print(f"Invalid parts: {score_parts}, {text_parts}, {token_parts}, {token_int_parts}")

    return results_by_nbest

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Parse recognition files from output.* directories.")
    # e.g. /ocean/projects/cis240125p/jzhang45/espnet/egs2/librispeech_100/asr1/exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_clean/logdir
    parser.add_argument(
        "--base_dir",
        required=True,
        help="Base directory to scan for output.* directories."
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory where output JSON files will be saved."
    )

    args = parser.parse_args()
    base_dir = args.base_dir
    output_dir = args.output_dir

    # Check if the output dir exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize a dict to store merged results by nbest
    final_results_by_nbest = {}

    # Parse files in each dir and merge results
    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)

        # Only process dir that match "output.*"
        if os.path.isdir(folder_path) and folder.startswith("output."):
            print(f"Processing: {folder_path}")
            results_by_nbest = parse_asr_result(folder_path)
            for nbest, results in results_by_nbest.items():
                if nbest not in final_results_by_nbest:
                    final_results_by_nbest[nbest] = {}
                final_results_by_nbest[nbest].update(results)

    # Save results to separate JSON files and count objects to double check
    for nbest, results in final_results_by_nbest.items():
        output_file = os.path.join(output_dir, f"{nbest}.json")
        with open(output_file, "w") as out_file:
            json.dump(results, out_file, indent=4)

        object_count = len(results) 
        print(f"Results for {nbest}best saved to: {output_file} with {object_count} objects.")

if __name__ == "__main__":
    main()




# import os
# import json

# def parse_recog_files(base_dir):
#     # Initialize a dictionary to store results by nbest
#     results_by_nbest = {}

#     # Iterate over each folder in the directory
#     for folder in sorted(os.listdir(base_dir)):
#         folder_path = os.path.join(base_dir, folder)
#         print(folder_path)
#         # Ensure the current path is a directory
#         if os.path.isdir(folder_path):
#             # Define paths for the `score` and `text` files
#             score_file = os.path.join(folder_path, "score")
#             text_file = os.path.join(folder_path, "text")
            
#             # Read the score and text files
#             if os.path.exists(score_file) and os.path.exists(text_file):
#                 with open(score_file, "r") as sf, open(text_file, "r") as tf:
#                     score_lines = sf.readlines()
#                     text_lines = tf.readlines()

#                 # Parse the files and classify by nbest
#                 for score_line, text_line in zip(score_lines, text_lines):
#                     score_parts = score_line.strip().split()
#                     text_parts = text_line.strip().split(maxsplit=1)

#                     if len(score_parts) == 2 and len(text_parts) == 2:
#                         # Extract ID, score, and text
#                         id_key = f"{score_parts[0]}_{folder.split('_')[0]}"
#                         asr_score = float(score_parts[1].replace("tensor(", "").replace(")", ""))
#                         asr_text = text_parts[1]

#                         # Extract nbest value from folder name
#                         nbest_key = folder.split("_")[0]

#                         # Ensure the nbest dictionary exists
#                         if nbest_key not in results_by_nbest:
#                             results_by_nbest[nbest_key] = {}

#                         # Add the parsed result to the corresponding nbest dictionary
#                         results_by_nbest[nbest_key][id_key] = {
#                             "ASR_score": asr_score,
#                             "text": asr_text
#                         }

#     return results_by_nbest

# # Define the base directories
# base_dirs = [
#     "/ocean/projects/cis240125p/jzhang45/espnet/egs2/librispeech_100/asr1/exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_other/logdir/output.1",
#     "/ocean/projects/cis240125p/jzhang45/espnet/egs2/librispeech_100/asr1/exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_other/logdir/output.2"
# ]

# # Initialize a dictionary to store merged results by nbest
# final_results_by_nbest = {}

# # Parse files in each directory and merge results
# for base_dir in base_dirs:
#     results_by_nbest = parse_recog_files(base_dir)
#     for nbest, results in results_by_nbest.items():
#         if nbest not in final_results_by_nbest:
#             final_results_by_nbest[nbest] = {}
#         final_results_by_nbest[nbest].update(results)

# # Save results to separate JSON files and count objects
# output_dir = "/ocean/projects/cis240125p/jzhang45/espnet/egs2/librispeech_100/asr1/exp/pyf98"
# for nbest, results in final_results_by_nbest.items():
#     output_file = os.path.join(output_dir, f"parsed_results_{nbest}.json")
#     with open(output_file, "w") as out_file:
#         json.dump(results, out_file, indent=4)
#     object_count = len(results)  # Count the number of objects
#     print(f"Results for {nbest}best saved to: {output_file} with {object_count} objects.")
