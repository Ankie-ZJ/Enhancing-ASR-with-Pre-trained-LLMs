import os
import json
import argparse
import Levenshtein  # Ensure the python-Levenshtein library is installed
import string


def calculate_cer(hyp: str, ref: str) -> float:
    """
    Calculate Character Error Rate (CER).
    Args:
        hyp (str): Hypothesis string.
        ref (str): Reference string.
    Returns:
        float: CER score as a percentage.
    """
    # Clean and preprocess strings
    excluded_punctuation = "'"
    allowed_characters = string.punctuation.replace(excluded_punctuation, "")
    hyp = hyp.translate(str.maketrans("", "", allowed_characters)).upper()
    ref = ref.translate(str.maketrans("", "", allowed_characters)).upper()

    # Handle cases where reference is empty
    if len(ref) == 0:
        return 100.0 if len(hyp) > 0 else 0.0

    # Calculate CER using Levenshtein distance
    e_distance = Levenshtein.distance(ref, hyp)
    return (e_distance / len(ref)) * 100


def load_txt_file(file_path: str) -> (list, list):
    """
    Load a TXT file and return two lists: identifiers and sentences.
    Args:
        file_path (str): Path to the text file.
    Returns:
        list, list: A list of identifiers and a list of corresponding sentences.
    """
    identifiers = []
    sentences = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:  # Ensure both identifier and text are present
                identifiers.append(parts[0])
                sentences.append(parts[1])
            else:
                print(f"Warning: Skipping malformed line: {line.strip()}")
    return identifiers, sentences


def load_json_file(file_path: str) -> list:
    """
    Load a JSON file and extract all "text" fields.
    Args:
        file_path (str): Path to the JSON file.
    Returns:
        list: List of hypothesis sentences sorted by their keys.
    """
    hyps = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sorted_keys = sorted(data.keys())
            for key in sorted_keys:
                entry = data[key]
                if "text" in entry:
                    hyps.append(entry["text"])
                else:
                    print(f"Warning: Entry '{key}' is missing the 'text' field and will be skipped.")
        return hyps
    except FileNotFoundError:
        print(f"Hypotheses file not found: {file_path}")
        exit(1)
    except json.JSONDecodeError:
        print(f"Invalid JSON format in hypotheses file: {file_path}")
        exit(1)
    except Exception as e:
        print(f"Error reading hypotheses file: {e}")
        exit(1)


def process_hypothesis_folder(folder_path: str) -> dict:
    """
    Load all hypothesis JSON files in a folder.
    Args:
        folder_path (str): Path to the folder containing hypothesis JSON files.
    Returns:
        dict: A dictionary where keys are file names and values are lists of hypotheses.
    """
    hypotheses = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            hypotheses[file_name] = load_json_file(file_path)
    return hypotheses


def find_min_cer_filenames(ref_lines: list, hypotheses: dict, ref_ids: list) -> list:
    """
    Find the filename of the hypothesis with the minimum CER for each reference line.
    Args:
        ref_lines (list): List of reference sentences.
        hypotheses (dict): Dictionary of hypotheses, where keys are file names and values are lists of hypotheses.
        ref_ids (list): List of reference identifiers.
    Returns:
        list: List of strings in the format `identifier-hypfilename`.
    """
    min_cer_results = []

    for ref_idx, ref_line in enumerate(ref_lines):
        min_cer = float("inf")
        best_file_name = None

        # Iterate over all hypothesis files
        for hyp_file, hyp_lines in hypotheses.items():
            if ref_idx < len(hyp_lines):  # Ensure the line index is valid for the current hypothesis file
                hyp_line = hyp_lines[ref_idx]
                cer = calculate_cer(hyp_line, ref_line)

                if cer < min_cer:
                    min_cer = cer
                    best_file_name = hyp_file.split(".")[0]  # Remove file extension

        # Append the result in the desired format
        if best_file_name:
            min_cer_results.append(f"{ref_ids[ref_idx]}-{best_file_name}")

    return min_cer_results


def save_to_file(output_path: str, lines: list):
    """
    Save lines to a specified output file.
    Args:
        output_path (str): Path to the output file.
        lines (list): List of lines to save.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Select the hypothesis file with the minimum CER for each reference line.")
    parser.add_argument('--ref', type=str, required=True, help='Path to the reference TXT file (text_clean.txt).')
    parser.add_argument('--hyp_folder', type=str, required=True, help='Path to the folder containing hypothesis JSON files.')
    parser.add_argument('--output', type=str, required=True, help='Path to the output TXT file for filenames with minimum CER.')
    args = parser.parse_args()

    # Load reference lines and identifiers
    reference_ids, reference_lines = load_txt_file(args.ref)

    # Load hypothesis files from the specified folder
    hypotheses = process_hypothesis_folder(args.hyp_folder)

    # Find the filename with the minimum CER for each reference line
    min_cer_filenames = find_min_cer_filenames(reference_lines, hypotheses, reference_ids)

    # Save the result to the output file
    save_to_file(args.output, min_cer_filenames)

    print(f"Saved filenames with minimum CER to {args.output}")
