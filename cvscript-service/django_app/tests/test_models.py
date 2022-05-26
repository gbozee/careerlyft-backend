from django.test import TestCase
from django_app import models
from unittest import mock


class CVGenerationTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.job_category = models.JobCategory.objects.create(
            name="Engineering", keywords=['Hardware', "Software", "Full Stack"], software_skills=['Django', 'React', "Vue"],
            industry_skills=['Software Design', "Analytics Development"])
        self.job_position = models.JobPosition.objects.create(
            name="Systems Engineering",
            keywords=['Hardware', "Software", "Full Stack"], software_skills=['Django', 'React', "Vue"],
            industry_skills=['Software Design', "Analytics Development"])
        self.job_position.job_categories.add(self.job_category)


    @mock.patch('cv_utils.get_choices')
    @mock.patch("cv_utils.get_rand")
    def test_mission_statement_for_job_category(self, mock_rand, mock_rand_choice):
        mock_rand.return_value = 5
        mock_rand_choice.side_effect = [
            ["Django", "React"],
            ['Hardware', "Software", "Full Stack"],
            ['Software Design', "Analytics Development"]]
        self.cv_script = models.CVScript.objects.create(
            section=1,
            text=("Organized, responsible, and driven "
                  "[Human Resource Manager] with (15)+ years of experience "
                  "in fast-moving environments. Track record of leading human "
                  "resources teams to {Microsoft Office} business solutions that are on "
                  "<Product Design>, <Fabrication>"
                  "time and to budget. Ability to overhaul human resources "
                  "procedures and processes to {Quick books} more cost-efficient "
                  "solutions to businesses. *mechatronics#, *3d modelling# and *chassis design#"))
        self.job_cv_script = models.JobCVScript.objects.create(
            script=self.cv_script, job_category=self.job_category
        )
        self.assertEqual(self.job_cv_script.script_content_using_default(self.job_position.name),
                         ("Organized, responsible, and driven "
                          f"{self.job_position.name} with 5+ years of experience "
                          "in fast-moving environments. Track record of leading human "
                          "resources teams to Django business solutions that are on "
                          "Software Design, Analytics Development"
                          "time and to budget. Ability to overhaul human resources "
                          "procedures and processes to React more cost-efficient "
                          "solutions to businesses. Hardware, Software and Full Stack"))
