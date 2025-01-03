# Enhancing ASR with Pre-trained LLMs
- Jing Zhang (jingzha4@andrew.cmu.edu)
- Yuliang Jing (yuliangj@andrew.cmu.edu)
- Fengyifan Chen (fengyifc@andrew.cmu.edu)
## Set Up Environment

To set up the environment, run the following script:

```bash
./setup.sh
```

Then setup your Hugging Face token:
```bash
export HF_TOKEN=<your_hf_token>
```

## Steps to Generate and Process N-Best Hypotheses, and Perform Rescoring
### Step 1: Run ASR to Generate N-Best Hypotheses
```bash
cd espnet/egs2/librispeech_100/asr1
cd conf
```

Update the `decode_asr.yaml` file and specify the number of hypotheses you want:
```yaml
nbest: <number_of_hypotheses>
```

Then run the ASR model to generate N-Best Hypotheses
```bash
./run.sh --skip_data_prep false --skip_train true --download_model pyf98/librispeech_100_e_branchformer
```

The N-best results will be generated and saved in the following locations:

- `exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_clean/logdir/output.1`
- `exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_clean/logdir/output.2`
- `exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_other/logdir/output.1`
- `exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_other/logdir/output.2`

### Step 2: Prepare Data for External LLM Integration
Run the `parse_asr_result.py` for preparing data. Example commands are shown below:
```bash
python parse_asr_result.py --base_dir /ocean/projects/cis240125p/jzhang45/espnet/egs2/librispeech_100/asr1/exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_clean/logdir --output_dir parsed_asr_results/test_clean/

python parse_asr_result.py --base_dir /ocean/projects/cis240125p/jzhang45/espnet/egs2/librispeech_100/asr1/exp/pyf98/librispeech_100_e_branchformer/decode_asr_asr_model_valid.acc.ave/test_other/logdir --output_dir parsed_asr_results/test_other/
```

### Step 3: Score N-Best Hypotheses with External LLM
To score the N-best hypotheses using the LLM, run `llm_scoring.py`.  

Parameters: 1. `temp` used to adjust the temperature 2. `start_best` and `end_best` used to select the range of the input file (e.g. --start_best 1 --end_best 10, selects 1best to 10best as the input file)  

Example command is shown below:
```bash
python llm_scoring.py --input_dir /ocean/projects/cis240125p/jzhang45/Enhancing-ASR-with-Pre-trained-LLMs/parsed_asr_results/test_clean --output_dir /ocean/projects/cis240125p/jzhang45/Enhancing-ASR-with-Pre-trained-LLMs/rescoring/llm_score_result/test_clean --temp 1.0 --start_best 1 --end_best 10
```

### Step 4: Rescoring N-Best Hypotheses with Weighted Scores
Option1(Process a single file) Run the `rescoring.py` to calculate the weighted score. Example command is shown below:
```bash
python rescoring.py --input_file llm_score_result/test_other/1best.json --output_file weighted_score/test_other/1best.json --lm_weight 1.0
```

Option2(Processes all files in a given directory) Run the `multi_rescoring.py` to calculate the weighted score. Example command is shown below:
```bash
python multi_rescoring.py --input_dir llm_score_result/test_other --output_dir weighted_score/test_other --lm_weight 1.0
```

### Step 5: Generate Final Results for Evaluation
Option1(generate single result): To generate the final result file (text, token, token_int) for evaluation, run `generate_best_result.py`. Example command is shown below:
```bash
python generate_best_result.py --input_dir /ocean/projects/cis240125p/jzhang45/Enhancing-ASR-with-Pre-trained-LLMs/rescoring/weighted_score/test_clean --output_dir result/test_clean
```
Option2(generate multiple results): To generate multiple final result files (text, token, token_int) for evaluation, run `generate_best_result_multi.py`. Example command is shown below:
```bash
python generate_best_result_multi.py --num_best 20 --input_dir /ocean/projects/cis240125p/yjing2/group_project/Enhancing-ASR-with-Pre-trained-LLMs/rescoring/weighted_score/test_clean --output_dir result/test_clean 
```

### Step 6(New): Evaluate Results with Regard to WER and CER
![image](https://github.com/user-attachments/assets/fe976c86-4973-45f7-b580-06e9f96b186b)
The format of exp_dir should follow the structure shown in the picture above. All the files need to be evaluated should be in the path named after exp_tag.
```bash
python eval.py --exp_dir test_results --exp_tag nbest_exps
```

### Step 6(Old): Evaluate Results with Regard to WER and CER
To calculate the wer and cer for the generated final results file. Metrics can be selected as: "wer", "cer" or "both".

Option1 (Calculate all hypothesis files in a given directory) Example command is shown below:
```bash
python rescoring/eval_utils.py --ref "./data/text_clean.txt" --hyp "./rescoring/weighted_score/test_clean" --metric "both" --output "./rescoring/eval_results/test_clean/weighted_result.txt"
```

Option2 (Calculate a single hypothesis file) Example command is shown below:
```bash
python rescoring/eval_utils.py --ref "./data/text_clean.txt" --hyp "./rescoring/weighted_score/test_clean/1best_temp0.2_w0.5.json" --metric "both" --output "./rescoring/eval_results/test_clean/weighted_result.txt"
```
