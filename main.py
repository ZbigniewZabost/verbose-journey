from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from urllib.request import urlopen
from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR
from dateutil import parser
from PIL import Image
from datetime import datetime, timedelta
import os
import piexif
from pathvalidate import sanitize_filename

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
BASE_URL = os.getenv('BASE_URL')  # e.g. "https://paiiigeeee.mykita.com"
DAY_FROM = os.getenv('DAY_FROM')  # e.g. "2022-12-31"
DAY_TO = os.getenv('DAY_TO')  # e.g  "2022-12-31"
GROUP_ID = os.getenv('GROUP_ID')  # e.g "11"

OUTPUT_DIR = "/data"
JOURNAL_ENTRIES_COUNT = 0
GALLERY_IMAGES_COUNT = 0
ATTACHMENTS_FILES_COUNT = 0


def setup_driver():
    print("Setting up webdriver")
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    return driver


def login(driver, url, email, password):
    print("Signing into {} with email {}".format(BASE_URL, EMAIL))
    driver.get(url)
    driver.find_element(By.ID, "user_email").send_keys(email)
    driver.find_element(By.ID, "user_password").send_keys(password)
    driver.find_element(By.NAME, "commit").click()
    WebDriverWait(driver=driver, timeout=10).until(
        lambda x: x.execute_script("return document.readyState === 'complete'")
    )


def work_week_days(start_date_string, end_date_string):
    print("Getting work week days between {} and {}".format(DAY_FROM, DAY_TO))
    start_date = parser.parse(start_date_string)
    end_date = parser.parse(end_date_string)
    return rrule(DAILY, dtstart=start_date, until=end_date, byweekday=(MO, TU, WE, TH, FR))


def navigate_to_day(driver, day):
    day_string = day.strftime("%Y-%m-%d")
    print("Navigating to {} day view for group {}".format(day_string, GROUP_ID))
    day_view_url = "{}/groups/{}/calendar/{}/day".format(BASE_URL, GROUP_ID, day_string)
    driver.get(day_view_url)
    WebDriverWait(driver=driver, timeout=10).until(
        lambda x: x.execute_script("return document.readyState === 'complete'")
    )


def scrap_images(driver, day):
    global JOURNAL_ENTRIES_COUNT, GALLERY_IMAGES_COUNT, ATTACHMENTS_FILES_COUNT
    entries = driver.find_elements(By.CLASS_NAME, 'JournalEntrySmall')
    JOURNAL_ENTRIES_COUNT = JOURNAL_ENTRIES_COUNT + len(entries)
    print("\tFound {} journal entries in the day view".format(len(entries)))
    for e in entries:
        images_urls = []  # list of images urls from gallery modal
        attachments_urls = []  # list of files urls added as attachments to journal activity

        e.click()
        WebDriverWait(driver=driver, timeout=10).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )

        entry_title = "no_entry_title"
        entry_title_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'title-light')]")
        if len(entry_title_elements) > 0:
            entry_title = entry_title_elements[0].text
            print("\t\t" + entry_title[:80] + ":")
            entry_title = entry_title[:25]

        photos_elements = driver.find_elements(By.XPATH,
                                               "//div[contains(@class, 'carousel-item')]/img[@loading='lazy']")
        for p in photos_elements:
            images_urls.append(p.get_attribute("src"))

        download_media(day, entry_title, images_urls)
        GALLERY_IMAGES_COUNT = GALLERY_IMAGES_COUNT + len(images_urls)

        attachments = driver.find_elements(By.XPATH,
                                           "//table/tbody/tr/td/a[contains(@class, 'btn-light') and contains(@class, 'btn')]")
        for a in attachments:
            attachments_urls.append(a.get_attribute("href"))

        download_media(day, entry_title, attachments_urls)
        ATTACHMENTS_FILES_COUNT = ATTACHMENTS_FILES_COUNT + len(attachments_urls)

        driver.find_element(By.XPATH, '//a[contains(@class, "new-modal__close")]').click()

    print("\t\tFound {} images and {} attachments".format(len(images_urls), len(attachments_urls)))

def download_media(day, title, urls):
    counter = 1
    for u in urls:
        original_file_name = u.rsplit('/', 1)[-1]
        new_file_name = sanitize_filename(day.strftime("%Y-%m-%d") + "_" + title + "-" + str(counter)) + "." + original_file_name.rsplit('.', 1)[-1]
        print("\t\t\tDownloading {}/{} - {}".format(counter, len(urls), new_file_name))
        counter = counter + 1
        with urlopen(u) as file:
            content = file.read()
        path = OUTPUT_DIR + "/" + new_file_name
        with open(path, 'wb') as download:
            download.write(content)
        try:
            add_date_to_exif(path, day)
        except:
            print("\t\t\tError during exif parsing. Ignoring and proceeding.")

def add_date_to_exif(image, day):
    image_file = Image.open(image)
    exif_dict = piexif.load(image_file.info["exif"])
    exif_dict["0th"][piexif.ImageIFD.DateTime] = day.strftime("%Y:%m:%d %H:%M:%S")
    exif_bytes = piexif.dump(exif_dict)
    image_file.save(image, exif=exif_bytes)


def scrap_site():
    global DAY_FROM, DAY_TO
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not DAY_TO:
        DAY_TO = datetime.now().strftime("%Y-%m-%d")
    if not DAY_FROM:
        DAY_FROM = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    driver = setup_driver()
    login(driver, "{}/sessions/sign_in".format(BASE_URL), EMAIL, PASSWORD)
    days_count = 0
    for day in work_week_days(DAY_FROM, DAY_TO):
        days_count = days_count + 1
        navigate_to_day(driver, day)
        scrap_images(driver, day)
    driver.quit()
    print("Summary:")
    print("\tChecked {} days between {} and {}".format(days_count, DAY_FROM, DAY_TO))
    print("\tVisited {} journal entries".format(JOURNAL_ENTRIES_COUNT))
    print("\tFound {} images in galleries and {} files in attachments".format(GALLERY_IMAGES_COUNT,
                                                                              ATTACHMENTS_FILES_COUNT))


scrap_site()
