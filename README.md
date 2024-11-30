# Enhancing ASR with Pre-trained LLMs
- Jing Zhang (jingzha4@andrew.cmu.edu)
- Yuliang Jing (yuliangj@andrew.cmu.edu)
- Fengyifan Chen
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
To score the N-best hypotheses using the LLM, run `llm_scoring.py`. Example command is shown below:
```bash
python llm_scoring.py --input_dir /ocean/projects/cis240125p/jzhang45/Enhancing-ASR-with-Pre-trained-LLMs/parsed_asr_results/test_clean --output_dir /ocean/projects/cis240125p/jzhang45/Enhancing-ASR-with-Pre-trained-LLMs/rescoring/llm_score_result/test_clean --temp 1.0
```

### Step 4: Rescoring N-Best Hypotheses with Weighted Scores
Run the `rescoring.py` to calculate the weighted score. Example command is shown below:
```bash
python rescoring.py --input_file llm_score_result/test_other/1best.json --output_file weighted_score/test_other/1best.json --lm_weight 1.0
```

### Step 5: Generate Final Results for Evaluation
To generate the final result file (text, token, token_int) for evaluation, run `generate_best_result.py`. Example command is shown below:
```bash
python generate_best_result.py --input_dir /ocean/projects/cis240125p/jzhang45/Enhancing-ASR-with-Pre-trained-LLMs/rescoring/weighted_score/test_clean --output_dir result/test_clean
```

## TODO

- [ ] **Add evaluation scripts.**
- [ ] **Add the ability in `llm_scoring.py` to control how many hypotheses will be passed for scoring.**
- [ ] Analyze how different prompts influence accuracy (e.g., score all hypotheses together in a single prompt vs. score one hypothesis at a time, or use different prompt templates to evaluate their effects on accuracy).
- [ ] **Analyze how different temperature settings influence scoring (e.g., test with temperatures like 0.1, 0.5, 1.0, and compare their effects on scores).**
- [ ] **Analyze how different `llm weight` influence scoring**
- [ ] Analyze how the number of parameters influences scoring (e.g., have the LLM score a few hypotheses multiple times—e.g., 10 iterations—and analyze the score distribution to evaluate consistency and variability). (TODO: Jing)
- [ ] **Analyze how the number of n-best hypotheses influences accuracy (e.g., experiment with different `nbest` values such as 3, 5, 10, or 20 and compare their impact on overall ASR accuracy).**
- [ ] Analyze how different LLMs influence scoring (e.g., compare scoring performance using models).
