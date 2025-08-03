#  ExtractEase

**ExtractEase** is an intelligent text extraction and summarization tool designed to process both printed and handwritten documents.  
It uses **Paddle OCR** for OCR, **Mistral 7B** for text correction and summarization, and a **Flask** backend with a clean frontend interface.  
The extracted text can be summarized on demand, making it ideal for academic, professional, and personal use.

---

##  Features

- 📷 **Image Upload** – Upload printed or handwritten documents.
- 🔍 **Text Extraction** – Accurate OCR using Google Vision API.
- ✏ **Text Correction** – Refines extracted text using Mistral 7B.
- 📝 **Summarization** – Summarize extracted text with a single click.
- 💾 **User Authentication** – Secure login using MongoDB Atlas.
- 🌐 **Frontend Integration** – Real-time display of extracted and summarized text.
- 🖥 **Cross-Platform** – Works on web browsers (React.js / HTML+CSS+JS frontend).

---

## 🛠 Tech Stack

**Frontend:**  
- HTML, CSS, JavaScript

**Backend:**  
- Python, Flask  

**Database:**  
- MongoDB Atlas  

**AI/ML:**  
- Paddle (OCR)  
- Mistral 7B (Text correction & summarization) via Ollama

**Other Tools:**  
- PIL (image preprocessing)  
- 

---

## 📂 Project Structure

Extract_Ease/
├── Backend/
│ └── app.py
├── Frontend/
│ ├── images/
│ │ ├── backgrounds.jpg
│ │ └── logo.jpg
│ ├── first.html
│ ├── index.html
│ ├── recent.html
│ ├── signup.html
│ ├── upload.html
│ ├── script.js
│ ├── style.css
├── .env
├── requirements.txt



## ⚙ Installation & Setup

 1️.Clone the Repository
```bash
git clone https://github.com/your-username/ExtractEase.git
cd ExtractEase
2️.Create a Virtual Environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate    # On macOS/Linux
venv\Scripts\activate       # On Windows

**3️.Install Dependencies**
bash
Copy
Edit
pip install -r backend/requirements.txt

**4.Set Up Environment Variables**
Create a .env file in the backend folder:

ini
Copy
Edit
MONGO_URI=your_mongodb_atlas_connection_string
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_cloud_key.json
MISTRAL_API_KEY=your_huggingface_api_key
SECRET_KEY=your_flask_secret_key
5️ Run the Application
bash
Copy
Edit
cd backend
python app.py
The app will be available at: http://localhost:5000

 Usage
Login or Register using MongoDB authentication.

Upload an image containing printed or handwritten text.

Extracted text will be displayed in the frontend.

Click "Summarize" to get a short version of the extracted text.

Download or copy the results.


 Future Enhancements

 Multilingual OCR support.

 Mobile-friendly UI.

Question Answring Bot

 Contributing
Pull requests are welcome!
For major changes, please open an issue first to discuss what you would like to change.

 License
This project is licensed under the MIT License – see the LICENSE file for details.
