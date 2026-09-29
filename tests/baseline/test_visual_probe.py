import importlib.util
import unittest

from tools.baseline.visual_probe import compare_images, review_html


@unittest.skipUnless(importlib.util.find_spec('PIL'), 'Optional local image qualification dependency')
class VisualMetricsTests(unittest.TestCase):
    def image(self):
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (100, 100), 'white')
        ImageDraw.Draw(image).rectangle((20, 20, 40, 40), fill='black')
        return image

    def test_identical_images_have_zero_error_but_still_need_review(self):
        image = self.image()
        result = compare_images(image, image)
        self.assertEqual(result['mean_absolute_channel_error'], 0)
        self.assertEqual(result['unmatched_pdf_ink_fraction'], 0)
        self.assertEqual(result['status'], 'measured_review_pending')

    def test_missing_content_is_detected(self):
        from PIL import Image
        result = compare_images(self.image(), Image.new('RGB', (100, 100), 'white'))
        self.assertEqual(result['unmatched_pdf_ink_fraction'], 1)

    def test_size_mismatch_is_not_silently_rescaled(self):
        from PIL import Image
        result = compare_images(self.image(), Image.new('RGB', (101, 100), 'white'))
        self.assertEqual(result['status'], 'size_mismatch')


class PrivateReviewTests(unittest.TestCase):
    def test_review_is_static_and_escapes_status(self):
        output = review_html([{'page': 1, 'status': '<script>unsafe</script>'}])
        self.assertNotIn('<script>', output)
        self.assertIn('pdf-page-1.png', output)
        self.assertIn("default-src 'none'", output)


if __name__ == '__main__':
    unittest.main()
