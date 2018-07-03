import posixpath
import tempfile
import binascii
import shutil
import codecs
import csv
import os

from django.core.files.base import File
from django.contrib.gis.geos import Point
from django.db.models.signals import post_save
from django.test import TestCase
from django.conf import settings

from model_mommy.mommy import make, prepare

from oregoninvasiveshotline.tests.base import ServiceTestCaseMixin
from oregoninvasiveshotline.comments.models import Comment
from oregoninvasiveshotline.images.models import Image
from oregoninvasiveshotline.species.models import Category, Species
from oregoninvasiveshotline.reports.models import Report, receiver__generate_icon
from oregoninvasiveshotline.reports.views import _export

ORIGIN = Point(0, 0)
TEST_IMAGE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'assets', 'fsm.png')
)


class SuppressPostSaveMixin:

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(receiver__generate_icon, sender=Report)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        post_save.connect(receiver__generate_icon, sender=Report)


class ReportTest(SuppressPostSaveMixin, ServiceTestCaseMixin, TestCase):

    def setUp(self):
        self.report = Report()

    def tearDown(self):
        if self.report.pk is not None:
            self.report.delete()

    def test_species(self):
        reported_species = make(Species)
        actual_species = make(Species)

        self.assertEqual(make(Report, actual_species=None, reported_species=reported_species, point=ORIGIN).species, reported_species)
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=reported_species, point=ORIGIN).species, actual_species)
        self.assertEqual(make(Report, actual_species=None, reported_species=None, point=ORIGIN).species, None)

    def test_category(self):
        reported_species = make(Species)
        actual_species = make(Species)

        self.assertEqual(
            make(Report, actual_species=None, reported_species=None, reported_category=reported_species.category, point=ORIGIN).category,
            reported_species.category
        )
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=reported_species, point=ORIGIN).category, actual_species.category)

    def test_is_misidentified(self):
        reported_species = make(Species)
        actual_species = make(Species)

        # if they didn't identify the species, then it can't be misidentified
        self.assertEqual(make(Report, actual_species=None, reported_species=None, point=ORIGIN).is_misidentified, False)
        # if the reported and actual species are the same, it's not misidentified
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=actual_species, point=ORIGIN).is_misidentified, False)
        # if the species differ, then it is misidentified
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=reported_species, point=ORIGIN).is_misidentified, True)

    def test_title(self):
        report = make(Report, actual_species=None, reported_species=None, reported_category=make(Category, name='Foo'), point=ORIGIN)
        self.assertEqual(report.title, 'Foo')
        report = make(Report, actual_species=None, reported_species=make(Species, name='Bar', scientific_name='Foo'), point=ORIGIN)
        self.assertEqual(report.title, 'Bar (Foo)')

    def test_image_url(self):
        report = make(Report, point=ORIGIN)

        # A report with only a private image shouldn't have an image URL
        make(Image, report=report, visibility=Image.PRIVATE)
        expected_url = None
        self.assertEqual(report.image_url, expected_url)

        # A report with a public image should have an image URL
        path = os.path.join(settings.MEDIA_ROOT, 'test.png')
        shutil.copyfile(TEST_IMAGE_PATH, path)
        image = make(Image, report=report, image=File(open(path, 'rb')), visibility=Image.PUBLIC)
        file_name = '{image.pk}.png'.format(image=image)
        expected_url = posixpath.join(settings.MEDIA_URL, 'generated_thumbnails', file_name)
        self.assertEqual(report.image_url, expected_url)

        path = os.path.join(settings.MEDIA_ROOT, 'generated_thumbnails', file_name)
        self.assertTrue(os.path.exists(path))

    def test_image_url_from_comment(self):
        report = make(Report, point=ORIGIN)

        make(Image, comment=make(Comment, report=report), visibility=Image.PRIVATE, _quantity=2)
        expected_url = None
        self.assertEqual(report.image_url, expected_url)

        path = os.path.join(settings.MEDIA_ROOT, 'test.png')
        shutil.copyfile(TEST_IMAGE_PATH, path)
        image = make(Image, report=report, image=File(open(path, 'rb')), visibility=Image.PUBLIC)
        file_name = '{image.pk}.png'.format(image=image)
        expected_url = posixpath.join(settings.MEDIA_URL, 'generated_thumbnails', file_name)
        self.assertEqual(report.image_url, expected_url)

        path = os.path.join(settings.MEDIA_ROOT, 'generated_thumbnails', file_name)
        self.assertTrue(os.path.exists(path))


class TestReportIconGeneration(TestCase):

    def _make_category_icon(self):
        content = binascii.unhexlify(
            # Turtle icon encoded as hex
            b'89504e470d0a1a0a0000000d494844520000002000000025080600000023b7eb47000000d249444154588'
            b'5ed95410ec42008453f93b9191cbb9ecd59991082561cba980c6fd3a6c6f004a1405114455114bf063377'
            b'fdfc96d7c9a6de7b9a0445373073bfae0b0020220080d61ae975bb47afa708008095d08c350020a2658cb'
            b'08027a1453cb14733e0e1952645203b3870d005abe083dde04702d9bcbd8fb69522274a1168add1183622'
            b'9236f53cdc123073b76d65dfb398a676e7c65ba21db014884a9c04bf15d0121a4f6877f28505acc86afc5'
            b'a911d19b70b66ec9422f223028219589d74466a066cf08c0115be038327a7e37ff101afa37d185ce02898'
            b'0000000049454e44ae426082'
        )
        icon_dir = os.path.join(settings.MEDIA_ROOT, 'icons')
        fd, name = tempfile.mkstemp(dir=icon_dir, suffix='.png')
        os.write(fd, content)
        os.close(fd)
        icon_file = File(open(name, 'rb'), name)
        return icon_file

    def test_generate_icon_manually(self):
        report = prepare(
            Report,
            point=ORIGIN,
            actual_species__severity__color='#ff8800',
            actual_species__category__icon=self._make_category_icon(),
        )
        self.assertFalse(os.path.exists(report.icon_path))
        report.generate_icon()
        self.assertTrue(os.path.exists(report.icon_path))
        # Clean up
        os.unlink(report.icon_path)

    def test_icon_is_generated_on_post_save_for_existing_reports(self):
        report = make(
            Report,
            point=ORIGIN,
            actual_species__severity__color='#ff8800',
            actual_species__category__icon=self._make_category_icon(),
        )
        # The report was saved with a PK by make(), so it should have an
        # icon.
        self.assertTrue(os.path.exists(report.icon_path))
        # Remove the icon and verify that its icon is re-created the
        # next time the report is saved.
        os.unlink(report.icon_path)
        self.assertFalse(os.path.exists(report.icon_path))
        report.save()
        self.assertTrue(os.path.exists(report.icon_path))
        # Clean up
        os.unlink(report.icon_path)


class ExportTest(TestCase):

    def test_csv(self):
        reports = make(Report, _quantity=3, point=ORIGIN)
        response = _export(reports, format="csv")
        reader = csv.DictReader(codecs.iterdecode(response, "utf8"))
        rows = list(reader)
        self.assertEqual(3, len(rows))
        self.assertEqual(rows[2]['Description'], reports[2].description)

    def test_kml(self):
        reports = make(Report, _quantity=3, point=ORIGIN)
        response = _export(reports, format="kml")
        # this is harder to test without trying to parse the XML
        self.assertIn(reports[0].description, response.content.decode())
