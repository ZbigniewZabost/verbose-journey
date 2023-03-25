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


def scrap_for_images_url(driver):
    global JOURNAL_ENTRIES_COUNT, GALLERY_IMAGES_COUNT, ATTACHMENTS_FILES_COUNT
    images_urls = []  # list of images urls from gallery modal
    attachments_urls = []  # list of files urls added as attachments to journal activity
    entries = driver.find_elements(By.CLASS_NAME, 'JournalEntrySmall')
    JOURNAL_ENTRIES_COUNT = JOURNAL_ENTRIES_COUNT + len(entries)
    print("\tFound {} journal entries in the day view".format(len(entries)))
    for e in entries:
        e.click()
        WebDriverWait(driver=driver, timeout=10).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )
        photos_elements = driver.find_elements(By.XPATH,
                                               "//div[contains(@class, 'carousel-item')]/img[@loading='lazy']")
        for p in photos_elements:
            images_urls.append(p.get_attribute("src"))
        attachments = driver.find_elements(By.XPATH,
                                           "//table/tbody/tr/td/a[contains(@class, 'btn-light') and contains(@class, 'btn')]")
        for a in attachments:
            attachments_urls.append(a.get_attribute("href"))
        driver.find_element(By.XPATH, '//a[contains(@class, "new-modal__close")]').click()
    print("\t\tFound {} images and {} attachments".format(len(images_urls), len(attachments_urls)))
    GALLERY_IMAGES_COUNT = GALLERY_IMAGES_COUNT + len(images_urls)
    ATTACHMENTS_FILES_COUNT = ATTACHMENTS_FILES_COUNT + len(attachments_urls)
    return images_urls + attachments_urls


def download_images(day, urls):
    counter = 1
    for u in urls:
        print("\t\tDownloading {}/{}".format(counter, len(urls)))
        counter = counter + 1
        with urlopen(u) as file:
            content = file.read()
        path = OUTPUT_DIR + "/" + day.strftime("%Y-%m-%d") + "-" + u.rsplit('/', 1)[-1]
        with open(path, 'wb') as download:
            download.write(content)
        add_date_to_exif(path, day)


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
    photos_count = 0
    days_count = 0
    for day in work_week_days(DAY_FROM, DAY_TO):
        days_count = days_count + 1
        navigate_to_day(driver, day)
        photos_url = scrap_for_images_url(driver)
        download_images(day, photos_url)
        photos_count = photos_count + len(photos_url)
    driver.quit()
    print("Summary:")
    print("\tChecked {} days between {} and {}".format(days_count, DAY_FROM, DAY_TO))
    print("\tVisited {} journal entries".format(JOURNAL_ENTRIES_COUNT))
    print("\tFound {} images in galleries and {} files in attachments".format(GALLERY_IMAGES_COUNT,
                                                                              ATTACHMENTS_FILES_COUNT))
    print("\tDownloaded {} files".format(photos_count))


scrap_site()
