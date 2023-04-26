import os
import time
import requests
import shutil
import json
import subprocess

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import openai
from whisper import Whisper
import openai_secret_manager

# function to manage file system, we need to create a directory for the content,  and delete it if it already exists


def manage_file_system(delete_existing=True):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    content_dir = os.path.join(root_dir, 'content')

    # delete the directory and all its contents
    if delete_existing and os.path.isdir(content_dir):
        shutil.rmtree(content_dir)

    # create content dir if it does not exist
    if not os.path.isdir(content_dir):
        os.mkdir(content_dir)
        os.chdir(content_dir)
    return content_dir

# function to initialize the Chrome driver with the capabilities


def initialize_driver():
    # Set up capabilities to enable performance logging
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    driver = webdriver.Chrome(desired_capabilities=caps)
    driver.get("https://learn.finops.org/path/finops-certified-professional")
    return driver

# function to find Sign In Button and click it


def do_login(driver):
    user_name = os.environ.get('user_name')
    password = os.environ.get('password')

    sign_in_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div/div[1]/div[1]/div[2]/div[2]/div/div/div/div[1]/p/strong/a')))
    sign_in_button.click()

    # Wait for page to load
    user_name_path = "/html/body/div/div[1]/div[2]/div/div/form/div/div[1]/input"
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, user_name_path)))

    # Login
    email_input = driver.find_element(By.XPATH, user_name_path)
    email_input.send_keys(user_name)

    password_input = driver.find_element(
        By.XPATH, "/html/body/div/div[1]/div[2]/div/div/form/div/div[2]/input")
    password_input.send_keys(password)

    login_button = driver.find_element(
        By.XPATH, "/html/body/div/div[1]/div[2]/div/div/form/div/div[4]/button")
    login_button.click()

    # Wait for page to load
    # WebDriverWait(driver, 10).until(EC.title_contains("Logged in"))


# function to find the course content
def find_content(driver):
    # get all sections
    all_sections = driver.find_element(
        By.XPATH, "/html/body/div/div[1]/div/div[4]/div[2]").text
    sections_list = all_sections.replace(
        '\n', ' ').replace('Complete ', '').split(' min ')
    return sections_list


def browse_sections(driver, sections_list, content_dir):
    # go through each section to find sub-sections
    for section_id in range(len(sections_list)):
        section = driver.find_element(
            By.XPATH, f"/html/body/div/div[1]/div/div[4]/div[2]/a[{section_id+1}]")
        section.click()  # Click on section to reveal content
        # Wait for page to load
        time.sleep(2)
        handle_section(driver, section_id, content_dir)


def handle_section(driver, section_id, content_dir):
    try:
        section_dir = f"{section_id + 1}-{driver.find_element(By.XPATH,'/html/body/div/div[1]/div[1]/div[2]/div/div/div[1]/h1').text}"
        section_dir = section_dir.replace(' ', '_')
        os.mkdir(section_dir)
        os.chdir(section_dir)
        # find each sub-section
        sub_sections = driver.find_element(
            By.XPATH, "/html/body/div/div[1]/div[2]/div/div/section[1]/div/div").text.split('\n')
        for sub_section_id in range(len(sub_sections)):
            sub_section = driver.find_element(
                By.XPATH, f"/html/body/div/div[1]/div[2]/div/div/section[1]/div/div/a[{sub_section_id + 1}]")
            # go through each sub-section
            section_path = os.path.join(content_dir, section_dir)
            handle_sub_sections(driver, sub_section, section_path)
        # after all subsections are done, go back to section
        os.chdir(content_dir)
        driver.back()

    except:
        # no sub section, break
        os.chdir(content_dir)
        driver.back()
        return


def handle_sub_sections(driver, sub_section, section_path):
    sub_section_name = sub_section.text
    sub_section.click()
    content_type = get_content_type(driver, sub_section_name)
    if content_type == 'video':
        handle_video_content(driver, section_path, sub_section_name)
    elif content_type == 'pdf':
        handle_pdf_content(driver)
    elif content_type == 'text':
        handle_text_content(driver, sub_section_name)
    # Save section content to file

    # go back to section
    driver.back()
    # go back to main
    os.chdir(section_path)


def get_content_type(driver, sub_section_name):
    page_source = driver.page_source
    # parse the page source using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    # find the 'a' tag with the href attribute containing the URL of the PDF
    pdf_link = soup.find('a', target="_blank")
    if pdf_link is not None:
        # get the URL of the PDF
        pdf_url = pdf_link['href']
        if pdf_url.find('.pdf') > -1:
            return 'pdf'

    # check if the subsection contains video based on the text
    if sub_section_name.find('Video') > -1:
        return 'video'
    else:
        return 'text'


def handle_text_content(driver, sub_section_name):
    # text only, save to file
    with open(f"{sub_section_name}.txt", "w", encoding="utf-8") as f:
        f.write(driver.find_element(By.XPATH,
                                    '/html/body/div/div[1]/div/div[2]/div/div/div[2]/div').text)


def handle_pdf_content(driver):
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
            pdf_filename = pdf_url.split('.pdf')[0].split(
                '/')[len(pdf_url.split('.pdf')[0].split('/'))-1]
            with open(f'{pdf_filename}.pdf', 'wb') as f:
                f.write(response.content)
                f.close()


def handle_video_content(driver, section_path, sub_section_name):
    # Set the name of the output file
    mp4_file = f"{sub_section_name}.mp4".replace(' ', '_').replace(':', '')

    # sub_section.click()
    # time.sleep(2)

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
                    # first download mp4 from m3u8 using ffmpeg
                    subprocess.run(
                        ['ffmpeg', '-i', m3u8_url, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', mp4_file])
                    # then transcribe text from video
                    transcribe_mp4_to_text(mp4_file)
                    # then extract slides from video
                    extract_slides_from_mp4(os.path.join(section_path, mp4_file))
                    break

# transcribe mp4 to text using open AI Whisper API
def transcribe_mp4_to_text(mp4_file):
 # convert mp4 to mp3
    mp3_file = mp4_file.replace('\\', '').replace('.mp4', '.mp3')
    subprocess.call(['ffmpeg', '-i', mp4_file.replace('\\', ''),
                    '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', mp3_file])

    openai.api_key = os.environ.get('open_ai_api')
    audio_file = open(mp3_file, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    # save to text, file
    with open(mp3_file.replace('.mp3', '.txt'), "w", encoding="utf-8") as f:
        f.write(transcript.text)
        f.close()

# extract slides from mp4 using slide-extractor cli tool
def extract_slides_from_mp4(mp4_file):
    mp4_folder = os.path.dirname(os.path.abspath(mp4_file))
    subprocess.call(['slide-extractor', '-p', mp4_file, mp4_folder])

def main():
    # initialize the driver
    driver = initialize_driver()

    # do login
    do_login(driver)

    # find content
    sections_list = find_content(driver)

    # manage file system
    content_dir = manage_file_system()

    # handle sections
    browse_sections(driver, sections_list, content_dir)

    driver.quit()

if __name__ == "__main__":
    main()
