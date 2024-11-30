import json
import argparse
import sys
import Levenshtein  # Ensure the python-Levenshtein library is installed
from tabulate import tabulate  # For formatted table output
import jiwer  # Ensure the jiwer library is installed
from tokenizer import CharTokenizer
import string
import os


def calculate_cer(hyp: str, ref: str, tokenizer: CharTokenizer) -> (float, dict):
    """
    Calculate Character Error Rate (CER) and provide error classification.
    Returns CER score and a dictionary with counts of correct characters, substitutions, deletions, and insertions.
    """
    # Define characters to exclude from removal (e.g., keep `'`)
    excluded_punctuation = "'"
    allowed_characters = string.punctuation.replace(excluded_punctuation, "")

    # Preprocess hypothesis and reference
    hyp = hyp.translate(str.maketrans("", "", allowed_characters)).upper()
    ref = ref.translate(str.maketrans("", "", allowed_characters)).upper()

    # Tokenize hypothesis and reference
    hyp_tokens = tokenizer.text2tokens(hyp.strip())
    ref_tokens = tokenizer.text2tokens(ref.strip())

    # Convert tokens back to strings (retaining spaces)
    hyp_chars = "".join(hyp_tokens).replace(tokenizer.space_symbol, " ").strip()
    ref_chars = "".join(ref_tokens).replace(tokenizer.space_symbol, " ").strip()

    if len(ref_chars) == 0:
        if len(hyp_chars) == 0:
            return 0.0, {"correct": 0, "substitutions": 0, "deletions": 0, "insertions": 0}
        else:
            return 100.0, {"correct": 0, "substitutions": 0, "deletions": 0, "insertions": len(hyp_chars)}

    e_distance = Levenshtein.distance(ref_chars, hyp_chars)
    score = e_distance / len(ref_chars) * 100

    # Get detailed edit operations
    ops = Levenshtein.editops(ref_chars, hyp_chars)
    # Count substitutions, deletions, and insertions
    substitutions = sum(1 for op in ops if op[0] == "replace")
    deletions = sum(1 for op in ops if op[0] == "delete")
    insertions = sum(1 for op in ops if op[0] == "insert")

    # Calculate correct characters
    correct = len(ref_chars) - (substitutions + deletions)

    return score, {
        "correct": correct,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
    }


def calculate_wer(hyp: str, ref: str) -> (float, dict):
    """
    Calculate Word Error Rate (WER) and provide error classification.
    Returns WER score and a dictionary with counts of correct words, substitutions, deletions, and insertions.
    """
    transformation = jiwer.Compose([
        # Add transformation steps as needed, such as ignoring case or removing punctuation
        # jiwer.ToLowerCase(),  # Uncomment if you want to ignore case
        # jiwer.RemovePunctuation(),  # Uncomment if you want to remove punctuation
    ])

    ref_transformed = transformation(ref)
    hyp_transformed = transformation(hyp)

    # Use compute_measures to get detailed error information
    wer_result = jiwer.compute_measures(ref_transformed, hyp_transformed)

    # Extract error information
    substitutions = wer_result.get('substitutions', 0)
    deletions = wer_result.get('deletions', 0)
    insertions = wer_result.get('insertions', 0)
    hits = wer_result.get('hits', 0)

    # Calculate total number of words in reference
    words_in_ref = len(ref_transformed.split())

    if words_in_ref == 0:
        return 0.0, {"correct": 0, "substitutions": 0, "deletions": 0, "insertions": 0}

    # Calculate error rate percentages
    err_wer = (substitutions + deletions + insertions) / words_in_ref * 100
    # corr_wer = (hits / words_in_ref) * 100
    # sub_wer = (substitutions / words_in_ref) * 100
    # del_wer = (deletions / words_in_ref) * 100
    # ins_wer = (insertions / words_in_ref) * 100

    return err_wer, {
        "correct": hits,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions
    }


def load_reference_txt(file_path: str) -> list:
    """
    Load the reference TXT file and extract all sentences.
    Returns a list of reference sentences.
    """
    refs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    print(f"Warning: Line {line_num} does not contain an identifier and sentence text. Skipping this line.")
                    continue
                sentence = parts[1]
                refs.append(sentence)
        return refs
    except FileNotFoundError:
        print(f"Reference file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading reference file: {e}")
        sys.exit(1)


