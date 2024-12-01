import os
import json
import argparse
import jiwer  # Ensure the jiwer library is installed


def calculate_wer(hyp: str, ref: str) -> float:
    """
    Calculate Word Error Rate (WER).
    Args:
        hyp (str): Hypothesis string.
        ref (str): Reference string.
    Returns:
        float: WER score as a percentage.
    """
    transformation = jiwer.Compose([])

    ref_transformed = transformation(ref)
    hyp_transformed = transformation(hyp)

    wer_result = jiwer.compute_measures(ref_transformed, hyp_transformed)

    substitutions = wer_result.get('substitutions', 0)
    deletions = wer_result.get('deletions', 0)
    insertions = wer_result.get('insertions', 0)

    words_in_ref = len(ref_transformed.split())

    if words_in_ref == 0:
        return 0.0

    return (substitutions + deletions + insertions) / words_in_ref * 100


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
            if len(parts) == 2:
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


def find_min_wer_filenames(ref_lines: list, hypotheses: dict, ref_ids: list) -> (list, list):
    """
    Find the filename of the hypothesis with the minimum WER for each reference line.
    Args:
        ref_lines (list): List of reference sentences.
        hypotheses (dict): Dictionary of hypotheses, where keys are file names and values are lists of hypotheses.
        ref_ids (list): List of reference identifiers.
    Returns:
        list, list: A list of strings in the format `identifier-hypfilename` and a list of WER scores.
    """
    min_wer_results = []
    wer_scores = []

    for ref_idx, ref_line in enumerate(ref_lines):
        min_wer = float("inf")
        best_file_name = None

        # Iterate over all hypothesis files
        for hyp_file, hyp_lines in hypotheses.items():
            if ref_idx < len(hyp_lines):  # Ensure the line index is valid for the current hypothesis file
                hyp_line = hyp_lines[ref_idx]
                wer = calculate_wer(hyp_line, ref_line)

                if wer < min_wer:
                    min_wer = wer
                    best_file_name = hyp_file.split(".")[0]  # Remove file extension

        if best_file_name:
            min_wer_results.append(f"{ref_ids[ref_idx]}-{best_file_name}")
            wer_scores.append(min_wer)

    return min_wer_results, wer_scores


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
    parser = argparse.ArgumentParser(description="Select the hypothesis file with the minimum WER for each reference line.")
    parser.add_argument('--ref', type=str, required=True, help='Path to the reference TXT file (text_clean.txt).')
    parser.add_argument('--hyp_folder', type=str, required=True, help='Path to the folder containing hypothesis JSON files.')
    parser.add_argument('--output', type=str, required=True, help='Path to the output TXT file for filenames with minimum WER.')
    args = parser.parse_args()

    # Load reference lines and identifiers
    reference_ids, reference_lines = load_txt_file(args.ref)

    # Load hypothesis files from the specified folder
    hypotheses = process_hypothesis_folder(args.hyp_folder)

    # Find the filename with the minimum WER for each reference line
    min_wer_filenames, wer_scores = find_min_wer_filenames(reference_lines, hypotheses, reference_ids)

    # Save the result to the output file
    save_to_file(args.output, min_wer_filenames)

    # Calculate and print the average WER
    average_wer = sum(wer_scores) / len(wer_scores) if wer_scores else 0.0
    print(f"Minimal Average WER: {average_wer:.2f}%")
    print(f"Saved filenames with minimum WER to {args.output}")
