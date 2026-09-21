import asyncio
from typing import Dict
from dataclasses import dataclass
import re


@dataclass
class ResumeParseResult:
    text: str
    fields: Dict


class ResumeParser:
    """Simple resume parsing pipeline.

    - extract_text_from_file: supports plain txt and PDFs via placeholder
    - parse_basic_fields: regex-based extraction for name/email/phone and simple skill list

    Replace or extend with ML-based Foundry resume analysis integration as needed.
    """

    async def parse_file(self, path: str) -> ResumeParseResult:
        text = await self.extract_text_from_file(path)
        fields = self.parse_basic_fields(text)
        # simulate async work
        await asyncio.sleep(0)
        return ResumeParseResult(text=text, fields=fields)

    async def extract_text_from_file(self, path: str) -> str:
        # Minimal implementation: if file is .txt return content; otherwise attempt naive PDF text extraction placeholder
        lower = path.lower()
        if lower.endswith('.txt'):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        # For other types (pdf, docx) - placeholder behavior: read as binary and decode best-effort
        try:
            with open(path, 'rb') as f:
                raw = f.read()
            # Try decoding as utf-8 for simple files
            try:
                return raw.decode('utf-8', errors='ignore')
            except Exception:
                # Fallback: return hex-ish placeholder
                return "\n".join([line.decode('latin-1', errors='ignore') for line in raw.splitlines()[:200]])
        except Exception:
            return ""

    def parse_basic_fields(self, text: str) -> Dict:
        # Email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
        email = email_match.group(0) if email_match else None
        # Phone (very permissive)
        phone_match = re.search(r"(\+?\d[\d\-\s()]{7,}\d)", text)
        phone = phone_match.group(0) if phone_match else None
        # Name heuristic: first non-empty line
        name = None
        for line in text.splitlines():
            s = line.strip()
            if s:
                # ignore lines that contain email or phone
                if email and email in s: continue
                if phone and phone in s: continue
                name = s
                break
        # Skills heuristic: look for 'Skills' header and collect following comma-separated tokens
        skills = []
        skills_header = re.search(r"(?im)^skills[:\-]?\s*$", text)
        if skills_header:
            # capture few lines after header
            start = skills_header.end()
            snippet = text[start:start+400]
            # split by newlines and commas
            parts = re.split(r"[\n,]+", snippet)
            for p in parts:
                p = p.strip()
                if p:
                    # stop at typical next section word
                    if re.match(r"(?i)experience|education|projects|certifications", p):
                        break
                    skills.append(p)
        else:
            # fallback: find common skill keywords
            common_skills = ["python","java","c++","c#","sql","javascript","react","node","aws","docker","kubernetes"]
            lower = text.lower()
            for s in common_skills:
                if s in lower:
                    skills.append(s)
        # Education and experience placeholders
        education = []
        experience = []

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "education": education,
            "experience": experience,
        }
