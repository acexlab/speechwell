"""
File Logic Summary: Grammar analysis module. Algorithm generates corrected text with a seq2seq model and estimates grammar-error probability from word-count deltas.
"""

grammar_pipeline = None
_load_attempted = False


def _ensure_pipeline_loaded() -> bool:
    global grammar_pipeline, _load_attempted
    if grammar_pipeline is not None:
        return True
    if _load_attempted:
        return False
    _load_attempted = True

    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

        model_name = "prithivida/grammar_error_correcter_v1"
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=True)
        grammar_pipeline = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device=-1,  # CPU
        )
        return True
    except Exception:
        grammar_pipeline = None
        return False


def detect_grammar_errors(transcript: str) -> dict:

    if not transcript.strip():
        return {
            "grammar_error_probability": 0.0,
            "error_count_estimate": 0,
            "corrected_text": transcript
        }

    if not _ensure_pipeline_loaded():
        return {
            "grammar_error_probability": 0.0,
            "error_count_estimate": 0,
            "corrected_text": transcript,
        }

    corrected = grammar_pipeline(
        transcript,
        max_length=256,
        clean_up_tokenization_spaces=True
    )[0]["generated_text"]

    original_words = transcript.split()
    corrected_words = corrected.split()

    diff = abs(len(original_words) - len(corrected_words))
    error_estimate = max(diff, int(0.05 * len(original_words)))

    probability = min(error_estimate / max(len(original_words), 1), 1.0)

    return {
        "grammar_error_probability": round(probability, 3),
        "error_count_estimate": error_estimate,
        "corrected_text": corrected
    }

