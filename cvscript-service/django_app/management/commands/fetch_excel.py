from django.core.management.base import (
    BaseCommand, CommandError, ImproperlyConfigured, SystemCheckError,
    connections, handle_default_options, sys)
from django.db import models

from django_app.models import (CompanyAndSchool, CVScript, JobCategory,
                               JobCVScript, JobPosition)
import cv_fetch


def get_job_category_id(_list, name):
    result = []
    new_list = [x for x in _list if x['name']]
    if name:
        o = name
        # for o in name.split(','):
        if isinstance(o, str):
            pp = [x['id']
                    for x in new_list if o.lower() == x['name'].lower()]
            result.extend(pp)
        else:
            print(o)
            print(_list)
            print(name)
    return result


def get_job_position_id(_list, name):
    new_result = [x for x in _list if x['name']]
    result = []
    if name:
        result = [x['id']
                  for x in new_result if x['name'].lower() == name.lower()]
    if len(result) > 0:
        return result[0]

    return None


def create_job_categories_with_positions(positions, categories):
    JobCategory.objects.bulk_create([JobCategory(name=x) for x in categories])

    categories_with_ids = JobCategory.objects.values('id', 'name')
    with_id = [{
        **x, "categories":
        get_job_category_id(categories_with_ids, x['category'])
    } for x in positions]
    # bulk create job positions
    JobPosition.objects.bulk_create([
        JobPosition(
            name=x['position'],
            keywords=x['keywords'],
            software_skills=x['software_skills'],
            industry_skills=x['industry_skills']) for x in with_id
    ])

    positions_with_ids = JobPosition.objects.values('id', 'name')
    # append id of job position to exisitng dict list
    with_position_id = [{
        **x, 'id':
        get_job_position_id(positions_with_ids, x['position'])
    } for x in with_id]
    jobpositioncategory_props = [{
        'id': y['id'],
        'category_id': x
    } for y in with_position_id for x in y['categories']]
    no_dupl = set(tuple(o.values()) for o in jobpositioncategory_props)
    return [{'id': x[0], 'category_id': x[1]} for x in no_dupl]


def combine_cv_with_jobs(job_ids, cv_ids, arr, key=None):
    excel_data = [x for x in arr if x.get(key)]
    new_data = []
    ids_only = [x['name'] for x in job_ids]
    for o in excel_data:
        try:
            index = ids_only.index(o['position'])
            new_data.append({**o, 'job_id': job_ids[index]['id']})
        except ValueError:
            pass
    for i in new_data:
        ids = []
        for o in cv_ids:
            if o['text'] in i[key]:
                ids.append(o['id'])
        i['cv_ids'] = ids

    return [{'job_id': x['job_id'], 'cv_ids': x['cv_ids']} for x in new_data]


def extract_inner_list(mlist):
    return [
        dict(job_id=y['job_id'], cv_id=x) for y in mlist for x in y['cv_ids']
    ]


def remove_duplicates(result):
    return [dict(t) for t in set([tuple(d.items()) for d in result])]


