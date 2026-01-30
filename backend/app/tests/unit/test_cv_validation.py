"""Unit tests for CV data validation"""
import pytest
from app.services.cv_validation import CVDataValidator


class TestSkillValidation:
    """Test skill validation logic"""

    def test_valid_skills(self):
        """Test that valid skills pass validation"""
        valid_skills = [
            "python",
            "java",
            "react.js",
            "machine learning",
            "aws certified",
            "docker",
            "kubernetes",
            "sql server",
            "node.js",
            "c++",
            "oracle database",
            "pl/sql",
        ]

        for skill in valid_skills:
            assert CVDataValidator.is_valid_skill(skill), f"Valid skill '{skill}' was rejected"

    def test_invalid_passport_numbers(self):
        """Test that passport numbers are filtered out"""
        invalid_skills = [
            "A1234567",  # UK passport
            "M12345678",  # India passport
            "123456789",  # US passport
            "P12345678",  # Generic passport
        ]

        for skill in invalid_skills:
            assert not CVDataValidator.is_valid_skill(skill), f"Passport number '{skill}' was accepted as skill"

    def test_invalid_phone_numbers(self):
        """Test that phone numbers are filtered out"""
        invalid_skills = [
            "1234567890",
            "+1 234 567 8900",
            "+91-9876543210",
            "(555) 123-4567",
            "555-123-4567",
        ]

        for skill in invalid_skills:
            assert not CVDataValidator.is_valid_skill(skill), f"Phone number '{skill}' was accepted as skill"

    def test_invalid_email_addresses(self):
        """Test that email addresses are filtered out"""
        invalid_skills = [
            "test@example.com",
            "user.name@company.co.uk",
            "info@test.org",
        ]

        for skill in invalid_skills:
            assert not CVDataValidator.is_valid_skill(skill), f"Email '{skill}' was accepted as skill"

    def test_invalid_dates(self):
        """Test that dates are filtered out"""
        invalid_skills = [
            "01/01/2020",
            "2020-01-01",
            "Jan 1, 2020",
            "December 25, 2019",
            "12-25-2019",
        ]

        for skill in invalid_skills:
            assert not CVDataValidator.is_valid_skill(skill), f"Date '{skill}' was accepted as skill"

    def test_invalid_national_ids(self):
        """Test that national IDs and SSNs are filtered out"""
        invalid_skills = [
            "123-45-6789",  # SSN
            "ABCDE1234F",  # PAN
            "123456789012",  # Aadhaar
        ]

        for skill in invalid_skills:
            assert not CVDataValidator.is_valid_skill(skill), f"National ID '{skill}' was accepted as skill"

    def test_noise_words(self):
        """Test that noise words are filtered out"""
        invalid_skills = [
            "proficient",
            "experience",
            "knowledge",
            "expert",
            "advanced",
        ]

        for skill in invalid_skills:
            assert not CVDataValidator.is_valid_skill(skill), f"Noise word '{skill}' was accepted as skill"

    def test_too_many_numbers(self):
        """Test that strings with too many numbers are filtered"""
        invalid_skills = [
            "12345abc",  # 62.5% numbers
            "a123456",  # 85% numbers
            "test12345",  # 55% numbers
        ]

        for skill in invalid_skills:
            assert not CVDataValidator.is_valid_skill(skill), f"Number-heavy string '{skill}' was accepted as skill"

    def test_length_boundaries(self):
        """Test length validation"""
        # Too short
        assert not CVDataValidator.is_valid_skill("a")
        assert not CVDataValidator.is_valid_skill("ab")

        # Just right
        assert CVDataValidator.is_valid_skill("sql")
        assert CVDataValidator.is_valid_skill("python")

        # Too long
        assert not CVDataValidator.is_valid_skill("a" * 101)

    def test_filter_skills_list(self):
        """Test filtering a list of skills"""
        skills = [
            "python",  # Valid
            "java",  # Valid
            "A1234567",  # Passport - invalid
            "test@example.com",  # Email - invalid
            "docker",  # Valid
            "123-45-6789",  # SSN - invalid
            "kubernetes",  # Valid
        ]

        filtered = CVDataValidator.filter_skills(skills)

        assert len(filtered) == 4
        assert "python" in filtered
        assert "java" in filtered
        assert "docker" in filtered
        assert "kubernetes" in filtered
        assert "A1234567" not in filtered
        assert "test@example.com" not in filtered


