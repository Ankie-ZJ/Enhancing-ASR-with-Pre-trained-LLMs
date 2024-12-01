import json
import argparse
import sys
import Levenshtein  # Ensure the python-Levenshtein library is installed
from tabulate import tabulate  # For formatted table output
import jiwer  # Ensure the jiwer library is installed
import string
import os


def calculate_cer(hyp: str, ref: str) -> (float, dict):
    """
    Calculate Character Error Rate (CER) and provide error classification.
    Returns CER score and a dictionary with counts of correct characters, substitutions, deletions, and insertions.
    """
    # Define excluded and allowed punctuation for cleaning text
    excluded_punctuation = "'"
    allowed_characters = string.punctuation.replace(excluded_punctuation, "")

    # Preprocess hypothesis and reference: remove unwanted punctuation and convert to uppercase
    hyp = hyp.translate(str.maketrans("", "", allowed_characters)).upper()
    ref = ref.translate(str.maketrans("", "", allowed_characters)).upper()

    # Handle cases where reference is empty
    if len(ref) == 0:
        if len(hyp) == 0:
            return 0.0, {"correct": 0, "substitutions": 0, "deletions": 0, "insertions": 0}
        else:
            return 100.0, {"correct": 0, "substitutions": 0, "deletions": 0, "insertions": len(hyp)}

    # Calculate Levenshtein distance between hypothesis and reference
    e_distance = Levenshtein.distance(ref, hyp)
    score = e_distance / len(ref) * 100

    # Get detailed edit operations (substitutions, deletions, insertions)
    ops = Levenshtein.editops(ref, hyp)
    substitutions = sum(1 for op in ops if op[0] == "replace")
    deletions = sum(1 for op in ops if op[0] == "delete")
    insertions = sum(1 for op in ops if op[0] == "insert")

    # Calculate correct characters
    correct = len(ref) - (substitutions + deletions)

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
    transformation = jiwer.Compose([])

    ref_transformed = transformation(ref)
    hyp_transformed = transformation(hyp)

    wer_result = jiwer.compute_measures(ref_transformed, hyp_transformed)

    substitutions = wer_result.get('substitutions', 0)
    deletions = wer_result.get('deletions', 0)
    insertions = wer_result.get('insertions', 0)
    hits = wer_result.get('hits', 0)

    words_in_ref = len(ref_transformed.split())

    if words_in_ref == 0:
        return 0.0, {"correct": 0, "substitutions": 0, "deletions": 0, "insertions": 0}

    err_wer = (substitutions + deletions + insertions) / words_in_ref * 100

    return err_wer, {
        "correct": hits,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions
    }


def load_txt_file(file_path: str) -> list:
    """
    Load the reference TXT file and extract all sentences.
    Returns a list of sentences.
    """
    refs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
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


def load_json_file(file_path: str) -> list:
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

