from __future__ import annotations
import time, random, os, csv, platform
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import pyautogui
from urllib.request import urlopen
from webdriver_manager.chrome import ChromeDriverManager
import re
import yaml
from datetime import datetime, timedelta

""" The tkinter window is a GUI popup to pause the script to allow user to validate human verification """
# import tkinter as tk
# # create root window
# root = tk.Tk()
# # create label widget and set text
# label = tk.Label(root, text="Check for Human Verification, Press Continue when done")
# # create button widget and set text + command
# button = tk.Button(root, text="OK", command=root.destroy)
# # configure label and button widgets
# label.pack(pady=10)
# button.pack()

log = logging.getLogger(__name__)

driver = webdriver.Chrome(ChromeDriverManager().install())


def setupLogger() -> None:
    dt: str = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")

    if not os.path.isdir("./logs"):
        os.mkdir("./logs")

    # TODO need to check if there is a log dir available or not
    logging.basicConfig(
        filename=("./logs/" + str(dt) + "applyJobs.log"),
        filemode="w",
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
        datefmt="./logs/%d-%b-%y %H:%M:%S",
    )
    log.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S"
    )
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)


class EasyApplyBot:
    setupLogger()
    # MAX_SEARCH_TIME is 10 hours by default, feel free to modify it
    # MAX_SEARCH_TIME = 10 * 60 * 60

    def __init__(
        self,
        username,
        password,
        phone_number,
        uploads={},
        filename="output.csv",
        blacklist=[],
        blackListTitles=[],
    ) -> None:
        log.info("Welcome to Easy Apply Bot")
        dirpath: str = os.getcwd()
        log.info("current directory is : " + dirpath)

        self.uploads = uploads
        past_ids: list | None = self.get_appliedIDs(filename)
        self.appliedJobIDs: list = past_ids if past_ids != None else []
        self.filename: str = filename
        self.options = self.browser_options()
        self.browser = driver
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(username, password)
        self.phone_number = phone_number

    def get_appliedIDs(self, filename) -> list | None:
        try:
            df = pd.read_csv(
                filename,
                header=None,
                names=["timestamp", "jobID", "job", "company", "attempted", "result"],
                lineterminator="\n",
                encoding="utf-8",
            )

            df["timestamp"] = pd.to_datetime(
                df["timestamp"], format="%Y-%m-%d %H:%M:%S"
            )
            df = df[df["timestamp"] > (datetime.now() - timedelta(days=2))]
            jobIDs: list = list(df.jobID)
            log.info(f"{len(jobIDs)} jobIDs found")
            return jobIDs
        except Exception as e:
            log.info(
                str(e) + "   jobIDs could not be loaded from CSV {}".format(filename)
            )
            return None

    def browser_options(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")

        # Disable webdriver flags or you will be easily detectable
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        return options

    def start_linkedin(self, username, password) -> None:
        log.info("Logging in.....Please wait :)  ")
        self.browser.get(
            "https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin"
        )
        try:
            user_field = self.browser.find_element("id", "username")
            pw_field = self.browser.find_element("id", "password")
            login_button = self.browser.find_element(
                "xpath", '//*[@id="organic-div"]/form/div[3]/button'
            )
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(1)
            pw_field.send_keys(password)
            time.sleep(1)
            login_button.click()
            # Call GUI popup to pause script to allow user to check for verification
            # root.mainloop()
        except TimeoutException:
            log.info(
                "TimeoutException! Username/password field or login button not found"
            )

    def fill_data(self) -> None:
        self.browser.set_window_size(1, 1)
        self.browser.set_window_position(2000, 2000)

    def start_apply(self, positions, locations) -> None:
        start: float = time.time()
        self.fill_data()

        combos: list = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)
            if combo not in combos:
                combos.append(combo)
                log.info(f"Applying to {position}: {location}")
                location = "&location=" + location
                self.applications_loop(position, location)
            if len(combos) > 500:
                break

    def applications_loop(self, position, location):
        count_application = 0
        count_job = 0
        jobs_per_page = 0
        start_time: float = time.time()

        log.info("Looking for jobs.. Please wait..")

        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page)
        log.info("Looking for jobs.. Please wait..")

        while True: # time.time() - start_time < self.MAX_SEARCH_TIME:
            try:
                # log.info(
                #     f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search"
                # )

                # sleep to make sure everything loads, add random to make us look human.
                randoTime: float = random.uniform(0.5, 1.5)
                log.debug(f"Sleeping for {round(randoTime, 1)}")
                time.sleep(randoTime)
                self.load_page(sleep=1)

                # LinkedIn displays the search results in a scrollable <div> on the left side, we have to scroll to its bottom

                scrollresults = self.browser.find_element(
                    By.CLASS_NAME, "jobs-search-results-list"
                )
                # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
                for i in range(300, 3000, 100):
                    self.browser.execute_script(
                        "arguments[0].scrollTo(0, {})".format(i), scrollresults
                    )

                time.sleep(0.3)

                # get job links, (the following are actually the job card objects)
                links = self.browser.find_elements("xpath", "//div[@data-job-id]")

                if len(links) == 0:
                    log.debug("No links found")
                    break

                IDs: list = []

                # children selector is the container of the job cards on the left
                for link in links:
                    children = link.find_elements(
                        "xpath", '//ul[@class="scaffold-layout__list-container"]'
                    )
                    for child in children:
                        if child.text not in self.blacklist:
                            temp = link.get_attribute("data-job-id")
                            jobID = temp.split(":")[-1]
                            IDs.append(int(jobID))
                IDs: list = set(IDs)
                log.debug(IDs)

                # remove already applied jobs
                before: int = len(IDs)
                jobIDs: list = [x for x in IDs if x not in self.appliedJobIDs]

                after: int = len(jobIDs)

                # it assumed that 25 jobs are listed in the results window
                if len(jobIDs) == 0 and len(IDs) > 23:
                    jobs_per_page = jobs_per_page + 25
                    count_job = 0
                    self.avoid_lock()
                    self.browser, jobs_per_page = self.next_jobs_page(
                        position, location, jobs_per_page
                    )
                # loop over IDs to apply
                for i, jobID in enumerate(jobIDs):
                    count_job += 1
                    self.get_job_page(jobID)

                    # get easy apply button
                    button = self.get_easy_apply_button()
                    # word filter to skip positions not wanted

                    if button is not False:
                        if any(word in self.browser.title for word in blackListTitles):
                            log.info(
                                "skipping this application, a blacklisted keyword was found in the job position"
                            )
                            string_easy = "* Contains blacklisted keyword"
                            result = False
                        else:
                            string_easy = "* has Easy Apply Button"
                            log.info("Clicking the EASY apply button")

                            # Scrolls to the top of the page to avoid the "Apply" button being hidden by the top banner
                            self.browser.execute_script("window.scrollTo(0, 0);")
                            time.sleep(0.5)
                            button.click()
                            time.sleep(0.1)
                            # self.fill_out_phone_number()
                            result: bool = self.send_resume()
                            count_application += 1
                    else:
                        log.info("The button does not exist.")
                        string_easy = "* Doesn't have Easy Apply Button"
                        result = False

                    position_number: str = str(count_job + jobs_per_page)
                    log.info(
                        f"\nPosition {position_number}:\n {self.browser.title} \n {string_easy} \n"
                    )

                    self.write_to_file(button, jobID, self.browser.title, result)

                    # sleep every 20 applications
                    # if count_application != 0 and count_application % 20 == 0:
                    #     sleepTime: int = random.randint(500, 900)
                    #     log.info(
                    #         f"""********count_application: {count_application}************\n\n
                    #                 Time for a nap - see you in:{int(sleepTime / 60)} min
                    #             ****************************************\n\n"""
                    #     )
                    #     time.sleep(sleepTime)

                    # go to new page if all jobs are done
                    if count_job == len(jobIDs):
                        jobs_per_page = jobs_per_page + 25
                        count_job = 0
                        log.info(
                            """****************************************\n\n
                        Going to next jobs page, YEAAAHHH!!
                        ****************************************\n\n"""
                        )
                        self.avoid_lock()
                        self.browser, jobs_per_page = self.next_jobs_page(
                            position, location, jobs_per_page
                        )
            except Exception as e:
                print(e)

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        attempted: bool = False if button == False else True
        job = re_extract(browserTitle.split(" | ")[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(" | ")[1], r"(\w.*)")

        toWrite: list = [timestamp, jobID, job, company, attempted, result]
        with open(self.filename, "a") as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):
        job: str = "https://www.linkedin.com/jobs/view/" + str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def get_easy_apply_button(self):
        try:
            button = self.browser.find_elements(
                "xpath", '//button[contains(@class, "jobs-apply-button")]'
            )

            EasyApplyButton = button[0]

        except Exception as e:
            print("Exception:", e)
            EasyApplyButton = False

        return EasyApplyButton

    def fill_out_phone_number(self):
        def is_present(button_locator) -> bool:
            return (
                len(self.browser.find_elements(button_locator[0], button_locator[1]))
                > 0
            )

        submitted = False
        for i in range(5):
            next_locater = (
                By.CSS_SELECTOR,
                "button[aria-label='Continue to next step']",
            )

            input_field_phone = self.browser.find_element(
                "xpath", "//input[contains(@name,'phoneNumber')]"
            )

            if input_field_phone:
                input_field_phone.clear()
                input_field_phone.send_keys(self.phone_number)
                time.sleep(random.uniform(0.5, 1))

                next_locater = (
                    By.CSS_SELECTOR,
                    "button[aria-label='Continue to next step']",
                )
                error_locator = (
                    By.CSS_SELECTOR,
                    "p[data-test-form-element-error-message='true']",
                )

                # Click Next or submit button if possible
                button: None = None
                if is_present(next_locater):
                    button: None = self.wait.until(
                        EC.element_to_be_clickable(next_locater)
                    )

                if is_present(error_locator):
                    for element in self.browser.find_elements(
                        error_locator[0], error_locator[1]
                    ):
                        text = element.text
                        if "Please enter a valid answer" in text:
                            button = None
                            break
                if button:
                    button.click()
                    time.sleep(random.uniform(0.5, 1))
                    if i in (3, 4):
                        submitted = True
                    if i != 2:
                        break

            else:
                log.debug(f"Could not find phone number field")
        return submitted

    def send_resume(self) -> bool:
        def scroll_down_modal():
            # Sometimes the model has a scroll and we can't see the "next, review, or submit" buttons. So Attempt to scroll down on the modal
            log.debug("Attempting to scroll down modal")
            modal = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "artdeco-modal__content")
                )
            )

            # Scroll the modal
            self.browser.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", modal
            )
            time.sleep(random.uniform(0.5, 1))
            log.debug("Scrolling down modal")

        try:
            time.sleep(random.uniform(0.5, 1))
            count = 0
            answer_count = 0
            submited = False

            while True:
                log.debug("Resume submit loop")
                log.debug("count: " + str(count))
                if count >= 5:
                    log.info("Infinite loop detected")
                    break

                try:
                    errorText = self.browser.find_elements_by_class_name(
                        "artdeco-inline-feedback__message"
                    )
                except:
                    errorText = None

                try:
                    review_button = driver.find_element_by_xpath(
                        "//button[contains(span, 'Review')]"
                    )
                except:
                    review_button = None

                try:
                    submit_button = driver.find_element_by_xpath(
                        "//button[contains(span, 'Submit')]"
                    )
                except:
                    submit_button = None

                try:
                    next_button = driver.find_element_by_xpath(
                        "//button[contains(span, 'Next')]"
                    )
                except:
                    next_button = None

                if errorText:
                    if answer_count >= 5:
                        log.info("Failed to answer question correctly 5 times")
                        break

                    log.debug("Wrong answer detected")
                    # Get the fields
                    try:
                        text_field = self.browser.find_elements_by_class_name(
                            "artdeco-text-input--input"
                        )
                    except:
                        text_field = None

                    try:
                        yes_radials = driver.find_elements_by_xpath(
                            '//Input[@data-test-text-selectable-option__label="Yes"]'
                        )
                    except:
                        yes_radials = None
                    try:
                        no_radials = driver.find_elements_by_xpath(
                            '//Input[@data-test-text-selectable-option__label="No"]'
                        )
                    except:
                        no_radials = None

                    # Loop through radial buttons and click "Yes"
                    for radial in yes_radials:
                        # Check if radial is unselected and has label "Yes"
                        if (
                            not radial.is_selected()
                            and radial.get_attribute(
                                "data-test-text-selectable-option__label"
                            )
                            == "Yes"
                        ):
                            # Click on "Yes" radial if condition is satisfied
                            radial.click()

                    # Fills out input fields
                    input_fields = driver.find_elements_by_class_name(
                        "artdeco-text-input--label"
                    )

                    for input_fields in text_field:
                        # log.debug("input field loop Var:" + input_fields)
                        # Hidden fields
                        if input_fields.get_attribute("type") == "hidden":
                            log.debug("Hidden field")
                            continue
                        # Submits the string "2" if the field is empty
                        textInput = input_fields.get_attribute("value")
                        log.debug(textInput)
                        if not textInput:
                            # Need a random values between 2, 2.5 3
                            randoNum = random.randint(0, 2)
                            randoDec = randoNum / 2 + 2
                            input_fields.send_keys(str(randoDec))
                            log.info("Answered question")
                            time.sleep(random.uniform(0.5, 2.5))

                    dropdowns = driver.find_elements_by_xpath("//select")
                    log.debug(dropdowns)

                    for elem in dropdowns:
                        sel = Select(elem)
                        val = sel.first_selected_option.text
                        log.debug("Selected option: " + val)
                        if val == "Select an option":
                            sel.select_by_value("Yes")
                            # sel.select_by_visible_text('Yes')
                    # In case we want to select no
                    # elem.select_by_value("No")

                    log.debug("Finished answering questions")
                    time.sleep(random.uniform(0.5, 1))
                    answer_count += 1

                elif next_button:
                    answer_count = 0
                    next_button = driver.find_element_by_xpath(
                        "//button[contains(span, 'Next')]"
                    )
                    next_button.click()

                    log.info("Clicked next button")
                    time.sleep(random.uniform(0.5, 1))
                elif review_button:
                    answer_count = 0
                    review_button.click()
                    log.info("Clicked Review button")
                    time.sleep(random.uniform(0.5, 1))

                elif submit_button:
                    answer_count = 0
                    submit_button.click()
                    log.info("Clicked submit button")
                    time.sleep(random.uniform(0.5, 1))
                    submited = True
                    break

                else:
                    answer_count = 0
                    log.debug("Submit button not available on current screen")
                    scroll_down_modal()
                    count += 1
                    log.debug(
                        "Submit button not found and no action available (Count: "
                        + str(count)
                        + ")"
                    )

        except Exception as e:
            log.info(e)
            log.info("cannot apply to this job")
            submited = False

        return submited

    def load_page(self, sleep=1):
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 200
            time.sleep(sleep)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep * 3)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def avoid_lock(self) -> None:
        x, _ = pyautogui.position()
        pyautogui.moveTo(x + 200, pyautogui.position().y, duration=1.0)
        pyautogui.moveTo(x, pyautogui.position().y, duration=0.5)
        pyautogui.keyDown("ctrl")
        pyautogui.press("esc")
        pyautogui.keyUp("ctrl")
        time.sleep(0.5)
        pyautogui.press("esc")

    def next_jobs_page(self, position, location, jobs_per_page):
        self.browser.get(
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords="
            + position
            + location
            + "&start="
            + str(jobs_per_page)
        )
        self.avoid_lock()
        log.info("Lock avoided.")
        self.load_page()
        return (self.browser, jobs_per_page)

    def finish_apply(self) -> None:
        self.browser.close()


