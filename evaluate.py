import json
import time
import unicodedata
from pathlib import Path
from typing import Any

from rag import generate_answer


EVALUATION_FILE = Path("evaluation.json")
REPORT_FILE = Path("evaluation_report.json")


def normalize_text(text: str) -> str:
    """
        Ignores differences in case, Unicode representation, and extra
        whitespace. Also normalizes Turkish-specific characters
        (ı/i, ş/s, ğ/g, ü/u, ö/o, ç/c), since OCR output frequently
        corrupts these into their Latin counterparts
        (e.g., "algılama" -> "algilama"). Does not strip punctuation or
        numeric values.
    """
    normalized = unicodedata.normalize("NFKC", str(text))
    normalized = " ".join(normalized.split())
    normalized = normalized.casefold()

    normalized = normalized.translate(str.maketrans({
        "ı": "i", "İ": "i",
        "ş": "s", "Ş": "s",
        "ğ": "g", "Ğ": "g",
        "ü": "u", "Ü": "u",
        "ö": "o", "Ö": "o",
        "ç": "c", "Ç": "c",
    }))

    return normalized.casefold()

ENGLISH_FALLBACKS = {
    normalize_text("I could not find the answer in the provided documents."),
    normalize_text("No relevant information was found in the uploaded documents."),
}

TURKISH_FALLBACKS = {
    normalize_text("Bu soruya ilişkin bilgi yüklenen belgelerde bulunamadı."),
}

def load_evaluation_cases() -> list[dict[str, Any]]:
    if not EVALUATION_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation file not found: {EVALUATION_FILE.resolve()}"
        )

    with EVALUATION_FILE.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError(
            "evaluation.json must contain a JSON array."
        )

    if not cases:
        raise ValueError(
            "evaluation.json does not contain any test cases."
        )

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(
                f"Test case {index} must be a JSON object."
            )

        if not case.get("question"):
            raise ValueError(
                f"Test case {index} does not contain a question."
            )

        has_exact_answer = "expected_answer" in case
        has_contains_answer = "expected_answer_contains" in case

        if not has_exact_answer and not has_contains_answer:
            raise ValueError(
                f"Test case {index} must contain expected_answer "
                "or expected_answer_contains."
            )

    return cases


def check_answer(test_case: dict[str, Any],actual_answer: str,) -> tuple[bool, str]:
    normalized_actual = normalize_text(actual_answer)

    # Hallucination tests
    if test_case.get("expected_source") is None:
        passed = any(
            fallback in normalized_actual
            for fallback in ENGLISH_FALLBACKS | TURKISH_FALLBACKS
        )

        return (passed,"Document not found fallback",)
        
    if "expected_answer" in test_case:
        expected_answer = str(test_case["expected_answer"])
        normalized_expected = normalize_text(expected_answer)

        # Instead of an exact match, we check whether the expected answer
        # is contained within the actual answer.
        # For example, expected "12%", actual answer "The IGST rate is 12%."
        passed = normalized_expected in normalized_actual

        return passed, expected_answer

    expected_parts = test_case.get(
        "expected_answer_contains",
        [],
    )

    if not isinstance(expected_parts, list):
        raise ValueError(
            "expected_answer_contains must be a JSON array."
        )

    missing_parts = [
        str(part)
        for part in expected_parts
        if normalize_text(str(part)) not in normalized_actual
    ]

    passed = len(missing_parts) == 0

    if passed:
        expected_description = ", ".join(
            str(part)
            for part in expected_parts
        )
    else:
        expected_description = (
            "Missing: " + ", ".join(missing_parts)
        )

    return passed, expected_description


def normalize_filename(filename: str) -> str:
    """
    Ignores folder path and case differences when comparing sources.
    """
    return Path(str(filename)).name.casefold()


def check_source(test_case: dict[str, Any],actual_sources: list[str],) -> tuple[bool | None, str | None]:
    expected_source = test_case.get("expected_source")

    if expected_source is None:
        return None, None

    normalized_expected = normalize_filename(str(expected_source))

    normalized_sources = [
        normalize_filename(source)
        for source in actual_sources
    ]

    passed = normalized_expected in normalized_sources

    return passed, str(expected_source)


def get_retrieved_sources(results: list[dict[str, Any]],) -> list[str]:
    sources = []

    for result in results:
        source = result.get("source")

        if source and source not in sources:
            sources.append(source)

    return sources