def load_hypotheses_json(file_path: str) -> list:
    """
    Load the hypotheses JSON file and extract all "text" fields.
    Returns a list of hypothesis sentences sorted by their keys.
    """
    hyps = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Sort the hypotheses by key to ensure consistent ordering with references
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
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Invalid JSON format in hypotheses file: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading hypotheses file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Script to calculate CER and WER without preprocessing.")
    parser.add_argument(
        '--ref',
        type=str,
        required=True,
        help='Path to the reference TXT file.'
    )
    parser.add_argument(
        '--hyp',
        type=str,
        required=True,
        help='Path to the hypotheses file or directory containing hypotheses files.'
    )
    parser.add_argument(
        '--metric',
        type=str,
        choices=['cer', 'wer', 'both'],
        default='both',
        help='Select the evaluation metric to compute.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to the output file. If not specified, results will be printed to the console.'
    )
    args = parser.parse_args()

    # Initialize tokenizer
    tokenizer = CharTokenizer()

    # Load reference
    refs = load_reference_txt(args.ref)

    # Check if `hyp` is a directory or file
    hyp_files = []
    if os.path.isdir(args.hyp):
        # Get all JSON files in the directory
        for root, _, files in os.walk(args.hyp):
            for file in files:
                if file.endswith(".json"):
                    hyp_files.append(os.path.join(root, file))
    else:
        # Single file
        hyp_files.append(args.hyp)

    # Initialize result accumulators
    all_output_lines = []

    # Process each hyp file
    for hyp_file in hyp_files:
        # Load hypotheses
        hyps = load_hypotheses_json(hyp_file)

        # Check if the number of references matches the number of hypotheses
        if len(refs) != len(hyps):
            print(f"Error: The number of references ({len(refs)}) does not match the number of hypotheses ({len(hyps)}) in {hyp_file}.")
            continue

        # Initialize accumulators for CER and WER
        total_correct_cer = total_substitutions_cer = total_deletions_cer = total_insertions_cer = total_chars_ref = 0
        total_correct_wer = total_substitutions_wer = total_deletions_wer = total_insertions_wer = total_words_ref = 0
        sentences_with_errors_wer = sentences_with_errors_cer = 0

        count = len(refs)

        # Calculate CER and WER for each sentence pair
        for hyp, ref in zip(hyps, refs):
            if args.metric in ['cer', 'both']:
                cer_score, cer_details = calculate_cer(hyp, ref, tokenizer)
                total_correct_cer += cer_details["correct"]
                total_substitutions_cer += cer_details["substitutions"]
                total_deletions_cer += cer_details["deletions"]
                total_insertions_cer += cer_details["insertions"]
                total_chars_ref += len(ref)
                if cer_details["substitutions"] + cer_details["deletions"] + cer_details["insertions"] > 0:
                    sentences_with_errors_cer += 1

            if args.metric in ['wer', 'both']:
                wer_score, wer_details = calculate_wer(hyp, ref)
                total_correct_wer += wer_details["correct"]
                total_substitutions_wer += wer_details["substitutions"]
                total_deletions_wer += wer_details["deletions"]
                total_insertions_wer += wer_details["insertions"]
                total_words_ref += len(ref.split())
                if wer_details["substitutions"] + wer_details["deletions"] + wer_details["insertions"] > 0:
                    sentences_with_errors_wer += 1

        # Calculate average CER and WER
        average_cer = (total_substitutions_cer + total_deletions_cer + total_insertions_cer) / total_chars_ref * 100 if args.metric in ['cer', 'both'] else None
        average_wer = (total_substitutions_wer + total_deletions_wer + total_insertions_wer) / total_words_ref * 100 if args.metric in ['wer', 'both'] else None

        # Prepare WER metrics
        if args.metric in ['wer', 'both']:
            corr_wer = (total_correct_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
            sub_wer = (total_substitutions_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
            del_wer = (total_deletions_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
            ins_wer = (total_insertions_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
            err_wer = sub_wer + del_wer + ins_wer
            s_err_wer = (sentences_with_errors_wer / count) * 100 if count > 0 else 0.0

            wer_table = [
                [
                    count,
                    total_words_ref,
                    f"{corr_wer:.2f}",
                    f"{sub_wer:.2f}",
                    f"{del_wer:.2f}",
                    f"{ins_wer:.2f}",
                    f"{err_wer:.2f}",
                    f"{s_err_wer:.2f}"
                ]
            ]
            wer_headers = ["Snt", "Wrd", "Corr", "Sub", "Del", "Ins", "Err", "S.Err"]

        # Prepare CER metrics
        if args.metric in ['cer', 'both']:
            corr_cer = (total_correct_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
            sub_cer = (total_substitutions_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
            del_cer = (total_deletions_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
            ins_cer = (total_insertions_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
            err_cer = sub_cer + del_cer + ins_cer
            s_err_cer = (sentences_with_errors_cer / count) * 100 if count > 0 else 0.0

            cer_table = [
                [
                    count,
                    total_chars_ref,
                    f"{corr_cer:.2f}",
                    f"{sub_cer:.2f}",
                    f"{del_cer:.2f}",
                    f"{ins_cer:.2f}",
                    f"{err_cer:.2f}",
                    f"{s_err_cer:.2f}"
                ]
            ]
            cer_headers = ["Snt", "Chrs", "Corr", "Sub", "Del", "Ins", "Err", "S.Err"]

        # Generate tables using tabulate
        if args.metric in ['wer', 'both']:
            all_output_lines.append(f"Results for {hyp_file} - WER")
            all_output_lines.append(tabulate(wer_table, headers=wer_headers, tablefmt="github"))
        if args.metric in ['cer', 'both']:
            all_output_lines.append(f"Results for {hyp_file} - CER")
            all_output_lines.append(tabulate(cer_table, headers=cer_headers, tablefmt="github"))

    # Combine all output
    full_output = "\n\n".join(all_output_lines)

    # Output the results
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as out_f:
                out_f.write(full_output)
            print(f"Results have been saved to {args.output}")
        except Exception as e:
            print(f"Unable to write to the output file: {e}")
            sys.exit(1)
    else:
        print(full_output)


