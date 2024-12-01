import os
import argparse
from eval_utils import process_cer, process_wer, load_txt_file

def ensure_txt_extension(file_path: str) -> str:
    """
    Ensure the file has a .txt extension.
    If the file is named 'text' without an extension, rename it to 'text.txt'.
    """
    base_name = os.path.basename(file_path)
    dir_name = os.path.dirname(file_path)
    # Check if the file exists and matches the criteria
    if base_name == "text" and os.path.exists(file_path):
        new_file_path = os.path.join(dir_name, "text.txt")
        
        # Perform renaming
        os.rename(file_path, new_file_path)
        print(f"[DEBUG] Renamed {file_path} to {new_file_path}")
        return new_file_path

    # If no renaming needed, return the original path
    return file_path

def generate_report(exp_dir: str, exp_tag: str):
    """
    Generate a report for all files in the experiment directory, recursively visiting all subfolders.
    """

    # Load reference texts
    text_clean_ref = load_txt_file('ref/text_clean.txt')
    text_other_ref = load_txt_file('ref/text_other.txt')
    
    # Write Title
    markdown_content = f"# {exp_tag}\n\n"

    # Storage for WER and CER results
    wer_clean_table = []
    wer_other_table = []
    cer_clean_table = []
    cer_other_table = []

    # Iterate over subdirectories in text_clean and text_other
    for root, dirs, files in sorted(os.walk(os.path.join(exp_dir, 'text_clean', exp_tag))):
        for file_name in sorted(files):
            # Parameters
            last_level = os.path.basename(root)

            # Full path of the current file
            file_path_clean = os.path.join(root, file_name)

            # Handle file extension
            file_path_clean = ensure_txt_extension(file_path_clean)
            file_path_other = ensure_txt_extension(os.path.join(
                exp_dir, 'text_other', exp_tag, os.path.basename(root), file_name
            ))

            if not file_path_clean.endswith('.txt') or not os.path.exists(file_path_clean) or not os.path.exists(file_path_other):
                
                continue

            print(f"[DEBUG] Processing {file_name} in {os.path.basename(root)}")
            
            # Load hypotheses
            hyps_clean = load_txt_file(file_path_clean)
            hyps_other = load_txt_file(file_path_other)
            
            # Calculate metrics for text_clean
            wer_clean = process_wer(text_clean_ref, hyps_clean, len(text_clean_ref))
            cer_clean = process_cer(text_clean_ref, hyps_clean, len(text_clean_ref))
            
            # Calculate metrics for text_other
            wer_other = process_wer(text_other_ref, hyps_other, len(text_other_ref))
            cer_other = process_cer(text_other_ref, hyps_other, len(text_other_ref))
            
           # Append to respective tables
            wer_clean_table.append({
                'Parameter': last_level,
                **wer_clean
            })
            wer_other_table.append({
                'Parameter': last_level,
                **wer_other
            })
            cer_clean_table.append({
                'Parameter': last_level,
                **cer_clean
            })
            cer_other_table.append({
                'Parameter': last_level,
                **cer_other
            })
    
    # Generate Markdown tables
    markdown_content = f"# {exp_tag}\n\n"
    
    # WER Clean Table
    markdown_content += "## WER_Clean\n\n"
    markdown_content += "| Parameter   | Snt   | Wrd   | Corr  | Sub  | Del  | Ins  | Err  | S.Err |\n"
    markdown_content += "|-------------|-------|-------|-------|------|------|------|------|-------|\n"
    for row in wer_clean_table:
        markdown_content += f"| {row['Parameter']} | {row['total_words_ref']} | {row['corr_wer']:.1f} | {row['sub_wer']:.1f} | {row['del_wer']:.1f} | {row['ins_wer']:.1f} | {row['err_wer']:.1f} | {row['s_err_wer']:.1f} |\n"
    
    markdown_content += "\n\n"

    # WER Other Table
    markdown_content += "## WER_Other\n\n"
    markdown_content += "| Parameter   | Snt   | Wrd   | Corr  | Sub  | Del  | Ins  | Err  | S.Err |\n"
    markdown_content += "|-------------|-------|-------|-------|------|------|------|------|-------|\n"
    for row in wer_other_table:
        markdown_content += f"| {row['Parameter']} | {row['total_words_ref']} | {row['corr_wer']:.2f} | {row['sub_wer']:.2f} | {row['del_wer']:.2f} | {row['ins_wer']:.2f} | {row['err_wer']:.2f} | {row['s_err_wer']:.2f} |\n"
    
    markdown_content += "\n\n"
    
    # CER Clean Table
    markdown_content += "## CER_Clean\n\n"
    markdown_content += "| Parameter   | Snt   | Char  | Corr  | Sub  | Del  | Ins  | Err  | S.Err |\n"
    markdown_content += "|-------------|-------|-------|-------|------|------|------|------|-------|\n"
    for row in cer_clean_table:
        markdown_content += f"| {row['Parameter']} | {row['total_chars_ref']} | {row['corr_cer']:.2f} | {row['sub_cer']:.2f} | {row['del_cer']:.2f} | {row['ins_cer']:.2f} | {row['err_cer']:.2f} | {row['s_err_cer']:.2f} |\n"
    
    markdown_content += "\n\n"

    # CER Other Table
    markdown_content += "## CER_Other\n\n"
    markdown_content += "| Parameter   | Snt   | Char  | Corr  | Sub  | Del  | Ins  | Err  | S.Err |\n"
    markdown_content += "|-------------|-------|-------|-------|------|------|------|------|-------|\n"
    for row in cer_other_table:
        markdown_content += f"| {row['Parameter']} | {row['total_chars_ref']} | {row['corr_cer']:.2f} | {row['sub_cer']:.2f} | {row['del_cer']:.2f} | {row['ins_cer']:.2f} | {row['err_cer']:.2f} | {row['s_err_cer']:.2f} |\n"
    
    # Save to markdown file
    if not os.path.exists("eval_results"):
        os.makedirs("eval_results")
    output_md_path = os.path.join("eval_results", f"{exp_tag}.md")
    with open(output_md_path, 'w') as f:
        f.write(markdown_content)

def main():
    parser = argparse.ArgumentParser(description="Calculate CER and WER for ASR-LLM outputs and generate markdown reports.")
    parser.add_argument('--exp_dir', type=str, required=True, help="Path to the experiment directory containing hypothesis files.")
    parser.add_argument('--exp_tag', type=str, required=True, help="Experiment tag to identify the output subdirectories.")
    # parser.add_argument('--output_md', type=str, required=True, help="Path to save the generated markdown file.")
    

    args = parser.parse_args()
    
    generate_report(
        exp_dir=args.exp_dir,
        exp_tag=args.exp_tag
        # output_md_path=args.output_md
    )

if __name__ == "__main__":
    main()
