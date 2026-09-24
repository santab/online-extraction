from extraction_agent.modalities.pdf.parser import _needs_visual_review, _page_embedded_image_count


class _FakePage:
    def __init__(self, images):
        self.images = images


def test_embedded_image_count_reads_images_attr():
    assert _page_embedded_image_count(_FakePage(["a", "b"])) == 2


def test_embedded_image_count_defaults_to_zero_without_images_attr():
    assert _page_embedded_image_count(object()) == 0


def test_page_with_text_and_no_images_does_not_need_visual_review():
    assert _needs_visual_review(has_text=True, embedded_image_count=0) is False


def test_scanned_page_with_no_text_needs_visual_review():
    assert _needs_visual_review(has_text=False, embedded_image_count=0) is True


def test_mixed_layout_page_with_text_and_embedded_image_needs_visual_review():
    assert _needs_visual_review(has_text=True, embedded_image_count=1) is True
