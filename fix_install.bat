@echo off
echo Fixing installation...

echo Updating pip...
python.exe -m pip install --upgrade pip

echo Uninstalling conflicting packages...
pip uninstall openai langchain langchain-community langchain-openai -y

echo Installing compatible versions...
pip install openai==1.12.0
pip install langchain==0.1.0
pip install langchain-community==0.1.0
pip install langchain-openai==0.1.0
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install mysql-connector-python==8.1.0
pip install python-multipart==0.0.6
pip install python-dotenv==1.0.0
pip install PyPDF2==3.0.1
pip install python-docx==1.1.0
pip install bcrypt==4.1.2
pip install pyjwt==2.8.0
pip install python-magic==0.4.27
pip install python-magic-bin==0.4.14
pip install redis==5.0.1
pip install celery==5.3.6
pip install numpy==1.26.3
pip install requests==2.31.0

echo Done! You can now run the application.
pause