def run_test(number: int,total: int,test_case: dict[str, Any],) -> dict[str, Any]:
    
    question = test_case["question"]

    print("=" * 80)
    print(f"TEST {number}/{total}")
    print("=" * 80)
    print(f"Question: {question}")

    started_at = time.perf_counter()

    try:
        result = generate_answer(question)

        duration = time.perf_counter() - started_at

        actual_answer = result.get("answer", "")
        actual_sources = result.get("sources", [])
        retrieval_results = result.get("results", [])

        answer_passed, expected_description = check_answer(
            test_case=test_case,
            actual_answer=actual_answer,
        )

        source_passed, expected_source = check_source(
            test_case=test_case,
            actual_sources=actual_sources,
        )

        answer_status = (
            "PASS"
            if answer_passed
            else "FAIL"
        )

        if source_passed is None:
            source_status = "NOT CHECKED"
        else:
            source_status = (
                "PASS"
                if source_passed
                else "FAIL"
            )

        print(f"Answer status : {answer_status}")
        print(f"Source status : {source_status}")
        print(f"Duration      : {duration:.2f} seconds")
        print(f"Expected      : {expected_description}")
        print(f"Actual answer : {actual_answer}")

        if expected_source is not None:
            print(f"Expected source: {expected_source}")

        if actual_sources:
            print(
                "Actual sources : "
                + ", ".join(actual_sources)
            )
        else:
            print("Actual sources : None")

        if retrieval_results:
            print("\nTop retrieval results:")

            for rank, retrieval in enumerate(
                retrieval_results,
                start=1,
            ):
                source = retrieval.get(
                    "source",
                    "Unknown source",
                )

                score = retrieval.get("score")

                if isinstance(score, (int, float)):
                    score_text = f"{score:.6f}"
                else:
                    score_text = "N/A"

                print(
                    f"  {rank}. {source} "
                    f"(score={score_text})"
                )

        print()

        overall_passed = (answer_passed and source_passed is not False)

        return {
            "question": question,
            "passed": overall_passed,
            "answer_passed": answer_passed,
            "source_passed": source_passed,
            "expected": expected_description,
            "expected_source": expected_source,
            "actual_answer": actual_answer,
            "actual_sources": actual_sources,
            "retrieved_sources": get_retrieved_sources(retrieval_results),
            "duration_seconds": round(duration, 3),
            "error": None,
        }

    except Exception as error:
        duration = time.perf_counter() - started_at

        print("Status   : ERROR")
        print(f"Duration : {duration:.2f} seconds")
        print(f"Error    : {error}")
        print()

        return {
            "question": question,
            "passed": False,
            "answer_passed": False,
            "source_passed": None,
            "expected": test_case.get(
                "expected_answer",
                test_case.get(
                    "expected_answer_contains"
                ),
            ),
            "expected_source": test_case.get(
                "expected_source"
            ),
            "actual_answer": None,
            "actual_sources": [],
            "retrieved_sources": [],
            "duration_seconds": round(duration, 3),
            "error": str(error),
        }


def save_report(test_results: list[dict[str, Any]], summary: dict[str, Any],) -> None:
    report = {
        "summary": summary,
        "tests": test_results,
    }

    with REPORT_FILE.open("w",encoding="utf-8",) as file:
        json.dump(report,file,ensure_ascii=False,indent=2,)


def main() -> None:
    test_cases = load_evaluation_cases()

    total = len(test_cases)

    print()
    print("=" * 80)
    print("RAG EVALUATION")
    print("=" * 80)
    print(f"Evaluation file : {EVALUATION_FILE}")
    print(f"Number of tests : {total}")
    print()

    all_started_at = time.perf_counter()

    test_results = []

    for number, test_case in enumerate(
        test_cases,
        start=1,
    ):
        test_result = run_test(number=number,total=total,test_case=test_case,)

        test_results.append(test_result)

    total_duration = (time.perf_counter() - all_started_at)

    answer_passed_count = sum(
        1
        for result in test_results
        if result["answer_passed"]
    )

    source_checked_results = [
        result
        for result in test_results
        if result["source_passed"] is not None
    ]

    source_passed_count = sum(
        1
        for result in source_checked_results
        if result["source_passed"]
    )

    overall_passed_count = sum(
        1
        for result in test_results
        if result["passed"]
    )

    error_count = sum(
        1
        for result in test_results
        if result["error"] is not None
    )

    answer_accuracy = (answer_passed_count / total * 100)

    overall_accuracy = (overall_passed_count / total * 100)

    if source_checked_results:
        source_accuracy = (
            source_passed_count
            / len(source_checked_results)
            * 100
        )
    else:
        source_accuracy = None

    average_duration = (total_duration / total)

    summary = {
        "total_tests": total,
        "overall_passed": overall_passed_count,
        "overall_accuracy_percent": round(
            overall_accuracy,
            2,
        ),
        "answer_passed": answer_passed_count,
        "answer_accuracy_percent": round(
            answer_accuracy,
            2,
        ),
        "source_checked": len(
            source_checked_results
        ),
        "source_passed": source_passed_count,
        "source_accuracy_percent": (
            round(source_accuracy, 2)
            if source_accuracy is not None
            else None
        ),
        "errors": error_count,
        "total_duration_seconds": round(
            total_duration,
            3,
        ),
        "average_duration_seconds": round(
            average_duration,
            3,
        ),
    }

    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    print(
        f"Overall          : "
        f"{overall_passed_count}/{total} "
        f"({overall_accuracy:.2f}%)"
    )

    print(
        f"Answer accuracy  : "
        f"{answer_passed_count}/{total} "
        f"({answer_accuracy:.2f}%)"
    )

    if source_accuracy is not None:
        print(
            f"Source Hit@K     : "
            f"{source_passed_count}/"
            f"{len(source_checked_results)} "
            f"({source_accuracy:.2f}%)"
        )
    else:
        print("Source Hit@K     : Not checked")

    print(f"Errors           : {error_count}")
    print(
        f"Total duration   : "
        f"{total_duration:.2f} seconds"
    )
    print(
        f"Average duration : "
        f"{average_duration:.2f} seconds"
    )

    failed_results = [
        result
        for result in test_results
        if not result["passed"]
    ]

    if failed_results:
        print("\nFailed questions:")

        for result in failed_results:
            print(f"- {result['question']}")

            if result["error"]:
                print(f"  Error: {result['error']}")
            else:
                if not result["answer_passed"]:
                    print("  Reason: Answer check failed")

                if result["source_passed"] is False:
                    print("  Reason: Source check failed")

    save_report(
        test_results=test_results,
        summary=summary,
    )

    print(
        f"\nDetailed report written to: "
        f"{REPORT_FILE.resolve()}"
    )


if __name__ == "__main__":
    main()