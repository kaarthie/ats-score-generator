import time
from dotenv import dotenv_values
config = dotenv_values(".env")
import re
import pdf2image
import json
import pytesseract
import PyPDF2
# from langchain_community.llms import CTransformers
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import warnings
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

import sys
sys.path.append("/home/karthikeyanr/Desktop/integratedResumeParser/Resume_Analyzer/resumes")
from description import jd1
def gemini_json_response(count,prompt,text):
    print("Attempt ",count)
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=config["GEMINI_API_KEY"])
    prompt+="{text}"

    # If you have local model then use this commented lines
    # config = {'max_new_tokens': 4096, 'context_length': 4096, 'temperature':0.1}
    # llm = CTransformers(model="./models/gemma-7b.gguf", model_type="text-generator",temperature=0.1,config=config)

    tweet_prompt = PromptTemplate.from_template(prompt)
    tweet_chain = LLMChain(llm=llm, prompt=tweet_prompt, verbose=False)

    try:
        response = tweet_chain.run(text=text)
        # print(response)
        obj=json.loads(response)
        # print(obj)
    except Exception as e:
        print(e)
        if count < 5:
            return gemini_json_response(count+1,prompt,text)
        else:
            return None
    return obj


def get_resume_information(resumeDetails):
    prompt='''Your task is to parse the resume details and give a json format which can be readily 
            converted into dict using json.loads in python and if there is no relevent information 
            found then use a empty string(""),. The output must be in the below format 
            "basicInfo": {{"name" : "", location : "", "email" : "", "gitHub" : ""}},
            "resumeHeadline":"mandatory field",
            "summary" : "", 
            "workingExperience" :[{{"Organization_name":"","role":"", "years_of_experience":"date or number"}}] (if available),
            "topSkills":[""](tools, frameworks, libraries, programming languages only),
            "education" : [{{"Institution_name":"","Degree":"", "Marks":"" ,"Completion_year":""}}],"Achievements":[""](if avaliable),
            "certifications":[""] (if available),
            "totalYearsOfExperience" : "" (in number)
            }}. And don\'t use backticks or other special symbols in the output.'''
    text=f"The resume detail is :{resumeDetails}"
    return gemini_json_response(0,prompt,text)

def get_description_information(jobDescription):
    prompt='''Your task is to parse the job description details and give a json format which can be readily 
            converted into dict using json.loads in python and if there is no relevent information 
            found then use a empty string(""),. The output must be in the below format 
            {{"jobPosition":"mandatory field",
            "mustHaveSkills":[""](tools, frameworks, libraries only),
            "Summary" : "", 
            "YearsOfExperienceRequired" : "" (number only),
            "niceToHaveSkills":[""] (tools, frameworks, libraries only),
            "jobLocation"
            "streamOfEducation" : "" (if available),
            }}. And don\'t use backticks or other special symbols in the output.'''
    text=f"The Description detail is :{jobDescription}"
    return gemini_json_response(0,prompt,text)

def extract_text(path):
    pdfFileObj = open(path, 'rb')  #reading the file
    result=""
    is_image=False
    pdfReader = PyPDF2.PdfReader(pdfFileObj) 

    for pg in range(0,len(pdfReader.pages)):
        result+=pdfReader.pages[pg].extract_text()  #extracting text directly

    if (len(result)<=0):  # if no text found, use ocr
        print("It is an image resume")
        is_image=True
        pdfFileObj.seek(0)  
        images = pdf2image.convert_from_bytes(pdfFileObj.read())  #converting the file object into bytes 

        for pg, img in enumerate(images):
            result+=pytesseract.image_to_string(img) #extracting the text using the ocr

    pdfFileObj.close()

    return {"text":result,"is_image":is_image}

text = extract_text('./resumes/sahil.pdf')["text"]
text = text.replace('\xa0', '')
print(text)

