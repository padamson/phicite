from typing import Annotated
import pytest
from pydantic import ValidationError, AfterValidator, BaseModel
from app.models.pydantic import is_valid_doi


class DoiUrl(BaseModel):
    doi: Annotated[str, AfterValidator(is_valid_doi)]


def test_doi_url_valid_formats():
    """Test that valid DOI formats are accepted."""
    # Standard DOI formats
    test_cases = [
        ("10.1000/journal.article.123", "10.1000/journal.article.123"),
        ("10.1234/NatureExample.2022.1234", "10.1234/natureexample.2022.1234"),
        ("10.5555/12345678", "10.5555/12345678"), 
        #("10.1002/(SICI)1096-8644(199808)106:4<483::AID-AJPA4>3.0.CO;2-K", "10.1002/(SICI)1096-8644(199808)106:4<483::AID-AJPA4>3.0.CO;2-K"),
        ("https://doi.org/10.1000/journal.article.123", "10.1000/journal.article.123"),  # With https prefix
        ("doi:10.1000/journal.article.123", "10.1000/journal.article.123")  # With doi: prefix
    ]
    
    for test_input, expected_output in test_cases:
        model = DoiUrl(doi=test_input)
        assert model.doi == expected_output

def test_doi_url_invalid_formats():
    """Test that invalid DOI formats are rejected."""
    invalid_dois = [
        "not-a-doi",
        "10.abc/invalid",  # Invalid prefix format
        "11.1234/invalid",  # First part must be 10
        "10.1234",  # Missing suffix
        "https://example.com/10.1234/test",  # Wrong URL format
        "10/1234/test"  # Wrong separator
    ]
    
    for doi in invalid_dois:
        with pytest.raises(ValidationError):
            DoiUrl(doi=doi)

def test_doi_url_normalization():
    """Test that DOIs are normalized to a standard format."""
    test_cases = [
        # (input, expected_normalized_output)
        ("https://doi.org/10.1234/example", "10.1234/example"),
        ("doi:10.1234/example", "10.1234/example"),
        ("10.1234/EXAMPLE", "10.1234/example"),  # If you normalize case
        ("10.1234/example", "10.1234/example")  # Already normalized
    ]
    
    for input_doi, expected_output in test_cases:
        doi_obj = DoiUrl(doi=input_doi)
        # Test the string representation or a normalize() method
        assert str(doi_obj.doi) == expected_output  # or doi_obj.normalize() == expected_output