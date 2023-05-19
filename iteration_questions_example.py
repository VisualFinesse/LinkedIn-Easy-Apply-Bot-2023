from selenium import webdriver

driver = webdriver.Chrome()

# Open the webpage
driver.get('https://www.website.com')

# Find the HTML elements by their respective tags
inputs = driver.find_elements_by_tag_name('input')
labels = driver.find_elements_by_tag_name('label')
buttons = driver.find_elements_by_tag_name('button')
legends = driver.find_elements_by_tag_name('legend')

# Answer the questions accordingly
for input in inputs:
    if input.get_attribute('type') == 'text':
        if input.get_attribute('id') == 'single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3545714079-4470919117355239022-text':
            input.send_keys('John Doe')
        elif input.get_attribute('id') == 'single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-3545714079-5717872389822591142-text':
            input.send_keys('$100,000')

for label in labels:
    if label.get_attribute('for') == 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(3545714079,8263771393388251360,multipleChoice)-0':
        label.click()
    elif label.get_attribute('for') == 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(3545714079,3260899347599232760,multipleChoice)-0':
        label.click()
    elif label.get_attribute('for') == 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(3545714079,5597309485646917590,multipleChoice)-1':
        label.click()

for button in buttons:
    if button.get_attribute('type') == 'submit':
        button.click()

for legend in legends:
    if legend.text == 'Are you 18 years of age or older?':
        legend.click()
    elif legend.text == 'Are you legally eligible and authorized to work in the United States?':
        legend.click()
    elif legend.text == 'Will you now or in the future require sponsorship for visa employment status (e.g., H-1B visa status)?':
        legend.click()

# Close the webdriver
driver.quit()