if __name__ == "__main__":
    with open("config.yaml", "r") as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    assert len(parameters["positions"]) > 0
    assert len(parameters["locations"]) > 0
    assert parameters["username"] is not None
    assert parameters["password"] is not None
    assert parameters["phone_number"] is not None

    if "uploads" in parameters.keys() and type(parameters["uploads"]) == list:
        raise Exception(
            "uploads read from the config file appear to be in list format"
            + " while should be dict. Try removing '-' from line containing"
            + " filename & path"
        )

    log.info(
        {
            k: parameters[k]
            for k in parameters.keys()
            if k not in ["username", "password"]
        }
    )

    output_filename: list = [
        f for f in parameters.get("output_filename", ["output.csv"]) if f != None
    ]
    output_filename: list = (
        output_filename[0] if len(output_filename) > 0 else "output.csv"
    )
    blacklist = parameters.get("blacklist", [])
    blackListTitles = parameters.get("blackListTitles", [])

    uploads = (
        {} if parameters.get("uploads", {}) == None else parameters.get("uploads", {})
    )
    for key in uploads.keys():
        assert uploads[key] != None

    bot = EasyApplyBot(
        parameters["username"],
        parameters["password"],
        parameters["phone_number"],
        uploads=uploads,
        filename=output_filename,
        blacklist=blacklist,
        blackListTitles=blackListTitles,
    )

    locations: list = [l for l in parameters["locations"] if l != None]
    positions: list = [p for p in parameters["positions"] if p != None]
    bot.start_apply(positions, locations)
