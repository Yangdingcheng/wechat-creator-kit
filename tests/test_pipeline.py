import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from creator_kit import parse_sections, template_draft, slug

def test_parse_sections():
    secs = parse_sections("## 导语\n你好\n## 发生了什么\n事实")
    assert [s[0] for s in secs] == ["导语", "发生了什么"]

def test_template_draft_uses_only_given_facts():
    d = template_draft({"title": "T", "facts": ["只有这条事实"]})
    assert "只有这条事实" in d and "导语" in d

def test_slug_stable():
    assert slug(0, "标题") == slug(0, "标题")

if __name__ == "__main__":
    test_parse_sections(); test_template_draft_uses_only_given_facts(); test_slug_stable(); print("ok")
