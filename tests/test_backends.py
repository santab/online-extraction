import pytest

pytest.importorskip("deepagents")

from extraction_agent.backends import SKILLS_ROOT, skills_deny_write_permission, to_virtual_skill_path


def test_to_virtual_skill_path_relative_to_skills_root():
    assert to_virtual_skill_path(SKILLS_ROOT / "triage" / "v1") == "/skills/triage/v1/"


def test_to_virtual_skill_path_rejects_none():
    with pytest.raises(ValueError, match="no skill path configured"):
        to_virtual_skill_path(None)


def test_skills_deny_write_permission_denies_writes_under_skills():
    rule = skills_deny_write_permission()
    assert rule.mode == "deny"
    assert rule.operations == ["write"]
    assert rule.paths == ["/skills/**"]


@pytest.mark.parametrize("agent", ["triage", "pdf", "excel", "image", "docx", "merge"])
def test_skill_files_are_discoverable_by_deepagents(agent):
    """Regression check for the Agent Skills convention deepagents actually
    enforces: SKILL.md's frontmatter `name` must match the directory
    directly containing it, and that directory must be a child of the vN
    source passed to `skills=[...]` — not the vN dir itself."""
    from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
    from deepagents.middleware.skills import _list_skills_with_errors

    composite = CompositeBackend(
        default=StateBackend(),
        routes={"/skills/": FilesystemBackend(root_dir=str(SKILLS_ROOT), virtual_mode=True)},
    )
    source = to_virtual_skill_path(SKILLS_ROOT / agent / "v1")
    skills, error = _list_skills_with_errors(composite, source)

    assert error is None
    assert [s["name"] for s in skills] == [agent]
