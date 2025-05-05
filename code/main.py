import asyncio
import contextlib
import datetime
import logging
import os
import random
import re
import shutil
import zipfile

import aiohttp
import httplib2
from aiohttp_proxy import ProxyConnector
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio
from transliterate import translit

from excel_functions import create_excel_file, write_datas
from json_functions import add_institution, get_institution_departments, add_department_to_institution

# Load environment variables from the .env file
load_dotenv()

# Configure logging to write logs to 'parser.log' with timestamp and level
logging.basicConfig(
    filename='parser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Load proxies from environment variable, split by commas
PROXIES = os.getenv("PROXIES", "").split(',')
proxy_index = 0

# Dictionary for temporary in-memory storage of department-related data
dictionary: dict = {}


# Define base and data directory paths (ensures access from project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def get_next_proxy():
    """
    Cycles through the list of proxies and returns the next available ProxyConnector

    :return: ProxyConnector object based on the current proxy URL
    """
    global proxy_index
    proxy = PROXIES[proxy_index % len(PROXIES)]
    proxy_index += 1
    return ProxyConnector.from_url(proxy)


def get_safe_name(name: str) -> str:
    """
    Sanitizes institution names for safe usage in file paths by removing forbidden characters.

    :param name: Original name (possibly containing unsafe characters)
    :return: Sanitized name safe for use in file/directory names
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)


async def parse_urls_institutions() -> None:
    """
    Fetches the main institutions page and collects all institution names and their URLs.
    Saves the results to 'data/institutions_urls.txt' in the format: "<name>*<url>"
    """
    # Prepare request headers with custom User-Agent
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": os.getenv("USER_AGENT")
    }

    url = os.getenv("TEACHERS_URL")

    # Start an HTTP session with the current proxy
    async with aiohttp.ClientSession(connector=get_next_proxy()) as session:
        session: aiohttp.ClientSession
        async with session.get(url=url, headers=headers) as response:
            src = await response.text()
            soup = BeautifulSoup(src, "lxml")

            # Get the list of institution <a> tags (7th block of class="mtop20")
            institutions = soup.find_all(class_="mtop20")[7].find_all("a")

            # Build full URLs and extract short names
            institutions_urls = [
                "https://studizba.com" + "/".join(url.get("href").split("-", 1)[0].split("/")[:-1]) + "/" +
                url.get("href").split("-", 1)[1] for url in institutions
            ]

            institutions_names = [
                institution.find(class_="link-hs-content").find(class_="link-hs-content-abbr").text
                for institution in institutions
            ]

            # Save as "<name>*<url>" pairs to a text file
            with open(os.path.join(DATA_DIR, "institutions_urls.txt"), "w", encoding="utf-8-sig") as file:
                for name, url in zip(institutions_names, institutions_urls):
                    file.write(f"{name}*{url}\n")


async def parse_institutions() -> None:
    """
    Goes through the list of institutions and launches department parsing for each one.
    For every institution:
      - it creates folders
      - saves meta-info
      - initializes Excel file
      - then extracts department blocks and schedules them for parsing
    """
    # Set HTTP headers for requests
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": os.getenv("USER_AGENT")
    }

    # Read the list of institutions from file (name*url)
    with open(os.path.join(DATA_DIR, "institutions_urls.txt"), encoding="utf-8-sig") as file:
        institutions = [line.strip().split("*") for line in file.readlines()]

    for original_name, url in institutions:
        # Clean local cache (used by httplib2)
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(".cache")

        safe_name = get_safe_name(original_name)
        logging.info(f"Processing: {original_name}")

        # Manually skipped institutions (e.g., too large or problematic)
        if original_name in ["МАИ", "МГТУ им. Н.Э.Баумана", "МГУ им. Ломоносова"]:
            logging.info(f"Skipped: {original_name}")
            continue

        # Add institution to JSON storage (if not already there)
        await add_institution(original_name)

        # Create folders to store output files and photos
        os.makedirs(os.path.join(DATA_DIR, f"{safe_name}/teachers"), exist_ok=True)

        # Save the institution's name and URL locally
        with open(os.path.join(DATA_DIR, f"{safe_name}/name-url.txt"), "w", encoding="utf-8-sig") as f:
            f.write(f"{original_name}*{url}")

        # Create a new Excel file for this institution
        await create_excel_file(os.path.join(DATA_DIR, f"{safe_name}/{original_name}.xlsx"))

        # Start a new session to fetch the department list
        async with aiohttp.ClientSession(connector=get_next_proxy()) as session:
            session: aiohttp.ClientSession
            async with session.get(url=url, headers=headers) as response:
                src = await response.text()
                soup = BeautifulSoup(src, "lxml")

                # Find all departments inside the institution page
                departments = soup.find(class_="cat-list t-list").find_all(
                    class_="content-white-block link-subj one-t t"
                )

                tasks = []

                for dept in departments:
                    dept_name = dept.get_text("*").split("*")[0].strip()

                    # Skip already processed departments
                    if dept_name in await get_institution_departments(original_name):
                        continue

                    await asyncio.sleep(random.uniform(1.5, 3.5))
                    tasks.append(parse_department(dept, url, original_name))

                # Parse all departments concurrently
                await asyncio.gather(*tasks)


async def parse_department(
        department: Tag,
        institution_url: str,
        institution_name: str
) -> None:
    """
    Parses a single department page and collects all teacher profiles listed there

    For each department:
      - extracts the department name and its URL
      - parses all teacher blocks
      - saves the data into Excel
      - and registers the department in the JSON structure

    :param department: HTML element representing the department (from the main page)
    :param institution_url: URL of the parent institution
    :param institution_name: Original name of the institution (used in Excel and JSON)
    """
    # Headers for HTTP request
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }

    # Extract department name and build full department URL
    department_name = department.get_text("*").split("*")[0].strip()
    department_url = institution_url + department.find("a").get("href")

    # Prepare in-memory list for storing teacher data
    dictionary[department_name] = []

    # Open a new session to fetch teacher list
    async with aiohttp.ClientSession(connector=get_next_proxy()) as session:
        session: aiohttp.ClientSession
        async with session.get(url=department_url, headers=headers) as response:
            src = await response.text()
            soup = BeautifulSoup(src, "lxml")

            # Extract all teacher blocks
            teachers = soup.find_all(class_="content-white-block t one-t")

            # Schedule parsing for each teacher with progress bar
            tasks = [
                parse_teacher(session, teacher, department_url, institution_name, department_name)
                for teacher in tqdm_asyncio(teachers, desc=f"Teachers: {department_name}")
            ]
            await asyncio.gather(*tasks)

    # Give a short pause before continuing
    await asyncio.sleep(0.3)

    # Save collected teacher data into Excel file
    safe_name = get_safe_name(institution_name)
    path = os.path.join(DATA_DIR, f"{safe_name}/{institution_name}.xlsx")
    await write_datas(dictionary[department_name], path)

    # Clean up in-memory storage
    dictionary.pop(department_name, None)

    # Add department to institution's list in JSON
    await add_department_to_institution(institution_name, department_name)
    logging.info(f"Parsed department: {department_name}")


async def parse_teacher(
        session: aiohttp.ClientSession,
        teacher: Tag,
        department_url: str,
        institution_name: str,
        department_name: str
) -> None:
    """
    Parses a single teacher's profile page, extracts relevant data, and adds it to the department dictionary

    Collected data includes:
    - full name
    - HTML and plain-text description
    - external profile links
    - links to saved photo files

    :param session: shared aiohttp session with proxy
    :param teacher: HTML element of the teacher block (from department page)
    :param department_url: full URL of the department page
    :param institution_name: name of the institution (used for directory structure)
    :param department_name: name of the department (used as a dictionary key)
    """
    # Headers for the teacher profile request
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": os.getenv("USER_AGENT")
    }

    # Extract full name and construct full profile URL
    teacher_fullname = teacher.get_text("*").split("*")[0].strip()
    teacher_url = department_url + teacher.find("a").get("href")

    # Fetch teacher profile page
    async with session.get(url=teacher_url, headers=headers) as response:
        src = await response.text()
        soup = BeautifulSoup(src, "lxml")

        # Ensure profile block exists
        teacher_block = soup.find(class_="teacher-body")
        if not teacher_block:
            return

        teacher_description = teacher_block.find(id="teacher_info_inside")
        if not teacher_description:
            return

        # Extract both HTML and plain text versions of the profile description
        description_html = str(teacher_description)
        description_text = teacher_description.get_text()

        # Collect external links (if any)
        links_block = soup.find(class_="hs-block-panel external-links")
        teacher_links = []
        if links_block:
            teacher_links = [a.get("href") for a in links_block.find_all("a") if a.get("href") != "#"]

        # Collect photo URLs and download them
        photos_block = soup.find(class_="teacher-fotorama")
        image_paths = []

        if photos_block:
            photo_urls = [
                "https://studizba.com/" + i.replace("amp;", "")
                for i in str(photos_block).split("\"")
                if i.startswith("/z.php?w=1200")
            ]
            count = 1
            safe_name = get_safe_name(institution_name)

            for url in photo_urls:
                filename = os.path.join(
                    DATA_DIR,
                    safe_name,
                    "teachers",
                    f"{translit('_'.join(teacher_fullname.split()), 'ru', reversed=True)}_{count}.jpg"
                )
                relative_path = os.path.relpath(filename, os.path.join(DATA_DIR, safe_name))
                image_paths.append(relative_path)
                count += 1

                # Download and save the photo
                h = httplib2.Http('.cache')
                _, content = h.request(url)
                with open(filename, 'wb') as f:
                    f.write(content)

        # Add all collected data to the shared dictionary for this department
        dictionary[department_name].append([
            department_name,
            teacher_fullname,
            description_html,
            description_text,
            ",".join(teacher_links),
            ",".join(image_paths)
        ])


async def main():
    """
    Entry point for the scraping process.

    This function:
    - launches the full parsing workflow for all institutions and departments
    - creates a ZIP archive with all collected data
    - deletes the original 'data/' directory after archiving
    - and logs the total runtime
    """
    start = datetime.datetime.now()
    logging.info(f"Started: {start}")

    # Start the scraping process
    await parse_institutions()

    # Create a ZIP archive from the collected data
    zip_path = os.path.join(BASE_DIR, "data.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(DATA_DIR):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, BASE_DIR)  # Relative path inside the archive
                zipf.write(file_path, arcname)

    logging.info("Created archive: data.zip")

    # Clean up: remove the 'data/' directory after archiving
    try:
        shutil.rmtree(DATA_DIR)
        logging.info("Deleted data directory after archiving")
    except Exception as e:
        logging.warning(f"Failed to delete data directory: {e}")

    logging.info(f"Finished in: {datetime.datetime.now() - start}")


if __name__ == '__main__':
    # Run the async main function and allow graceful interruption via Ctrl+C
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Cancelled by user")
