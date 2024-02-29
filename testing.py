import time
from dotenv import dotenv_values

config = dotenv_values(".env")
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
        if count<5:
            return gemini_json_response(count+1,prompt,text)
        else:
            return None
    return obj


def get_resume_information(resumeDetails):
    prompt='''Your task is to parse the resume details and give a json format which can be readily 
            converted into dict using json.loads in python and if there is no relevent information 
            found then use a empty string(""),. The output must be in the below format 
            {{"contactInformation":{{"Name":"", "email":"", "phone":"", "Linkedin":""}},
            "resumeHeadline":"mandatory field",
            "summary" : "", 
            "workingExperience" :[{{"Organization_name":"","role":"", "years_of_experience":"date or number"}}] (if available),
            "topSkills":[""](tools, frameworks, libraries, programming languages only),
            "education" : [{{"Institution_name":"","Degree":"", "Marks":"" ,"Completion_year":""}}],"Achievements":[""](if avaliable),
            "c
            ertifications":[""] (if available)
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
            "YearsOfExperienceRequired" : "",
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


text = extract_text('./resumes/sudh.pdf')["text"]
text = text.replace('\xa0', '')


resumeInfo = get_resume_information(text)
descriptionInfo = get_description_information(jd1)


def skill_compare(skills1,skills2):
    matching_skills=[]
    not_match_skills=[]
    for index,skill in enumerate(skills1):
        skills1[index]=skill.replace(" ","").replace("-","").replace(".","").lower()
    skills2=list(map(str.lower,skills2))
    for skill in skills2:
        skill_formated=skill.replace(" ","").replace("-","").replace(".","").lower()
        if skill_formated in skills1:
            matching_skills.append(skill)
        else:
            not_match_skills.append(skill)
    return {"match":matching_skills,"not_match":not_match_skills}

# Headline x Job Position Matching and Recommendation of adding/removing headline

def headline_match(headLine, jobPosition):
    jobPosition_formatted = jobPosition.replace(" ","").replace("-","").replace(".","").lower()
    headLine_formatted = headLine.replace(" ","").replace("-","").replace(".","").lower()

    if headLine_formatted in jobPosition_formatted:
        print("Objective Matching --> ", headLine)

# Must have skills Matching

print(skill_compare(resumeInfo["topSkills"], descriptionInfo["mustHaveSkills"]))

# Nice to have skills Matching

print(skill_compare(resumeInfo["topSkills"], descriptionInfo["niceToHaveSkills"]))

# Education Matching with streams mentioned JD (if applicable)

# Matching Certifications related to the skills in JD

# Suggestions of missed skills in the user Linked in profile