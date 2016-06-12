import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from config import *
from sshConnector import get_token
from random import randint
import sys, argparse

print('Welcome to Appliance Script')
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--providername",help="Add a Provider Name")
parser.add_argument("-host", "--providerhostname",help="Add a Provider Host Name")
parser.add_argument("-u", "--sproutuser",help="Add a Sprout User")
parser.add_argument("-p", "--sproutpass",help="Add a Sprout Password")
args = parser.parse_args()


if args.providername is not None:
    print('Adding a ' + args.providername + ' Provider Name')
if args.providerhostname is not None:
    print('Adding a ' + args.providerhostname + ' Provider Host Name')
if args.sproutuser is not None:
    print('Logging with ' + args.sproutuser + ' user')

if not args.providername:
    provider_name = default_provider_name
else:
    provider_name = args.providername

if not args.providerhostname:
    provider_hostname = default_provider_hostname
else:
    provider_hostname = args.providerhostname

if not args.sproutuser:
    sprout_user = default_sprout_user
else:
    sprout_user = args.sproutuser

if not args.sproutpass:
    sprout_pass = default_sprout_pass
else:
    sprout_pass = args.sproutpass


#Driver setup
driver = webdriver.Firefox()
# driver = webdriver.Remote(
#    command_executor='http://127.0.0.1:9515/wd/hub',
#    desired_capabilities=DesiredCapabilities.CHROME)
random_number = str(randint(0,10000))
driver.maximize_window()

def wait_until_element_loaded(element):
    delay = 3
    try:
        element_present = EC.presence_of_element_located((By.ID, element))
        WebDriverWait(driver, delay).until(element_present)
    except TimeoutException:
        print("Loading took too much time!")

def try_loaded(element_loaded):
    try:
        if element_loaded.__contains__(' '):
            pass
        elif element_loaded.__contains__('//'):
            element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, element_loaded)))
        else:
            element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, element_loaded)))
    except TimeoutException:
        print("Loading took too much time!")

def open_url(url, element_loaded = ' '):
    driver.get(url)
    time.sleep(1)
    try_loaded(element_loaded)

def click_element(element, element_loaded = ' '):
    driver.find_element_by_xpath(element).click()
    time.sleep(1)
    try_loaded(element_loaded)

def send_keys(element, key):
    element = driver.find_element_by_id(element)
    element.send_keys(key)

def is_element_exist(xpath):
    try:
        if driver.find_elements_by_xpath(xpath):
            return True
    except:
        return False

def substring_after(word, delim):
    return word.partition(delim)[2]

def get_pool_id():
    element = driver.find_element_by_xpath('//div[@class="alert alert-success alert-dismissible fade in"]')
    text_content = element.text
    return int(substring_after(text_content, "id "))

def get_url(pool_id):
    pool_id_num = 'pool-' + str(pool_id)
    element_id = "//div[@id='" + pool_id_num + "']//table[@class='table table-striped table-hover']//tbody/tr/td[4]"
    element = driver.find_element_by_xpath(element_id)
    text_content = element.text
    return text_content

def close_browser():
    driver.close()

# while not is_element_exist('//span[@class="pficon pficon-ok"]'):
#     time.sleep(5)
#     driver.refresh()

#Get Token
token = get_token(provider_hostname, 22, 'root', 'qum5net')
if token:
    token = token
else:
    token = default_token

#Open Browser and go to Sprout
open_url(sprout_url)
click_element('//a[@title="Login"]')
send_keys("inputUsername", sprout_user)
send_keys("inputPassword", sprout_pass)
click_element('//button[@class="btn btn-lg btn-primary btn-block"]')
click_element('//a[@href="/appliances/my"]','//h2[contains(text(),\'Listing and operation of your appliances\')]')

# Check if there are free appliances
if (is_element_exist('//h3[contains(text(),\'You reached the limit of your account, no more pools\')]')):
    close_browser()
    sys.exit('Appliance script failed: You are out of free pools')
else:
    pass

#Select stream
click_element('//span[@id ="select2-stream-container"]')
click_element('//li[contains(text(),\'downstream-56z\')]')
click_element('//input[@id="exp_default"]')

expiration_days_element = driver.find_element_by_id("exp_days")
expiration_days_element.clear()
expiration_days_element.send_keys(expiration_days)

expiration_hours_element = driver.find_element_by_id("exp_hours")
expiration_hours_element.clear()
expiration_hours_element.send_keys(expiration_hours)

click_element('//button[@class="btn btn-primary btn-lg"]')
driver.switch_to.alert.accept()

#Verify Appliance was created succesfully
pool_id = get_pool_id()
appliance_url = "https://" + get_url(pool_id)


#Open the created appliance
open_url(appliance_url)
send_keys("user_name", default_cfme_user)
send_keys("user_password", default_cfme_pass)
click_element('//a[@alt="Login"]','//p[@class="navbar__user-name"]')
time.sleep(1)

#Go to Compute --> Containers-->Providers
open_url(appliance_url + "/ems_container/show_list", 'search_text')
click_element('//button[@data-click="ems_container_vmdb_choice"]', '//a[@data-click="ems_container_vmdb_choice__ems_container_new"]')
click_element('//a[@data-click="ems_container_vmdb_choice__ems_container_new"]','//h1[contains(text(),\'Add New Containers Provider\')]')

send_keys("ems_name", provider_name)
click_element('//button[@data-id="ems_type"]', '//span[@class="text"]')
# click_element('//span[@class="text"]', '//span[@class="filter-option pull-left"]')
click_element('//span[contains(text(),\'OpenShift Enterprise\')]', '//span[@class="filter-option pull-left"]')
send_keys("default_hostname", provider_hostname)
send_keys("bearer_password", token)
send_keys("bearer_verify", token)
click_element('//button[@alt=\'Add\'][2]','//a[@data-click="ems_container_vmdb_choice__ems_container_new"]')

#delete the created Appliances
click_element("//a[contains(text(),'" + provider_name + "')]", "//a[contains(text()," + provider_name + ")]")
click_element('//button[@data-click="ems_container_vmdb_choice"]', '//a[@data-click="ems_container_vmdb_choice__ems_container_delete"]')
click_element('//a[@data-click="ems_container_vmdb_choice__ems_container_delete"]', )
driver.switch_to.alert.accept()
# wait_until_element_loaded(('dropdownMenu2'))
# assert is_element_exist("//strong[contains(text(),'Delete initiated')]")

close_browser()
print('Applance was added successfully')