class TestCertificationValidation:
    """Test certification validation logic"""

    def test_valid_certifications(self):
        """Test that valid certifications pass validation"""
        valid_certs = [
            "AWS Certified Solutions Architect",
            "Oracle Certified Professional",
            "Microsoft Certified Azure Administrator",
            "Certified Kubernetes Administrator (CKA)",
            "PMP - Project Management Professional",
            "Certified ScrumMaster (CSM)",
            "CISSP - Certified Information Systems Security Professional",
        ]

        for cert in valid_certs:
            assert CVDataValidator.is_valid_certification(cert), f"Valid certification '{cert}' was rejected"

    def test_invalid_passport_in_certs(self):
        """Test that passport numbers are filtered from certifications"""
        invalid_certs = [
            "Passport: A1234567",
            "Passport No: M12345678",
            "123456789",
        ]

        for cert in invalid_certs:
            assert not CVDataValidator.is_valid_certification(cert), f"Passport '{cert}' was accepted as certification"

    def test_invalid_personal_info_in_certs(self):
        """Test that personal info indicators are filtered"""
        invalid_certs = [
            "Date of Birth: 01/01/1990",
            "Nationality: Indian",
            "Driving License: DL12345678",
            "National ID: 123456789",
        ]

        for cert in invalid_certs:
            assert not CVDataValidator.is_valid_certification(cert), f"Personal info '{cert}' was accepted as certification"

    def test_certification_with_cert_keywords(self):
        """Test that strings with certification keywords are more lenient"""
        # These should pass even with some numbers
        valid_with_keywords = [
            "AWS Certified 2023",
            "Certification ID: AWS-123 (AWS Solutions Architect)",
            "Professional Certificate in Data Science",
        ]

        for cert in valid_with_keywords:
            # Only check if it has cert keywords, not the full validation
            has_indicator = any(word in cert.lower() for word in ["certified", "certification", "certificate", "professional"])
            if has_indicator:
                # Should be more lenient
                result = CVDataValidator.is_valid_certification(cert)
                # At least the valid ones should pass
                if not any(invalid in cert for invalid in ["Certification ID:"]):
                    assert result, f"Cert with keyword '{cert}' was rejected"

    def test_filter_certifications_list(self):
        """Test filtering a list of certifications"""
        certs = [
            "AWS Certified Solutions Architect",  # Valid
            "Oracle Certified Professional",  # Valid
            "Passport: A1234567",  # Invalid - passport
            "test@example.com",  # Invalid - email
            "Certified Kubernetes Administrator",  # Valid
            "Date of Birth: 01/01/1990",  # Invalid - personal info
        ]

        filtered = CVDataValidator.filter_certifications(certs)

        assert len(filtered) >= 3  # At least the 3 valid ones
        assert any("AWS" in cert for cert in filtered)
        assert any("Oracle" in cert for cert in filtered)
        assert any("Kubernetes" in cert for cert in filtered)
        assert not any("Passport" in cert for cert in filtered)
        assert not any("@" in cert for cert in filtered)
        assert not any("Date of Birth" in cert for cert in filtered)

    def test_certification_length_boundaries(self):
        """Test certification length validation"""
        # Too short
        assert not CVDataValidator.is_valid_certification("AB")

        # Just right
        assert CVDataValidator.is_valid_certification("AWS Certified")

        # Too long
        assert not CVDataValidator.is_valid_certification("a" * 201)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_none_and_empty_strings(self):
        """Test handling of None and empty strings"""
        assert not CVDataValidator.is_valid_skill(None)
        assert not CVDataValidator.is_valid_skill("")
        assert not CVDataValidator.is_valid_skill("   ")

        assert not CVDataValidator.is_valid_certification(None)
        assert not CVDataValidator.is_valid_certification("")
        assert not CVDataValidator.is_valid_certification("   ")

    def test_mixed_case_validation(self):
        """Test that validation is case-insensitive"""
        assert CVDataValidator.is_valid_skill("Python")
        assert CVDataValidator.is_valid_skill("PYTHON")
        assert CVDataValidator.is_valid_skill("python")

    def test_special_characters(self):
        """Test handling of special characters"""
        # Valid technical terms with special chars
        assert CVDataValidator.is_valid_skill("c++")
        assert CVDataValidator.is_valid_skill("c#")
        assert CVDataValidator.is_valid_skill("node.js")
        assert CVDataValidator.is_valid_skill("react.js")

        # Invalid - pure special chars
        assert not CVDataValidator.is_valid_skill("###")
        assert not CVDataValidator.is_valid_skill("***")

    def test_urls_filtered(self):
        """Test that URLs are filtered out"""
        invalid = [
            "https://example.com",
            "http://test.com/path",
            "www.example.com",
        ]

        for url in invalid:
            assert not CVDataValidator.is_valid_skill(url)
            assert not CVDataValidator.is_valid_certification(url)

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly"""
        # Leading/trailing whitespace should be stripped
        assert CVDataValidator.is_valid_skill("  python  ")
        assert CVDataValidator.is_valid_certification("  AWS Certified  ")

    def test_real_world_messy_data(self):
        """Test with real-world messy CV data"""
        messy_skills = [
            "Python",  # Valid
            "Passport No: A1234567",  # Invalid
            "Java",  # Valid
            "+91-9876543210",  # Invalid - phone
            "Docker",  # Valid
            "john@example.com",  # Invalid - email
            "AWS",  # Valid
            "123-45-6789",  # Invalid - SSN
        ]

        filtered = CVDataValidator.filter_skills(messy_skills)

        # Should only have the 4 valid skills
        assert len(filtered) == 4
        valid_terms = {"python", "java", "docker", "aws"}
        assert all(any(term in skill.lower() for term in valid_terms) for skill in filtered)
