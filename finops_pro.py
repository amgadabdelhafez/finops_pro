from selenium.webdriver.common.by import By
import time
import base64
import requests
from selenium import webdriver

# Set the options for the Chrome driver
options = webdriver.ChromeOptions()
options.add_argument("--disable-site-isolation-trials")

# Initialize the Chrome driver with the options
driver = webdriver.Chrome(options=options)

driver.get("https://learn.finops.org/path/finops-certified-professional")

# Find Sign In Button and click it

sign_in_link = driver.find_element(By.XPATH,
                                   '/html/body/div/div[1]/div[1]/div[2]/div[2]/div/div/div/div[1]/p/strong/a')
sign_in_link.click()

# Wait for page to load
time.sleep(3)
user_name = ''
password = ''

# Login
email_input = driver.find_element(By.XPATH,
                                  "/html/body/div/div[1]/div[2]/div/div/form/div/div[1]/input")

email_input.send_keys(user_name)

password_input = driver.find_element(By.XPATH,
                                     "/html/body/div/div[1]/div[2]/div/div/form/div/div[2]/input")
password_input.send_keys(password)

login_button = driver.find_element(By.XPATH,
                                   "/html/body/div/div[1]/div[2]/div/div/form/div/div[4]/button")
login_button.click()

# Wait for page to load
time.sleep(2)

# all sections
all_sections = driver.find_element(By.XPATH,
                                   "/html/body/div/div[1]/div/div[4]/div[2]").text
sections_list = all_sections.replace('\n', ' ').split(' min')

# all sections path
for i in range(len(sections_list)):
    section = driver.find_element(By.XPATH,
                                  f"/html/body/div/div[1]/div/div[4]/div[2]/a[{i+1}]")
    section_name = section.text.replace('\n', ' ')
    print(section_name)
    section.click()  # Click on section to reveal content
    time.sleep(2)
    # find each sub-section
    sub_sections = driver.find_element(By.XPATH,
                                       "/html/body/div/div[1]/div[2]/div/div/section[1]/div/div").text.split('\n')
    # go through each sub-section
    for j in range(len(sub_sections)):
        sub_section = driver.find_element(
            By.XPATH, f"/html/body/div/div[1]/div[2]/div/div/section[1]/div/div/a[{j+1}]")
        print(sub_section.text)
        mp4_file = f"{sub_section.text}.mp4"

        print(sub_section.get_attribute("href"))
        sub_section.click()
        time.sleep(2)
        # find the mp4 in the page
        mp4_link = driver.find_element(
            By.XPATH, "/html/body/div/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[2]/div[4]/video")
        mp4_blob = mp4_link.get_attribute("src")
        print(mp4_blob)
        # download mp4
        # response = urllib.request.urlopen(mp4_blob)
        # video_data = response.read()

        # with open(mp4_file, "wb") as f:
        #     f.write(mp4_blob.encode())
        #     f.close()
        #     print(mp4_file)
        #     time.sleep(2)
        #     # go back to section
        #     driver.back()

        # Save section content to file
        # with open(f"{section_name}.txt", "w", encoding="utf-8") as f:
        #     f.write(driver.find_element_by_css_selector(
        #         'div[data-path="content"] div[class="content"]').text)

    driver.get("https://learn.finops.org/path/finops-certified-professional")
    time.sleep(2)


driver.quit()