def extract_years_from_experience(text):
    start_index = text.find("Experience")
    end_index = text.find("Education")
    experience_text = text[start_index:end_index]

    # Define a regular expression pattern to match years
    pattern = r'(\d+)\s+years?'

    # Find all matches of the pattern in the experience text
    matches = re.findall(pattern, experience_text)

    # Convert the matched years to integers and sum them up
    total_years = sum(int(year) for year in matches)

    return total_years


def skill_compare(skills1, skills2):
    matching_skills = []
    not_match_skills = []
    for index, skill in enumerate(skills1):
        skills1[index] = skill.replace(" ", "").replace("-", "").replace(".", "").lower()
    skills2 = list(map(str.lower, skills2))
    for skill in skills2:
        skill_formated = skill.replace(" ", "").replace("-", "").replace(".", "").lower()
        if skill_formated in skills1:
            matching_skills.append(skill)
        else:
            not_match_skills.append(skill)
    return {"matchingSkills": matching_skills, "notMatchSkills": not_match_skills}
# 
def headline_match(headline, jobPosition):
    jobPosition_formatted = jobPosition.replace(" ", "").replace("-", "").replace(".", "").lower()
    headline_formatted = headline.replace(" ", "").replace("-", "").replace(".", "").lower()
    lengthOfHeadline = len(headline);
# 
    # Length checking
    if len(headline.split(" ")) < 6:
        lengthSuggestion = 'Good LinkedIn headlines are 6-12 words and take advantage of the 120 character limit.'
    else :
        lengthSuggestion = 'Length of headline is good.'
# 
    # Special characters checking
    special_characters_count = sum(1 for char in headline if not char.isalnum())
    if special_characters_count > 2:
        specialCharactersSuggestion = "Your headline contains more than 2 special characters. Consider simplifying it for better readability."
    else:
        specialCharactersSuggestion = "Number of special characters in headline is acceptable."
# 
    # Headline Match Checking
    if headline_formatted in jobPosition_formatted or jobPosition_formatted in headline_formatted:
        objective = f"Fantastic job including '{jobPosition}' in your headline! This simple step can greatly improve your visibility to recruiters, making it easier for them to find you. Keep up the excellent work!"
    else:
        objective = f"We recommend including the exact title '{jobPosition}' in your headline. Recruiters frequently search by job titles and exact phrasing ranks higher in search results."                                                                                  
#    
    return {"length" : lengthSuggestion ,
            "headlineMatch": objective,
            "specialCharacters" : specialCharactersSuggestion,
            "sampleHeadline" : jobPosition}
# 
def education_match(resumeDegree, descriptionDegree):
    matching_degrees = []
    description_degree_formatted = descriptionDegree.replace(" ", "").replace("-", "").replace(".", "").lower()
    for degree_info in resumeDegree:
        resume_degree_formatted = degree_info['Degree'].replace(" ", "").replace("-", "").replace(".", "").replace(",", "").lower()
        if description_degree_formatted in resume_degree_formatted or resume_degree_formatted in description_degree_formatted:
            matching_degrees.append(descriptionDegree)
    return matching_degrees
# 
def complete_analysis(text, jd1):
    # Get resume and Job description information
    resumeInfo = get_resume_information(text)
    descriptionInfo = get_description_information(jd1)
# 
    # Perform skill comparison
    skill_comparison = {
        "mustHave": skill_compare(resumeInfo["topSkills"], descriptionInfo["mustHaveSkills"]),
        "niceToHave": skill_compare(resumeInfo["topSkills"], descriptionInfo["niceToHaveSkills"])
    }
    # 
    # Perform headline matching
    headline_matching = headline_match(resumeInfo["resumeHeadline"], descriptionInfo["jobPosition"])
    # 
    # Perform education matching
    education_matching = education_match(resumeInfo["education"], descriptionInfo["streamOfEducation"])
    print(resumeInfo["totalYearsOfExperience"])
    print(descriptionInfo["YearsOfExperienceRequired"])
    return {
        "Contact": resumeInfo["basicInfo"],
        "Skills": skill_comparison,
        "Headline": headline_matching,
        "Education Matching": education_matching
    }
# 
print(json.dumps(complete_analysis(text, jd1), indent=4))