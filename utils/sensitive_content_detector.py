"""
Sensitive Content Detection Module for the Personal AI Employee system.
Detects emotional, legal, medical, and other sensitive contexts that require human approval.
"""

import re
from typing import Dict, List, Set, Tuple
from enum import Enum


class SensitivityCategory(Enum):
    """Categories of sensitive content."""
    EMOTIONAL = "emotional"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    PERSONAL = "personal"
    BUSINESS_CRITICAL = "business_critical"
    AUTHORITY = "authority"
    COMPLIANCE = "compliance"


class SensitiveContentDetector:
    """
    Class to detect sensitive content in text that requires human approval.
    """

    def __init__(self):
        """Initialize the sensitive content detector with predefined patterns."""

        # Emotional content indicators
        self.emotional_keywords = {
            'angry', 'frustrated', 'disappointed', 'concerned', 'unhappy',
            'dissatisfied', 'terrible', 'awful', 'horrible', 'annoyed',
            'upset', 'mad', 'irritated', 'livid', 'furious', 'enraged',
            'devastated', 'heartbroken', 'hurt', 'offended', 'betrayed'
        }

        # Legal content indicators
        self.legal_keywords = {
            'legal', 'lawyer', 'lawsuit', 'contract', 'agreement', 'terms',
            'liability', 'responsibility', 'court', 'attorney', 'litigation',
            'dispute', 'settlement', 'compliance', 'regulatory', 'violation',
            'penalty', 'fine', 'sanction', 'subpoena', 'warrant', 'hearing'
        }

        # Medical content indicators
        self.medical_keywords = {
            'medical', 'health', 'doctor', 'hospital', 'medicine', 'prescription',
            'patient', 'treatment', 'condition', 'diagnosis', 'symptoms',
            'therapy', 'pharmacy', 'clinic', 'nurse', 'physician', 'surgery',
            'medication', 'illness', 'disease', 'injury', 'recovery'
        }

        # Financial content indicators
        self.financial_keywords = {
            'payment', 'invoice', 'refund', 'charge', 'money', 'financial',
            'bank', 'account', 'credit', 'debit', 'expense', 'budget',
            'salary', 'compensation', 'payroll', 'tax', 'investment',
            'loan', 'mortgage', 'insurance', 'broker', 'stocks'
        }

        # Personal/private content indicators
        self.personal_keywords = {
            'personal', 'private', 'confidential', 'secret', 'intimate',
            'family', 'child', 'relative', 'spouse', 'partner', 'husband',
            'wife', 'son', 'daughter', 'mother', 'father', 'parents',
            'siblings', 'private', 'intimate', 'confidential'
        }

        # Business critical content indicators
        self.business_critical_keywords = {
            'urgent', 'emergency', 'critical', 'immediate', 'asap', 'now',
            'crisis', 'problem', 'issue', 'failure', 'breakdown', 'outage',
            'emergency', 'alert', 'warning', 'recall', 'shutdown', 'incident'
        }

        # Authority figure indicators
        self.authority_keywords = {
            'manager', 'director', 'ceo', 'boss', 'supervisor', 'hr',
            'human resources', 'executive', 'president', 'vp', 'lead',
            'chief', 'head', 'administrator', 'officer', 'superintendent'
        }

        # Compliance/regulatory indicators
        self.compliance_keywords = {
            'compliance', 'regulatory', 'audit', 'policy', 'procedure',
            'governance', 'ethics', 'standards', 'requirements', 'rules',
            'guidelines', 'certification', 'license', 'permit', 'approval'
        }

        # Compile regex patterns for more sophisticated matching
        self.patterns = {
            SensitivityCategory.EMOTIONAL: re.compile(
                r'\b(?:' + '|'.join(self.emotional_keywords) + r')\b',
                re.IGNORECASE
            ),
            SensitivityCategory.LEGAL: re.compile(
                r'\b(?:' + '|'.join(self.legal_keywords) + r')\b',
                re.IGNORECASE
            ),
            SensitivityCategory.MEDICAL: re.compile(
                r'\b(?:' + '|'.join(self.medical_keywords) + r')\b',
                re.IGNORECASE
            ),
            SensitivityCategory.FINANCIAL: re.compile(
                r'\b(?:' + '|'.join(self.financial_keywords) + r')\b',
                re.IGNORECASE
            ),
            SensitivityCategory.PERSONAL: re.compile(
                r'\b(?:' + '|'.join(self.personal_keywords) + r')\b',
                re.IGNORECASE
            ),
            SensitivityCategory.BUSINESS_CRITICAL: re.compile(
                r'\b(?:' + '|'.join(self.business_critical_keywords) + r')\b',
                re.IGNORECASE
            ),
            SensitivityCategory.AUTHORITY: re.compile(
                r'\b(?:' + '|'.join(self.authority_keywords) + r')\b',
                re.IGNORECASE
            ),
            SensitivityCategory.COMPLIANCE: re.compile(
                r'\b(?:' + '|'.join(self.compliance_keywords) + r')\b',
                re.IGNORECASE
            ),
        }

    def detect_sensitive_content(self, text: str, sender: str = "") -> List[Tuple[SensitivityCategory, str]]:
        """
        Detect sensitive content in the provided text.

        Args:
            text: Text to analyze for sensitive content
            sender: Optional sender information for additional context

        Returns:
            List of tuples containing (category, matched_text) for detected sensitive content
        """
        detected_content = []

        # Check for matches using compiled patterns
        for category, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                detected_content.append((category, match))

        # Additional context-based checks
        # Check for authority figures in sender
        if sender:
            for auth_keyword in self.authority_keywords:
                if auth_keyword.lower() in sender.lower():
                    detected_content.append((SensitivityCategory.AUTHORITY, f"from {auth_keyword}"))

        # Check for urgent/time-sensitive language
        urgent_patterns = [r'\burgen(?:cy|cies|t|cy|cies\b)', r'\basap\b', r'\bimmediate(?:ly)?\b', r'\bnow\b']
        for pattern in urgent_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_content.append((SensitivityCategory.BUSINESS_CRITICAL, "urgent language"))

        # Remove duplicates while preserving order
        seen = set()
        unique_detected = []
        for category, match in detected_content:
            key = (category, match.lower())
            if key not in seen:
                seen.add(key)
                unique_detected.append((category, match))

        return unique_detected

    def calculate_sensitivity_score(self, text: str, sender: str = "") -> float:
        """
        Calculate a sensitivity score for the given text (0.0 to 1.0).

        Args:
            text: Text to analyze
            sender: Optional sender information

        Returns:
            Sensitivity score between 0.0 and 1.0
        """
        detected = self.detect_sensitive_content(text, sender)

        if not detected:
            return 0.0

        # Weight different categories
        category_weights = {
            SensitivityCategory.MEDICAL: 1.0,
            SensitivityCategory.LEGAL: 0.9,
            SensitivityCategory.FINANCIAL: 0.8,
            SensitivityCategory.EMOTIONAL: 0.7,
            SensitivityCategory.COMPLIANCE: 0.9,
            SensitivityCategory.BUSINESS_CRITICAL: 0.6,
            SensitivityCategory.AUTHORITY: 0.5,
            SensitivityCategory.PERSONAL: 0.6
        }

        total_score = 0.0
        for category, match in detected:
            weight = category_weights.get(category, 0.5)
            total_score += weight

        # Normalize to 0-1 range (cap at 1.0)
        return min(total_score / len(detected) if detected else 0.0, 1.0)

    def should_require_approval(self, text: str, sender: str = "", threshold: float = 0.3) -> bool:
        """
        Determine if the content should require human approval based on sensitivity.

        Args:
            text: Text to analyze
            sender: Optional sender information
            threshold: Sensitivity threshold (0.0 to 1.0) above which approval is required

        Returns:
            True if approval is required, False otherwise
        """
        score = self.calculate_sensitivity_score(text, sender)
        return score >= threshold

    def get_sensitivity_breakdown(self, text: str, sender: str = "") -> Dict[SensitivityCategory, int]:
        """
        Get a breakdown of sensitivity by category.

        Args:
            text: Text to analyze
            sender: Optional sender information

        Returns:
            Dictionary mapping categories to count of matches
        """
        detected = self.detect_sensitive_content(text, sender)

        breakdown = {}
        for category, _ in detected:
            breakdown[category] = breakdown.get(category, 0) + 1

        return breakdown

    def analyze_content_risk(self, text: str, sender: str = "") -> Dict:
        """
        Perform a comprehensive risk analysis of the content.

        Args:
            text: Text to analyze
            sender: Optional sender information

        Returns:
            Dictionary with risk analysis results
        """
        detected_content = self.detect_sensitive_content(text, sender)
        sensitivity_score = self.calculate_sensitivity_score(text, sender)
        requires_approval = self.should_require_approval(text, sender)
        breakdown = self.get_sensitivity_breakdown(text, sender)

        return {
            'sensitivity_score': sensitivity_score,
            'requires_approval': requires_approval,
            'detected_categories': [category.value for category, _ in detected_content],
            'detected_terms': [term for _, term in detected_content],
            'category_breakdown': {cat.value: count for cat, count in breakdown.items()},
            'risk_level': self._determine_risk_level(sensitivity_score)
        }

    def _determine_risk_level(self, score: float) -> str:
        """
        Determine risk level based on sensitivity score.

        Args:
            score: Sensitivity score

        Returns:
            Risk level as a string
        """
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "minimal"


def get_default_detector() -> SensitiveContentDetector:
    """
    Get a default instance of the sensitive content detector.

    Returns:
        SensitiveContentDetector instance
    """
    return SensitiveContentDetector()


if __name__ == "__main__":
    # Example usage
    detector = get_default_detector()

    # Test cases
    test_cases = [
        ("Hi, I need to discuss my medical condition with you urgently", "Patient"),
        ("Can you please review the legal contract I sent?", "Client"),
        ("Hey, how are you doing?", "Friend"),
        ("We need to talk about the financial audit results", "Manager"),
        ("I'm really frustrated with the service quality", "Customer"),
        ("Meeting minutes from today's session", "Colleague")
    ]

    print("Sensitive Content Detection Results")
    print("=" * 50)

    for text, sender in test_cases:
        result = detector.analyze_content_risk(text, sender)
        print(f"\nText: {text}")
        print(f"Score: {result['sensitivity_score']:.2f}")
        print(f"Requires Approval: {result['requires_approval']}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Detected Categories: {result['detected_categories']}")
        print(f"Detected Terms: {result['detected_terms']}")
        print("-" * 30)