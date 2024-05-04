import os
import traceback
import requests
import json
import sys


api_token = os.getenv("API_TOKEN")
repository = os.getenv("GITHUB_REPOSITORY") or os.getenv("CI_REPOSITORY_URL")
job_name = "Update Google Font"

local_file_path = "lawnchair/assets/google_fonts.json"


def get_google_fonts(api_token: str) -> json:
    """GET font data from Google Fonts API"""

    url = f"https://www.googleapis.com/webfonts/v1/webfonts?key={api_token}"
    content = requests.get(url)

    if content.status_code == 429:
        raise Exception("Rate limit exceeded, please try again later")
    if content.status_code != 200:
        raise Exception(
            f"Failed to fetch data from Google Fonts API due to {content.status_code}"
        )
    return content.json()


def get_local_fonts(file_path: str) -> json:
    """Loads font data from local JSON file"""

    with open(file_path, "r") as file:
        return json.load(file)


def generate_comparison_table(old_data: json, new_data: json) -> str:
    """Generate a markdown table comparing font versions and last modified dates"""

    table = "| Font Family | Version | Date |\n"
    table += "|---|---|---|\n"
    for old_font, new_font in zip(old_data["items"], new_data["items"]):
        if old_font["family"] == new_font["family"] and (
            old_font["version"] != new_font["version"]
            or old_font["lastModified"] != new_font["lastModified"]
        ):
            table += f"| {old_font['family']} | {old_font['version']} -> **{new_font['version']}** | {old_font['lastModified']} -> **{new_font['lastModified']}** |\n"
        else:
            if old_data == new_data:
                table = "🗿 No changes detected in font data"
    return table


def write_to_local_file(data: json, file_path: str, dev: bool = True) -> None:
    """Writes font data to a local JSON file"""

    if dev is False:
        with open(file_path, "w") as file:
            json.dump(data, file)
            print(f"Successful write on: {file_path}")
    print(f"dev is True passed, assuming task successful on: {file_path}")


def generate_summary(
    repository: str = None,
    task_name: str = None,
    markdown_table: str = None,
    error: str = None,
) -> list:
    """Generate a markdown summary message"""

    content = []

    heading = (
        f"👷 {repository} Automated Maintenance"
        if repository
        else "👷 Automated Maintenance"
    )
    heading_body = (
        f"This is auto-generated by {repository}'s `{sys.argv[0]}` script."
        if repository
        else f"This is auto-generated by `{sys.argv[0]}` script."
    )

    font_job_heading = f"{task_name}" if task_name else f"`{sys.argv[0]}`"
    font_job_body = (
        f"{task_name} data for **{repository}**. Here's a summary of the changes:"
        if task_name and repository
        else f"`{sys.argv[0]}` data. Here's a summary of the changes:"
    )

    content.append(f"# {heading}")
    content.append(heading_body)
    content.append(f"## {font_job_heading}")
    content.append(font_job_body)
    if markdown_table is None:
        content.append(
            "\nThe summary of the changes was not passed to me so this will remains blank\n"
        )
    else:
        content.append(markdown_table)
    if error is not None:
        content.append(f"Error: {error}")
        if stack_trace := traceback.print_exc():
            content.append("```")
            content.append(stack_trace)
            content.append("```")
        else:
            content.append("... No stack trace available?")

    return content


if not api_token:
    summary = generate_summary(
        repository,
        job_name,
        error="This script requires Google Fonts API, please set the API_TOKEN env variable",
    )
    for string in summary:
        print(string)
    exit(1)


local_fonts_data = get_local_fonts(local_file_path)
try:
    new_fonts_data = get_google_fonts(api_token)
except Exception as e:
    summary = generate_summary(
        repository, job_name, error=f"Failed to fetch data from Google Fonts API: {e}"
    )
    for string in summary:
        print(string)
    exit(1)

if local_fonts_data and new_fonts_data:
    try:
        comparison_table = (
            generate_comparison_table(local_fonts_data, new_fonts_data) or None
        )
    except Exception as e:
        summary = generate_summary(
            repository, job_name, error=f"Failed to generate comparison table: {e}"
        )
        for string in summary:
            print(string)
        exit(3)

    try:
        write_to_local_file(new_fonts_data, local_file_path, False)
    except Exception as e:
        summary = generate_summary(
            repository, job_name, error=f"Failed to write to local file: {e}"
        )
        for string in summary:
            print(string)
        exit(3)

    summary = generate_summary(repository, job_name, comparison_table)
    for string in summary:
        print(string)
else:
    summary = generate_summary(repository, job_name, error="Missing font data")
    for string in summary:
        print(string)
    exit(2)