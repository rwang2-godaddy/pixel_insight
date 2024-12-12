# Pixel Insights Recommender

Pixel Insights is an innovative, AI-powered solution developed for **GoDaddy**, designed to empower Gen Z and Millennial users to discover their perfect domain name. By leveraging image-driven analysis and personalized recommendations, Pixel Insights transforms domain name searches into a fun, engaging, and productive journey.

## Local Run


1. Clone the repository
2. Connect to the VPN
3. Install the dependencies by running `pip3 install -r requirements.txt` (For installing gd_auth, you need to have access to GoDaddy artifacts. Ping a team member for help)
4. Authenticate to an AWS account which has access to GoCaaS 
5. Run `python app.py` launch image driven domain suggestion backend locally
6. Run `npm start` to start the frontend locally

## **How It Works**
### Design Diagram
<img width="1057" alt="Screenshot 2024-12-12 at 11 08 54 AM" src="https://github.com/user-attachments/assets/7b53dbd1-b1d0-41ec-b281-06f930038703" />


### 1. Image-Driven Domain Name Suggestions
- Users upload an image via the "Haven't decided on a domain yet?" button.
- The image is analyzed using **Amazon Rekognition** to labels and passed to **GPT-4 o Mini** model to, generate three personalized questions inspired by the visual content.
- User responses along with the image labels are processed by **GPT-4 o Mini** to produce five domain name suggestions.
- Each suggestion is evaluated and visualized with a radar graph based on **Domainality Dimensions** (e.g., emotional appeal, brand fit, and functional relevance).

### 2. Domainality Test
- For users without an image, the Domainality Test offers a series of thoughtful, multi-dimensional questions to uncover their ideal domain.
- Users can "Spill the Tea" by sharing their goals and intentions, providing deeper insights for tailored recommendations.



---

## **Technology Stack**

- **Frontend**: React-based UI for a seamless user experience.
- **Backend**: Flask based server to support image driven domain name generation and tests based domain name generation from two sepearte ports for this prototype
- **Image Processing**: **Amazon Rekognition** for extracting insights from uploaded images.
- **Language Processing**: **GPT-4 o Mini** LLM for generating personalized questions and domain suggestions.
- **Data Evaluation**: Suggestions evaluated against **Domainality Dimensions**.
- **APIs**: The current prototype get prices from **GPT-4 o Mini** model, for the productization plan, the Domain availability and pricing should be handled via **FIND APIs**.



## **Business Impact**

### Revenue Potential
- **Average Revenue per Search**: $0.894.
- **Targeted Improvement**: 5% conversion rate on searches without clear user intent (51,945 searches).
- **Projected Additional Daily Revenue**: $2,322.

### Strategic Value
- Enhances user engagement through visual and interactive tools.
- Bridges gaps in intent-based search conversions.

---

## **Future Roadmap**

<img width="1088" alt="Screenshot 2024-12-12 at 12 23 41 PM" src="https://github.com/user-attachments/assets/6002e177-2747-48ad-810e-20dad1e2e35a" />



1. **Enhanced Personalization**:
   - **Vector Database**: Storing text labels for enhanced recommendations.
   - **API Integration**: Integrating with **ReTiRe**,  **Gardrails** , **Vector DBs**  for more advanced personalization and convenient data retrieval. 
   - Incorporate data from **ReTiRe** and Pgen Vector DB, Aftermarket Vector DB for richer, more tailored suggestions.

2. **Social Insights Integration**:
   - Generate domain recommendations using insights from public profiles on Instagram and Pinterest.





