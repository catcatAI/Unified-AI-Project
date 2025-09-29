
class TonalRepairEngine:
    def repair_output(self, original_text: str, issues: List[str]) -> str:
        """
        Repairs the text based on the detected issues.
        """
        repaired_text = original_text
        for issue in issues:
            if issue == "repetitive":
                repaired_text = " ".join(sorted(set(repaired_text.split), key=repaired_text.split.index))
            elif issue == "negative_sentiment":
                repaired_text = f"I'm sorry to hear that. It sounds like you're saying: {repaired_text}"
        return f"Repaired: {repaired_text}"