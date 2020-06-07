"""You will need to install the chrome webdriver (or any other preferred webdriver)
before being able to use this program"""


# Imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import json
import csv
import string
import time

# Initialize variables
total_jobs = []
terms = {}

# Authentication
USERNAME = "TYPE IN YOUR USERNAME HERE"
PASSWORD = "TYPE IN YOUR PASSWORD HERE"



"""Reads in all the terms from the skills.csv file.
Write your own terms - each a single word and only one per line.
Look at the skills.csv as an example."""

with open("skills.csv", "r") as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        terms[row[0]] = 0

# Selenium driver
driver = webdriver.Chrome('./chromedriver')

# First time scraping for log in auth
first = True


"""Before running the script, populate searches.csv with the links of your choice.
Keep close attention to how the links are gathered. Do the following:
1. Search a phrase like "software engineer intern"
2. Go to page 2
3. You should get a link like: https://www.glassdoor.com/Job/san-francisco-software-engineer-intern-jobs-SRCH_IL.0,13_IC1147401_KE14,38_IP2.htm
4. Get rid of the "_IP2
5. Paste the link in searches.csv
6. Do steps 1-5 for whatever search results you want."""

with open("searches.csv", "r") as file:
    # Reads the csv file
    csv_reader = csv.reader(file)

    # Reads through each row in the csv file
    for row in csv_reader:
        # Creates the link because csv forms array from terms separated by commas
        ## Combine the array elements with a comma to form the link
        link = ','.join(row)

        # Open the link using selenium webdriver
        driver.get(link)
        
        # If it is the first time, then selenium does authentication
        if first:

            # Lets user enter y to make sure there is no captcha at the beginning
            confirm_continue = ""
            while confirm_continue != "y":
                user_input = input("Type 'y' when you can continue after doing the captcha (if necessary)")
                confirm_continue = user_input
            
            # Clicks the sign in button
            signin = driver.find_element_by_class_name("sign-in")
            signin.click()

            # Waits for 10 seconds or the page to load, whichever comes first
            driver.implicitly_wait(10)

            # Types in the username provided at the top of the script
            email = driver.find_element_by_name("username")
            email.send_keys(USERNAME)

            # Types in the password provided at the top of the script
            password = driver.find_element_by_name("password")
            password.send_keys(PASSWORD)

            # Clicks submit to log in
            submit = driver.find_element_by_name("submit")
            submit.click()

            # No longer first time scripting
            first = False
        
        # Reads the page that selenium webdriver opened for scraping
        page = driver.page_source

        # Beautiful Soup to parse the html of the page
        soup = BeautifulSoup(page, features="html.parser")

        # Finds all the classes jobLink on the page
        jobs = soup.findAll("a", {"class": "jobLink"})

        # Gets all the job links on the page
        jobs = [job['href'] for job in jobs]

        # Appends to the array that is populating all the jobs
        for job in jobs:
            total_jobs.append(job)

        # Scrapes through the rest of the pages from the search result
        for i in range(2,int(driver.find_element_by_class_name("padVertSm").text[10:]) + 1):
            # Goes to the link of each page result by concatenating the link
            driver.get(link[:-4] + '_IP=' + str(i) + link[-4:])
            
            # Reads the page that selenium webdriver opened for scraping
            page = driver.page_source

            # Beautiful Soup to parse the html of the page
            soup = BeautifulSoup(page, features="html.parser")

            # Finds all the classes jobLink on the page
            jobs = soup.findAll("a", {"class": "jobLink"})

            # Gets all the job links on the page
            jobs = [job['href'] for job in jobs]

            # Appends to the array that is populating all the jobs
            for job in jobs:
                total_jobs.append(job)

# There are three links for each job, so this removes all the duplicate links
total_jobs = total_jobs[0::3]

# Writes to the csv file: jobs.csv all the unique job links
## Includes some unusable links, but the code will not read them later on
with open("jobs.csv", "w") as file:
    csv_writer = csv.writer(file)
    for job in total_jobs:
        csv_writer.writerow([job])


# Reads the csv file with all the job links
with open("jobs.csv", "r") as file:
    # Reads the file
    csv_reader = csv.reader(file)

    # Each row has a unique job link
    for row in csv_reader:
        # Creates the link because csv forms array from terms separated by commas
        ## Combine the array elements with a comma to form the link
        link = ','.join(row)

        # Makes sure that the link is usable and is a glassdoor job posting
        if "glassdoor" in link:
            # Tries to run following code unless there is an error along the way
            try:
                driver.get(link)
                driver.implicitly_wait(10)
                page = driver.page_source
                soup = BeautifulSoup(page)

                # Gets the description of the job posting
                description = driver.find_element_by_class_name("desc").text

                # Joins the description into one string
                description = "".join(description)

                # The following three lines of code helps join the description into readable string
                empty = ""
                for c in description:
                    empty += c
                
                # Splits the description by words
                description = empty.split()

                # Loops through the words in the description
                for word in description:
                    # Punctuation array
                    punctuation = [",","'", '"', ":", ";"]

                    # Makes each word lowercase
                    word = word.lower()

                    # Gets rid of the punctuation from the array above in each word
                    word = ''.join(ch for ch in word if ch not in punctuation)

                    # Checks to see if word is part of the words that user entered in skills.csv
                    if word in terms.keys():
                        print(word)
                        terms[word] = terms[word] + 1

            # Goes here if there is an error
            except:
                # Checks to see if the error is because the job posting is expired
                try:
                    # Finds the error message if there is one
                    error_msg = driver.find_element_by_class_name("description").text
                    if "This job has expired" in error_msg:
                        # Gets rid of the link from all the job links
                        total_jobs.pop(0)
                        # Continues the loop
                        continue
                # Goes here if the error is not a job posting expired
                ## Most likely glassdoor noticed scraping and there is a captcha :(
                except:
                    # Sorts the skills based on most commonly found
                    sorted_terms = sorted(terms.items(), key=lambda x: x[1], reverse=True)

                    # Dumps the terms in a json file
                    json_object = json.dumps(sorted_terms, indent = 4)
                    with open("terms.json", "w") as termsfile:
                        termsfile.write(json_object)

                    # Adds all the links that were not used to the remaining_jobs.csv file so
                    # user does not have to run the file all over again from the start
                    with open("remaining_jobs.csv", "w") as file:
                        csv_writer = csv.writer(file)
                        for job in total_jobs:
                            csv_writer.writerow([job])

                    # Quits the program
                    exit()

            # After every loop, gets rid of the link from all job links 
            # to show that it has been parsed
            total_jobs.pop(0)


# Sorts the skills based on most commonly found
sorted_terms = sorted(terms.items(), key=lambda x: x[1], reverse=True)

# Dumps the terms in a json file
json_object = json.dumps(sorted_terms, indent = 4)
with open("terms.json", "w") as termsfile:
    termsfile.write(json_object)
