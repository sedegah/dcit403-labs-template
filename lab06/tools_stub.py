"""Stub tools for the Asempa Community Clinic assistant (Lab 6)."""

from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "lab05" / "docs"


def get_opening_hours(service="opd", day=""):
    return f"[stub] opening hours for {service} on {day or 'all days'}"


def get_service_info(service):
    return f"[stub] service info for {service}"


def get_test_prep(test_name):
    return f"[stub] preparation for {test_name}"


def get_payment_info():
    return "[stub] NHIS and payment info"


def detect_emergency(text):
    keywords = ("chest pain", "difficulty breathing", "severe bleeding",
                "seizure", "unconscious", "serious injury")
    return any(keyword in text.lower() for keyword in keywords)


if __name__ == "__main__":
    print(get_opening_hours("opd", "Sunday"))
    print(detect_emergency("I have chest pain"))
    print(detect_emergency("What are your hours?"))