def process_cer(refs: list, hyps: list, total_sentences: int) -> dict:
    """
    Process CER for the given references and hypotheses.
    Returns a dictionary of aggregated results.
    """
    total_correct_cer = total_substitutions_cer = total_deletions_cer = total_insertions_cer = total_chars_ref = 0
    sentences_with_errors_cer = 0

    for hyp, ref in zip(hyps, refs):
        cer_score, cer_details = calculate_cer(hyp, ref)
        total_correct_cer += cer_details["correct"]
        total_substitutions_cer += cer_details["substitutions"]
        total_deletions_cer += cer_details["deletions"]
        total_insertions_cer += cer_details["insertions"]
        total_chars_ref += len(ref)
        if cer_details["substitutions"] + cer_details["deletions"] + cer_details["insertions"] > 0:
            sentences_with_errors_cer += 1

    corr_cer = (total_correct_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
    sub_cer = (total_substitutions_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
    del_cer = (total_deletions_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
    ins_cer = (total_insertions_cer / total_chars_ref) * 100 if total_chars_ref > 0 else 0.0
    err_cer = sub_cer + del_cer + ins_cer
    s_err_cer = (sentences_with_errors_cer / total_sentences) * 100

    return {
        "total_sentences": total_sentences,
        "total_chars_ref": total_chars_ref,
        "corr_cer": corr_cer,
        "sub_cer": sub_cer,
        "del_cer": del_cer,
        "ins_cer": ins_cer,
        "err_cer": err_cer,
        "s_err_cer": s_err_cer
    }


def process_wer(refs: list, hyps: list, total_sentences: int) -> dict:
    """
    Process WER for the given references and hypotheses.
    Returns a dictionary of aggregated results.
    """
    total_correct_wer = total_substitutions_wer = total_deletions_wer = total_insertions_wer = total_words_ref = 0
    sentences_with_errors_wer = 0

    for hyp, ref in zip(hyps, refs):
        wer_score, wer_details = calculate_wer(hyp, ref)
        total_correct_wer += wer_details["correct"]
        total_substitutions_wer += wer_details["substitutions"]
        total_deletions_wer += wer_details["deletions"]
        total_insertions_wer += wer_details["insertions"]
        total_words_ref += len(ref.split())
        if wer_details["substitutions"] + wer_details["deletions"] + wer_details["insertions"] > 0:
            sentences_with_errors_wer += 1

    corr_wer = (total_correct_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
    sub_wer = (total_substitutions_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
    del_wer = (total_deletions_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
    ins_wer = (total_insertions_wer / total_words_ref) * 100 if total_words_ref > 0 else 0.0
    err_wer = sub_wer + del_wer + ins_wer
    s_err_wer = (sentences_with_errors_wer / total_sentences) * 100

    return {
        "total_sentences": total_sentences,
        "total_words_ref": total_words_ref,
        "corr_wer": corr_wer,
        "sub_wer": sub_wer,
        "del_wer": del_wer,
        "ins_wer": ins_wer,
        "err_wer": err_wer,
        "s_err_wer": s_err_wer
    }


def output_results(results: dict, metric: list, output_path: str):
    """
    Outputs the results for CER/ WER in the specified format.
    """
    all_output_lines = []
    if metric in ['cer', 'both']:
        cer = results["cer"]
        cer_table = [[
            cer["total_sentences"],
            cer["total_chars_ref"],
            f"{cer['corr_cer']:.2f}",
            f"{cer['sub_cer']:.2f}",
            f"{cer['del_cer']:.2f}",
            f"{cer['ins_cer']:.2f}",
            f"{cer['err_cer']:.2f}",
            f"{cer['s_err_cer']:.2f}"
        ]]
        cer_headers = ["Snt", "Chrs", "Corr", "Sub", "Del", "Ins", "Err", "S.Err"]
        all_output_lines.append(tabulate(cer_table, headers=cer_headers, tablefmt="github"))

    if metric in ['wer', 'both']:
        wer = results["wer"]
        wer_table = [[
            wer["total_sentences"],
            wer["total_words_ref"],
            f"{wer['corr_wer']:.2f}",
            f"{wer['sub_wer']:.2f}",
            f"{wer['del_wer']:.2f}",
            f"{wer['ins_wer']:.2f}",
            f"{wer['err_wer']:.2f}",
            f"{wer['s_err_wer']:.2f}"
        ]]
        wer_headers = ["Snt", "Wrd", "Corr", "Sub", "Del", "Ins", "Err", "S.Err"]
        all_output_lines.append(tabulate(wer_table, headers=wer_headers, tablefmt="github"))

    full_output = "\n\n".join(all_output_lines)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write(full_output)
        print(f"Results have been saved to {output_path}")
    else:
        print(full_output)


def main():
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
        help='Path to the hypothesis TXT file.'
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

    # Load reference
    refs = load_txt_file(args.ref)

    # Load hypothesis
    hyp_extension = os.path.splitext(args.hyp)[1].lower()
    if hyp_extension == '.json':
        hyps = load_json_file(args.hyp)
    else:
        hyps = load_txt_file(args.hyp)

    if len(refs) != len(hyps):
        print(f"Error: The number of references ({len(refs)}) does not match the number of hypotheses ({len(hyps)}).")
        sys.exit(1)

    total_sentences = len(refs)

    # Initialize accumulators for CER and WER
    results = {}
    if args.metric in ['cer', 'both']:
        results["cer"] = process_cer(refs, hyps, total_sentences)

    if args.metric in ['wer', 'both']:
        results["wer"] = process_wer(refs, hyps, total_sentences)

    # Generate output
    output_results(results, args.metric, args.output)

if __name__ == "__main__":
    main()
