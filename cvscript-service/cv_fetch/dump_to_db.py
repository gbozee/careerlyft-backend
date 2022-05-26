import os
import itertools
from .constants import BASE_DIR
import openpyxl

CV_DIRECTORY = os.path.join(BASE_DIR, "cv_files")


def get_value_from_index(arr, index):
    try:
        value = arr[index].split(",")
    except IndexError:
        value = None
    except AttributeError:
        value = None
    return value


def terminate_when_empty(column):
    for i in column:
        if not i.value:
            return
        yield i.value


def return_column_summary(arr):
    title = arr[0]
    return {"title": arr[0], "data": arr[1:]}


def parse_school_or_degree(sheet):
    result = parce_excel_sheet(sheet, True, True)
    if sheet.title == "University":
        output = list(set(result[1]["data"]))
    else:
        output = list(set(result[0]["data"]))
    return output


def parse_certifications(sheet):
    result = parce_excel_sheet(sheet, True, True)
    # if sheet.title == "Certifications":
    output = [
        {"name": value, "job_category": result[1]["data"][i]}
        for i, value in enumerate(result[0]["data"])
    ]
    # else:
    #     output =
    return output


def parse_job_positions(sheet):
    result = parce_excel_sheet(sheet, True, True)
    # import pdb
    # pdb.set_trace()
    if sheet.title == "JobPosition":
        output = [
            {
                "position": value,
                "category": result[1]["data"][i],
                "cv_script": get_value_from_index(result[2]["data"], i),
            }
            for i, value in enumerate(result[0]["data"])
        ]
    else:
        output = list(set(result[0]["data"]))
    return output


def get_skil_only(arr):
    result = []
    for ii in arr:
        splitted = ii.split(":")[0].strip()
        result.append(splitted)
    return result


def get_array_val(gen):
    result = {}
    for o in gen:
        if o["title"].lower() in ["keywords", "software skills"]:
            result[o["title"].lower()] = o["data"]
        if o["title"].lower() == "industry skills":
            result[o["title"].lower()] = get_skil_only(o["data"])
        if o["title"].lower() in [
            "work achievement",
            "industry skills",
            "cover letter scripts",
        ]:
            result[f"{o['title'].lower()}_cv_script"] = o["data"]
        if o["title"].lower() in ["mission statement", "misson statement"]:
            result["mission statement_cv_script"] = o["data"]
    return result


def flatten(key, _list):
    array = [x for x in _list if x.get(key)]
    return [o for p in [x[key] for x in array] for o in p]


def get_cv_scripts_arrays(positions):
    """Get the cv scripts for the different sections removing all duplicates"""
    merged_mission_statments = flatten("mission_statement_cv_script", positions)
    merged_work_achievements = flatten("work_achievement_cv_script", positions)
    merged_industry_skills = flatten("industry_skills_cv_script", positions)
    return (
        set(merged_mission_statments),
        set(merged_work_achievements),
        set(merged_industry_skills),
    )


def extract_keyword_data(skill):
    result = {}
    array_dict = get_array_val(skill["data"])
    if array_dict.get("keywords"):
        result.update(
            {
                "position": skill["title"],
                "keywords": array_dict["keywords"],
                "software_skills": array_dict["software skills"],
                "industry_skills": array_dict["industry skills"],
                "mission_statement_cv_script": array_dict.get(
                    "mission statement_cv_script"
                ),
                "work_achievement_cv_script": array_dict.get(
                    "work achievement_cv_script"
                ),
                "industry_skills_cv_script": array_dict.get(
                    "industry skills_cv_script"
                ),
                "cover_letter_cv_script": array_dict.get(
                    "cover letter scripts_cv_script"
                ),
            }
        )
    return result


def populate_keywords_and_skills():
    result = main()
    positions_with_list = []
    for category in result:
        for skill in category["data"]:
            dump = extract_keyword_data(skill)
            positions_with_list.append(dump)
    return positions_with_list


def cv_script_for_categories():
    file_name = "Default.xlsx"
    print("Fetching cv script for categories")
    fetched_files = parse_excel_file(file_name)
    return [extract_keyword_data(k) for k in fetched_files]


def get_universities_and_degrees():
    file_name = "List of University and Degrees.xlsx"
    print("Fetching the list of universities and possible degrees")
    return [x["data"] for x in parse_excel_file(file_name, parse_school_or_degree)]


def get_university_courses():
    file_name = "List of University Courses.xlsx"
    print("Fetching the list of universities")
    return parse_excel_file(file_name, parse_school_or_degree)[0]["data"]


def get_companies():
    file_name = "List of Companies.xlsx"
    print("Fetching the list of companies")
    return parse_excel_file(file_name, parse_school_or_degree)[0]["data"]


def get_softwares():
    file_name = "List of Generic Softwares.xlsx"
    print("Fetching list of generic softwares")
    return parse_excel_file(file_name, parse_school_or_degree)[0]["data"]


def get_certifications():
    file_name = "List of Certifications and Affiliations.xlsx"
    print("Fetching list of certifications")
    result = parse_excel_file(file_name, parse_certifications)
    return {"certifications": result[0]["data"], "affiliations": result[1]["data"]}