def merge_list(mlist, wlist, ilist):
    result1 = extract_inner_list(mlist)
    result2 = extract_inner_list(wlist)
    result3 = extract_inner_list(ilist)
    result = result1 + result2 + result3
    return remove_duplicates(result)


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def clear_all(self):
        self.print("Deleting all the data in db")
        JobCategory.objects.all().delete()
        JobPosition.objects.all().delete()
        CVScript.objects.all().delete()
        JobCVScript.objects.all().delete()
        CompanyAndSchool.objects.all().delete()

    def print(self, data):
        self.stdout.write(self.style.SUCCESS(data))

    def populate_job_position_and_categories(self, positions, categories):
        self.print("Save both JobCategories and Job Position")
        jobpositioncategory_props = create_job_categories_with_positions(
            positions, categories)
        JobPositionCategory = JobPosition.job_categories.through
        self.print("Save Link between JobCategory and Job Position")
        JobPositionCategory.objects.bulk_create([
            JobPositionCategory(
                jobposition_id=x['id'], jobcategory_id=x['category_id'])
            for x in jobpositioncategory_props
        ])
        # delete all the job positions without a job category
        JobPosition.objects.annotate(cc=models.Count('job_categories')).filter(
            cc=0).all().delete()

    def update_categories_with_keywords_skills_and_achievements(
            self, categories):
        job_ids = JobCategory.objects.all()
        titles_only = [x.name for x in job_ids]
        for i in categories:
            self.print(
                f"Saving Default keywords, and software for {i['position']}")
            try:
                index = titles_only.index(i['position'])
                job = job_ids[index]
                for k in ['keywords', 'software_skills', 'industry_skills']:
                    setattr(job, k, i[k])
                job.save()
            except ValueError:
                pass

    def update_skill_with_shared_keywords_and_skills(self, _list):
        names_only = [x['position'] for x in _list]
        all_cvs = [i for o in _list for i in o['cv_script']]

        names_instance = JobPosition.objects.filter(name__in=names_only)
        cv_instance = JobPosition.objects.filter(name__in=all_cvs)
        for o in names_instance:
            self.print(
                f"Extending keywords, softwares and industry skill for {o.name}"
            )
            working_value = [x for x in cv_instance if x.name in all_cvs]
            keywords = o.keywords or []
            software_skills = o.software_skills or []
            industry_skills = o.industry_skills or []
            for i in working_value:
                keywords.extend(i.keywords or [])
                software_skills.extend(i.software_skills or [])
                industry_skills.extend(i.industry_skills or [])
            o.keywords = list(set(keywords))
            o.software_skills = list(set(software_skills))
            o.industry_skills = list(set(industry_skills))
            o.save()

    def merge_skills_without_cvs_to_existing_cvs_attached_to_them(
            self, positions):
        with_cvs = [x for x in positions if x.get('cv_script')]
        more_than_one_cv_script = [
            x for x in with_cvs if len(x['cv_script']) > 1
        ]
        self.update_skill_with_shared_keywords_and_skills(
            more_than_one_cv_script)

        jobs_with_cv_script_name = [
            x['position'] for x in with_cvs
            if x['position'].lower() in [o.lower() for o in x['cv_script']]
        ]
        job_ids = JobCVScript.objects.filter(
            job_position__name__in=jobs_with_cv_script_name).values(
                'script_id', 'job_position__name')

        excluded = [
            x for x in with_cvs
            if x['position'] not in jobs_with_cv_script_name
        ]
        excluded_ids = JobPosition.objects.filter(
            name__in=[x['position'] for x in excluded]).values('id', 'name')
        excluded_names_only = [x['name'].lower() for x in excluded_ids]

        for o in excluded:
            try:
                index = excluded_names_only.index(o['position'].lower())
                o['job_id'] = excluded_ids[index]['id']
            except ValueError:
                pass

        names_only = [x['job_position__name'] for x in job_ids]
        for i in excluded:
            nno = i['cv_script']
            temp = []
            for nn in nno:
                if nn in names_only:
                    temp.extend([
                        o['script_id'] for o in job_ids
                        if o['job_position__name'].lower() == nn.lower()
                    ])
            i['cv_ids'] = temp
        # import pdb; pdb.set_trace()
        rr = [
            dict(job_id=x['job_id'], cv_ids=x['cv_ids']) for x in excluded
            if x.get('cv_ids') and x.get('job_id')
        ]
        result = remove_duplicates(extract_inner_list(rr))
        self.print("Save Positions with CVScript attached to existing Jobs")
        JobCVScript.objects.bulk_create([
            JobCVScript(script_id=x['cv_id'], job_position_id=x['job_id'])
            for x in result
        ])

    def populate_cv_script_link_with_jobs_or_category(self,
                                                      positions,
                                                      model,
                                                      key_value,
                                                      kind="jobs"):
        cvs_with_ids = CVScript.objects.values('id', 'section', 'text')
        jobs_with_ids = model.objects.values('id', 'name')
        self.print(f"Get mission statment cv_ids for {kind} in database")
        m_list = combine_cv_with_jobs(jobs_with_ids, cvs_with_ids, positions,
                                      "mission_statement_cv_script")
        self.print(f"Get work archievements cv_ids for {kind} in database")

        w_list = combine_cv_with_jobs(jobs_with_ids, cvs_with_ids, positions,
                                      "work_achievement_cv_script")

        self.print(f"Get industry skills cv_ids for f{kind} in database")

        i_list = combine_cv_with_jobs(jobs_with_ids, cvs_with_ids, positions,
                                      "industry_skills_cv_script")

        self.print(
            f"Merge cv ids for different section together for each {kind} in db"
        )
        merged_list = merge_list(m_list, w_list, i_list)
        self.print(f"Save {kind} connected to cvs")
        dump = [
            JobCVScript(**{
                'script_id': x['cv_id'],
                key_value: x['job_id']
            }) for x in merged_list
        ]
        JobCVScript.objects.bulk_create(dump)

    def populate_cv_script_link_with_jobs(self, positions):
        self.populate_cv_script_tables(positions)
        self.populate_cv_script_link_with_jobs_or_category(
            positions, JobPosition, "job_position_id")

    def populate_cv_script_link_with_categories(self, categories):
        self.populate_cv_script_tables(categories)
        self.populate_cv_script_link_with_jobs_or_category(
            categories, JobCategory, "job_category_id", kind="job categories")

    def populate_cv_script_tables(self, positions):
        mission, archievement, industy = cv_fetch.dump_to_db.get_cv_scripts_arrays(
            positions)
        self.print("Saving Mission statement CVScripts")
        CVScript.objects.bulk_create(
            [CVScript(section=1, text=o) for o in mission])
        self.print("Saving Achievment CVScripts")
        CVScript.objects.bulk_create(
            [CVScript(section=2, text=o) for o in archievement])
        self.print("Saving Industry Skills CVScript")
        CVScript.objects.bulk_create(
            [CVScript(section=3, text=o) for o in industy])

    def handle(self, *args, **options):
        cv_fetch.fetch_from_drive.main(self.options)
        # cv_fetch.fetch_from_drive_async.main(self.options)
        self.clear_all()
        positions, categories = cv_fetch.dump_to_db.categories_with_skills()
        self.populate_job_position_and_categories(positions.copy(),
                                                  categories.copy())
        self.populate_cv_script_link_with_jobs(positions.copy())
        result = cv_fetch.dump_to_db.cv_script_for_categories()
        flat = [x for x in result if len(x.keys()) > 0]
        self.populate_cv_script_link_with_categories(flat)
        self.update_categories_with_keywords_skills_and_achievements(flat)
        self.merge_skills_without_cvs_to_existing_cvs_attached_to_them(
            positions)
        cv_fetch.dump_to_db.get_certifications()
        self.dump_list_of_companies_and_degrees()

    def dump_list_of_companies_and_degrees(self):
        CompanyAndSchool.objects.all().delete()
        companies = cv_fetch.dump_to_db.get_companies()
        universities, degrees = cv_fetch.dump_to_db.get_universities_and_degrees(
        )
        university_courses = cv_fetch.dump_to_db.get_university_courses()
        softwares = cv_fetch.dump_to_db.get_softwares()
        affiliation_and_certifications = cv_fetch.dump_to_db.get_certifications()
        certifications = [
            x for x in affiliation_and_certifications['certifications'] if x['name']]
        affiliations = [
            x for x in affiliation_and_certifications['affiliations'] if x['name']]
        options = {
            CompanyAndSchool.COMPANY: companies,
            CompanyAndSchool.DEGREE: degrees,
            CompanyAndSchool.SCHOOL: universities,
            CompanyAndSchool.COURSE: university_courses,
            CompanyAndSchool.SOFTWARE: softwares,
            CompanyAndSchool.CERTIFICATION: certifications,
            CompanyAndSchool.AFFILIATION: affiliations
        }
        for key, value in options.items():
            string = dict(CompanyAndSchool.CHOICES)[key]
            self.print(f"Bulk create {string}")
            CompanyAndSchool.bulk_create_action(key, value)

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        self.options = parser.parse_args(argv[2:])
        cmd_options = vars(self.options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop('args', ())
        handle_default_options(self.options)
        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            if self.options.traceback or not isinstance(e, CommandError):
                raise

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(1)
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                # Ignore if connections aren't setup at this point (e.g. no
                # configured settings).
                pass

    def add_arguments(self, parser):
        parser.add_argument(
            '--auth_host_name',
            default='localhost',
            help='Hostname when running a local web server.')
        parser.add_argument(
            '--noauth_local_webserver',
            action='store_true',
            default=False,
            help='Do not run a local web server.')
        parser.add_argument(
            '--auth_host_port',
            default=[8080, 8090],
            type=int,
            nargs='*',
            help='Port web server should listen on.')
        parser.add_argument(
            '--logging_level',
            default='ERROR',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set the logging level of detail.')

        self.parser = parser
