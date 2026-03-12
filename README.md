**End to End Ecommerce Automation Pipeline**

PROJECT OUTLINE:
1. Pipeline maintains and updates 3 notion databases - Product Catalog (Also stores Inventory Status), Customer Relationship Management Log and Order Log
2. It then generates 2 personalised emails for each order and saves them in drafts:

      (i) A "thankyou for ordering" message along with the order reciept

      (ii) A cross-sell email suggesting what products to buy next based on the ordered item
3. Created a server using Render which can automate the pipeline with real time uptake of data

COMPONENTS AND WORKFLOW:
1. Ecommerce Automation Claude Skill- Created a skill in claude which updates the notion databases with each order and generates personalised emails.
2. ML Dataset Generator Claude Skill- Created a skill which creates sample input dataset in all common dataset input formats, specially trained for ecommerce orders in .json format
3. APIs used and their working:

   Gemini API Key - Google AI Studio - For generating personalised email text

   GMail API Key - Google Cloud Console - Used to connect Claude skill setup with gmail - OAuth 2.0 client

   FastAPI - Used for server deployment on Render
5. Website Deployment using Render: After these APIs had started working, a website was deployed using FastAPI which hosted the above tasks on internet, instead of the machine locally.

SIGNIFICANCE OF EACH FILE:
1. credentials.json - Stores the credentials for the OAuth 2.0 client, registers our system in Google ecosystem
2. token.json - Unique token generated when GMail API starts working successfully, expires every 7 days (testing mode expiry)
3. auth.py - Automatically generates the token.json file when it expires
4. main.py - Main python script, integrates all the 3 APIs with each other, creates drafts in gmail with personalized messages and connects 1 port with Render
5. requirements.txt - List of dependencies Render needs to install to deploy our website
6. models.py - Defines the shape of the .json input file, so it is easy for FastAPI to read or reject.
7. render.yaml - Defines rules for the Render environment, automates the whole Render setup process