def categories_with_skills():
    file_name = "List of Jobs Positions.xlsx"
    print("Fetching skills with actual cvscript content")
    skills_with_keywords = [
        x for x in populate_keywords_and_skills() if len(x.keys()) > 0
    ]
    positions = [x["position"] for x in skills_with_keywords]
    print("Fetching the list of skills and categories")
    actual_skills, category = [
        x["data"] for x in parse_excel_file(file_name, parse_job_positions)
    ]
    final_skills = []
    print("Merging skills with cvscript with list of all skills")
    for ss in actual_skills:
        found = {"keywords": [], "software_skills": [], "industry_skills": []}
        if ss["position"] in positions:
            found = skills_with_keywords[positions.index(ss["position"])]

        final_skills.append({**ss, **found})
    job_positions = [x for x in final_skills if x["position"]]
    job_categories = [x for x in category if x]
    print("Populate cvscricript for positions that are shared")
    new_final = []
    without_keywords = [x for x in job_positions if x["cv_script"]]
    without_keywords = [
        x["position"] for x in without_keywords if len(x["software_skills"]) == 0
    ]
    for ss in job_positions:
        if ss["position"] in without_keywords:
            if ss["cv_script"]:
                if set(ss["cv_script"]).intersection(set(positions)):
                    found = merge_found_cvscript(
                        ss["cv_script"], skills_with_keywords, positions
                    )
                    # found = skills_with_keywords[positions.index(ss["cv_script"][0])]
                    # print(f"Found details for {ss['position']}")
                    found["position"] = ss["position"]
                    found["cv_script"] = ss["cv_script"]
                    found["category"] = ss["category"]
                    new_final.append(found)
                else:
                    new_final.append(ss)
            else:
                new_final.append(ss)
        else:
            new_final.append(ss)

    return new_final, job_categories


def merge_found_cvscript(data, skills_with_keywords, positions):
    result = {"keywords": [], "software_skills": [], "industry_skills": []}

    for ss in data:
        if ss in positions:
            found = skills_with_keywords[positions.index(ss)]
            for key, value in found.items():
                if isinstance(value, list):
                    if key in result.keys():
                        result[key] = list(set(result.get(key)).union(set(value)))
                else:
                    result[key] = value
    return result


def groupings(data):
    groups = []
    non_groups = []
    uniquekeys = []
    keyfunc = lambda x: x["cv_script"]
    data = sorted(data, key=keyfunc)
    for k, g in itertools.groupby(data, keyfunc):
        item = list(g)
        grouped = [
            x for x in item if x["software_skills"] and len(x["software_skills"]) > 0
        ]
        not_grouped = [
            x for x in item if x["software_skills"] and len(x["software_skills"]) == 0
        ]
        if len(grouped) > 0:
            groups.append(item)  # Store group iterator as a list
        if len(not_grouped) > 0:
            non_groups.append(not_grouped)
        uniquekeys.append(k)
    return groups, non_groups, uniquekeys


def read_directory(files_path):
    result = [
        {"title": file_name.split(".xlsx")[0], "data": parse_excel_file(file_name)}
        for file_name in files_path
    ]
    return result


def main():
    files_path = [x for x in os.listdir(CV_DIRECTORY)]
    files_to_exclude = [
        "List of Generic Softwares",
        "Default",
        "Transportation and Logistics",
        "Therapy",
        # "Real Estate",
        "Military & Security",
        "Manufacturing",
        "Maintenance & Repair",
        "Hospitality & Food Service",
        "List of Companies & Degree",
        "List of Companies",
        "List of Generic Softwares",
        "List of University and Degrees",
        "List of University Courses",
        "List of Certifications and Affiliations",
        "Personal Care and Home Services",
        "Aviation",
        "List of Jobs Positions",
    ]
    working_files = [
        x for x in files_path if x.split(".xlsx")[0] not in files_to_exclude
    ]
    result = read_directory(working_files)
    return result


def parce_excel_sheet(sheet, gen=False, use_length_of_first_row=False):
    position_name = sheet.title
    strings = "abcdefghijklmnopqrstuvwxyz".upper()
    rows = [y for y in terminate_when_empty(next(sheet.rows))]
    if use_length_of_first_row:
        result = (
            return_column_summary([x.value for x in sheet[strings[index]]])
            for index, value in enumerate(rows)
        )  # result =
    else:
        result = (
            return_column_summary(
                [x for x in terminate_when_empty(sheet[strings[index]])]
            )
            for index, value in enumerate(rows)
        )
    if gen:
        result = list(result)
    return result
    # result = [terminate_when_empty(sheet[strings[i]]) for i,v in enumerate(rows)]
    # import pdb; pdb.set_trace()


def parse_excel_file(file_name, func=parce_excel_sheet):
    wb = openpyxl.load_workbook(os.path.join(CV_DIRECTORY, file_name))
    print(f"Opening {file_name}.xlsx")
    worksheets = [{"title": x.title, "data": func(x)} for x in wb.worksheets]
    # worksheets = (
    #     {'title': x.title, 'data': func(x)} for x in wb.worksheets
    # )
    return worksheets


# if __name__ == '__main__':
#     main()
