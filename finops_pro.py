from selenium.webdriver.common.by import By
import time
import requests
from selenium import webdriver
import os
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import subprocess
from bs4 import BeautifulSoup
import shutil

root_dir = os.path.dirname(os.path.abspath(__file__))
content_dir = f"{root_dir}/content"
if os.path.isdir(content_dir):
    # delete the directory and all its contents
    shutil.rmtree(content_dir)

os.makedirs(content_dir)
os.chdir(content_dir)

# Set up capabilities to enable performance logging
caps = DesiredCapabilities.CHROME
caps['goog:loggingPrefs'] = {'performance': 'ALL'}

# Initialize the Chrome driver with the capabilities
driver = webdriver.Chrome(desired_capabilities=caps)
driver.get("https://learn.finops.org/path/finops-certified-professional")

# Find Sign In Button and click it
sign_in_link = driver.find_element(By.XPATH,
                                   '/html/body/div/div[1]/div[1]/div[2]/div[2]/div/div/div/div[1]/p/strong/a')
sign_in_link.click()

# Wait for page to load
time.sleep(3)

user_name = os.environ.get('user_name')
password = os.environ.get('password')

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

# go through each section to find sub-sections
# for i in range(len(sections_list)):
for i in range(1, 40):#debugging only
    section = driver.find_element(By.XPATH,
                                  f"/html/body/div/div[1]/div/div[4]/div[2]/a[{i+1}]")
    section_name = section.text.replace('\n', ' ')
    # print(section_name)
    section.click()  # Click on section to reveal content
    try:
        section_short_name = f"{i}-{driver.find_element(By.XPATH,'/html/body/div/div[1]/div[1]/div[2]/div/div/div[1]/h1').text}"
        os.mkdir(section_short_name)
        os.chdir(section_short_name)
    except:
        os.chdir(content_dir)
        driver.back()
        continue

    # Wait for page to load
    time.sleep(2)
    # find each sub-section
    try:
        sub_sections = driver.find_element(By.XPATH,
                                       "/html/body/div/div[1]/div[2]/div/div/section[1]/div/div").text.split('\n')
    except:
        # no sub section, breeak
        os.chdir(content_dir)
        driver.back()
        continue

    # go through each sub-section
    for j in range(len(sub_sections)):
        sub_section = driver.find_element(
            By.XPATH, f"/html/body/div/div[1]/div[2]/div/div/section[1]/div/div/a[{j+1}]")
        sub_section_name = sub_section.text
        # print(sub_section_name)
        # print(sub_section.get_attribute("href"))
 
        # check if the subsection contains video based on the text
        if sub_section.text.find('Video') > -1:
            # Set the name of the output file
            mp4_file = f"{sub_section.text}.mp4".replace(' ', '_').replace(':','')

            sub_section.click()
            time.sleep(2)

            # find the mp4 in the page
            logs = driver.get_log('performance')

            # Extract the m3u8 link from the logs
            m3u8_url = None
            for log in logs:
                message = json.loads(log['message'])
                if 'Network.responseReceived' in message['message']['method']:
                    params = message['message']['params']
                    if 'response' in params:
                        url = params['response']['url']
                        if url.endswith('.m3u8'):
                            m3u8_url = url
                            # download mp4 from m3u8 using ffmpeg
                            subprocess.run(['ffmpeg', '-i', m3u8_url, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', mp4_file])
                            break
        else:
            # Save section content to file
            sub_section.click()

            # if pdf found, download
            # get the page source
            page_source = driver.page_source
            # parse the page source using BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            # find the 'a' tag with the href attribute containing the URL of the PDF
            pdf_link = soup.find('a', target="_blank")
            if pdf_link is not None:
                # get the URL of the PDF
                pdf_url = pdf_link['href']
                if pdf_url.find('.pdf') > -1:
                    # download the PDF using requests
                    response = requests.get(pdf_url)
                    # save the PDF to a file
                    pdf_filename = pdf_url.split('.pdf')[0].split('/')[len(pdf_url.split('.pdf')[0].split('/'))-1]
                    with open(f'{pdf_filename}.pdf', 'wb') as f:
                        f.write(response.content)
                        f.close()
                else: # text only, save to file
                    with open(f"{sub_section_name}.txt", "w", encoding="utf-8") as f:
                        f.write(driver.find_element(By.XPATH,
                            '/html/body/div/div[1]/div/div[2]/div/div/div[2]/div').text)

        # go back to section
        driver.back()
    # go back to main
    os.chdir(content_dir)
    driver.back()

driver.quit()
