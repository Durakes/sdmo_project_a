from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

driver_path = r'chromedriver.exe'

service = Service(driver_path)

driver = webdriver.Chrome(service=service)

url = "https://aserg-ufmg.github.io/why-we-refactor/#/projects"
driver.get(url)

time.sleep(5)

links = driver.find_elements(By.TAG_NAME, "a")

with open('selenium_links.txt', 'w') as file:
    for link in links:
        href = link.get_attribute('href')
        if href:
            file.write(href + '\n')

driver.quit()

print(f"Saved {len(links)} url links in selenium_links.txt")
