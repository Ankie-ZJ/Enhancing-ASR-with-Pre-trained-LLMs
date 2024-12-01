import os
import argparse
from eval_utils import process_cer, process_wer, load_txt_file

def generate_report(exp_dir: str, exp_tag: str, output_md_path: str):
    """
    Generate a report for all files in the experiment directory.

    An Example Directory Structure:
    ├── exp_dir
    │   ├── text_clean
    │   │   └── exp_tag
    │   │       ├── text_1.txt
    │   │       └── text_2.txt
    │   └── text_other
    │       └── exp_tag
    │           ├── text_1.txt
    │           └── text_2.txt
    """

    # Load reference texts
    text_clean_ref = load_txt_file('ref/text_clean.txt')
    text_other_ref = load_txt_file('ref/text_other.txt')
    
    # Write Title
    markdown_content = f"# {exp_tag}\n\n"

    # Iterate over hypothesis files
    for file_name in sorted(os.listdir(os.path.join(exp_dir, 'text_clean', exp_tag))):
        file_path_clean = os.path.join(exp_dir, 'text_clean', exp_tag, file_name)
        file_path_other = os.path.join(exp_dir, 'text_other', exp_tag, file_name)
        
        if not file_name.endswith('.txt') or not os.path.exists(file_path_clean) or not os.path.exists(file_path_other):
            print(f"Skipping {file_name}")
            continue

        print(f"Processing {file_name}")
            
        # Load hypotheses
        hyps_clean = load_txt_file(file_path_clean)
        hyps_other = load_txt_file(file_path_other)
        
        # Calculate metrics for text_clean
        wer_clean = process_wer(text_clean_ref, hyps_clean, len(text_clean_ref))
        cer_clean = process_cer(text_clean_ref, hyps_clean, len(text_clean_ref))
        
        # Calculate metrics for text_other
        wer_other = process_wer(text_other_ref, hyps_other, len(text_other_ref))
        cer_other = process_cer(text_other_ref, hyps_other, len(text_other_ref))
        
        # Append to markdown
        markdown_content += f"## {exp_tag}/{file_name}\n\n"
        
        # Combined WER Table
        markdown_content += "### WER\n\n"
        markdown_content += "| Dataset     | Snt   | Wrd   | Corr  | Sub  | Del  | Ins  | Err  | S.Err |\n"
        markdown_content += "|-------------|-------|-------|-------|------|------|------|------|-------|\n"
        markdown_content += f"| text_clean  | {len(text_clean_ref)} | {wer_clean['total_words_ref']} | {wer_clean['corr_wer']:.1f} | {wer_clean['sub_wer']:.1f} | {wer_clean['del_wer']:.1f} | {wer_clean['ins_wer']:.1f} | {wer_clean['err_wer']:.1f} | {wer_clean['s_err_wer']:.1f} |\n"
        markdown_content += f"| text_other  | {len(text_other_ref)} | {wer_other['total_words_ref']} | {wer_other['corr_wer']:.1f} | {wer_other['sub_wer']:.1f} | {wer_other['del_wer']:.1f} | {wer_other['ins_wer']:.1f} | {wer_other['err_wer']:.1f} | {wer_other['s_err_wer']:.1f} |\n\n"
        
        # Combined CER Table
        markdown_content += "### CER\n\n"
        markdown_content += "| Dataset     | Snt   | Char  | Corr  | Sub  | Del  | Ins  | Err  | S.Err |\n"
        markdown_content += "|-------------|-------|-------|-------|------|------|------|------|-------|\n"
        markdown_content += f"| text_clean  | {len(text_clean_ref)} | {cer_clean['total_chars_ref']} | {cer_clean['corr_cer']:.1f} | {cer_clean['sub_cer']:.1f} | {cer_clean['del_cer']:.1f} | {cer_clean['ins_cer']:.1f} | {cer_clean['err_cer']:.1f} | {cer_clean['s_err_cer']:.1f} |\n"
        markdown_content += f"| text_other  | {len(text_other_ref)} | {cer_other['total_chars_ref']} | {cer_other['corr_cer']:.1f} | {cer_other['sub_cer']:.1f} | {cer_other['del_cer']:.1f} | {cer_other['ins_cer']:.1f} | {cer_other['err_cer']:.1f} | {cer_other['s_err_cer']:.1f} |\n\n"

    # Save to markdown file
    with open(output_md_path, 'w') as f:
        f.write(markdown_content)

def main():
    parser = argparse.ArgumentParser(description="Calculate CER and WER for ASR-LLM outputs and generate markdown reports.")
    parser.add_argument('--exp_dir', type=str, required=True, help="Path to the experiment directory containing hypothesis files.")
    parser.add_argument('--exp_tag', type=str, required=True, help="Experiment tag to identify the output subdirectories.")
    parser.add_argument('--output_md', type=str, required=True, help="Path to save the generated markdown file.")
    

    args = parser.parse_args()
    
    generate_report(
        exp_dir=args.exp_dir,
        exp_tag=args.exp_tag,
        output_md_path=args.output_md
    )
    print(f"Markdown report saved to {args.output_md}")

if __name__ == "__main__":
    main()
