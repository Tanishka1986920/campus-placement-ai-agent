import asyncio
from app.core.resume_parser import ResumeParser


def test_parse_basic_text_tmp(tmp_path):
    p = tmp_path / "test.txt"
    content = "John Doe\njohn.doe@example.com\n+1 (555) 123-4567\nSkills: Python, SQL, Docker\n"
    p.write_text(content, encoding='utf-8')

    parser = ResumeParser()
    result = asyncio.get_event_loop().run_until_complete(parser.parse_file(str(p)))

    assert "John Doe" in result.text
    assert result.fields.get("email") == "john.doe@example.com"
    assert result.fields.get("phone") is not None
    assert "python" in [s.lower() for s in result.fields.get("skills", [])]
