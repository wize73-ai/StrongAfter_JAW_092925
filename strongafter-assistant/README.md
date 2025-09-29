# StrongAfter Project

This project consists of a frontend Angular application and a backend Flask application for AI-powered book excerpt analysis and theme retrieval.

## Prerequisites

### System Requirements
- **Node.js**: Version 18.x or higher (for frontend)
- **npm**: Version 9.x or higher (comes with Node.js)
- **Python**: Version 3.8 or higher (for backend)
- **pip**: Latest version (for Python package management)

### API Access
- **Google Gemini API**: Required for AI features
- **OpenAI API** (optional): For alternative embedding generation

## Setup & Installation

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   
   # On Windows:
   # venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   You'll need to create a `.env` file with several environment variables. See the detailed **[Environment Variables & API Keys](#environment-variables--api-keys)** section below for complete setup instructions, including how to obtain all required API keys and credentials.
   
   For a quick start, create the `.env` file:
   ```bash
   touch .env
   ```
   
   Then follow the comprehensive setup guide in the Environment Variables section.

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Verify Angular CLI installation:**
   ```bash
   # If Angular CLI is not installed globally, install it:
   npm install -g @angular/cli
   
   # Verify installation
   ng version
   ```

## Environment Variables & API Keys

### Required Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

- **`GOOGLE_API_KEY`**: Your API key for Google Gemini
  - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Required for AI-powered theme analysis and content generation

- **`GOOGLE_CLOUD_PROJECT`**: Your Google Cloud Project ID
  - Required for Google Cloud services integration
  - Found in your Google Cloud Console dashboard

- **`PORT`**: Port number for the Flask application
  - Default: `5000`
  - Can be changed if port 5000 is already in use

- **`GOOGLE_CLOUD_LOCATION`**: Google Cloud region for your services
  - Example: `us-central1`, `us-east1`, `europe-west1`
  - Choose a region close to your users for better performance

- **`GOOGLE_APPLICATION_CREDENTIALS`**: Path to your Google Cloud service account key file
  - Required for Google Cloud authentication
  - Points to a JSON file containing service account credentials

- **`OPENAI_API_KEY`** (Optional): Your OpenAI API key
  - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
  - Used for alternative embedding generation methods

- **`FLASK_ENV`**: Set to `development` for local development
- **`FLASK_DEBUG`**: Set to `True` for debugging (development only)

### Example .env File

Create a `.env` file in the `backend` directory with the following content (replace with your actual values):

```env
# Google AI Studio API Key
GOOGLE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=my-strongafter-project-123456
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Flask Configuration
PORT=5000
FLASK_ENV=development
FLASK_DEBUG=True

# OpenAI Configuration (Optional)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Setting Up Required Accounts and Services

#### 1. Google AI Studio (for GOOGLE_API_KEY)

1. **Visit Google AI Studio:**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account

2. **Create an API Key:**
   - Click "Create API Key"
   - Choose "Create API key in new project" or select an existing project
   - Copy the generated API key
   - Add it to your `.env` file as `GOOGLE_API_KEY`

#### 2. Google Cloud Platform Setup

**Step 1: Create a Google Cloud Project**

1. **Visit Google Cloud Console:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Sign in with your Google account

2. **Create a New Project:**
   - Click "Select a project" at the top
   - Click "New Project"
   - Enter a project name (e.g., "strongafter-app")
   - Note the Project ID (this becomes your `GOOGLE_CLOUD_PROJECT`)
   - Click "Create"

**Step 2: Enable Required APIs**

1. **Navigate to APIs & Services:**
   - In the Google Cloud Console, go to "APIs & Services" > "Library"

2. **Enable the following APIs:**
   - Vertex AI API
   - AI Platform API
   - Cloud Resource Manager API

**Step 3: Create a Service Account**

1. **Navigate to IAM & Admin:**
   - Go to "IAM & Admin" > "Service Accounts"

2. **Create Service Account:**
   - Click "Create Service Account"
   - Enter a name (e.g., "strongafter-service-account")
   - Add description: "Service account for StrongAfter application"
   - Click "Create and Continue"

3. **Assign Roles:**
   - Add the following roles:
     - `AI Platform Developer`
     - `Vertex AI User`
     - `Storage Object Viewer` (if using Cloud Storage)
   - Click "Continue" then "Done"

4. **Create and Download Key:**
   - Click on your newly created service account
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose "JSON" format
   - Click "Create" - this downloads the JSON key file
   - Create a credentials directory in your backend folder:
     ```bash
     mkdir -p backend/credentials
     ```
   - Save the downloaded file as `backend/credentials/service-account-key.json`
   - Secure the file permissions:
     ```bash
     chmod 600 backend/credentials/service-account-key.json
     ```
   - Add the full path to this file as `GOOGLE_APPLICATION_CREDENTIALS` in your `.env`
   - Example: `GOOGLE_APPLICATION_CREDENTIALS=/home/username/projects/strongafter/backend/credentials/service-account-key.json`

**Step 4: Set Google Cloud Location**

1. **Choose a Region:**
   - Common regions: `us-central1`, `us-east1`, `us-west1`, `europe-west1`, `asia-southeast1`
   - Choose based on your location for better performance
   - Add this as `GOOGLE_CLOUD_LOCATION` in your `.env`

#### 3. OpenAI API Setup (Optional)

1. **Create OpenAI Account:**
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Sign up or sign in to your account

2. **Create API Key:**
   - Go to [API Keys](https://platform.openai.com/api-keys)
   - Click "Create new secret key"
   - Give it a name (e.g., "StrongAfter App")
   - Copy the generated key
   - Add it to your `.env` file as `OPENAI_API_KEY`

3. **Set up Billing (Required):**
   - Go to [Billing](https://platform.openai.com/account/billing)
   - Add a payment method
   - Set usage limits if desired

### Security Best Practices

1. **Keep your `.env` file secure:**
   - Never commit `.env` files to version control
   - The `.env` file is already in `.gitignore`
   - Use different `.env` files for different environments

2. **Service Account Key Security:**
   - Store the JSON key file outside your project directory if possible
   - Set appropriate file permissions: `chmod 600 service-account-key.json`
   - Consider using Google Cloud's Application Default Credentials in production

3. **API Key Management:**
   - Regularly rotate your API keys
   - Set up usage quotas and alerts
   - Monitor API usage in respective dashboards

### Verifying Your Setup

After setting up all environment variables, verify your configuration:

1. **Check your `.env` file:**
   ```bash
   cd backend
   cat .env  # Verify all variables are set
   ```

2. **Test Google Cloud authentication:**
   ```bash
   # Install Google Cloud CLI (if not already installed)
   # Then authenticate:
   gcloud auth application-default login
   
   # Verify project access:
   gcloud config set project YOUR_PROJECT_ID
   gcloud projects describe YOUR_PROJECT_ID
   ```

3. **Test the backend startup:**
   ```bash
   cd backend
   source venv/bin/activate
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GOOGLE_API_KEY:', 'Set' if os.getenv('GOOGLE_API_KEY') else 'Missing')"
   ```

## Running the Application

### Starting the Backend Server

1. **Ensure your virtual environment is activated:**
   ```bash
   # Navigate to backend directory
   cd backend
   
   # Activate virtual environment (if not already active)
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate    # Windows
   ```

2. **Start the Flask development server:**
   ```bash
   # Option 1: Using Flask directly (recommended for development)
   flask run
   
   # Option 2: Using Python directly
   python app.py
   
   # Option 3: Using Gunicorn (for production-like testing)
   gunicorn -w 4 -b 127.0.0.1:5000 app:app
   ```

3. **Verify the backend is running:**
   - The server will start on `http://127.0.0.1:5000` or `http://localhost:5000`
   - You should see output indicating the server is running
   - Test by visiting `http://localhost:5000` in your browser

### Starting the Frontend Development Server

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Start the Angular development server:**
   ```bash
   # Start development server
   ng serve
   
   # Or start with specific host/port
   ng serve --host 0.0.0.0 --port 4200
   
   # Or use npm script
   npm start
   ```

3. **Access the application:**
   - The frontend will be available at `http://localhost:4200`
   - The application will automatically reload when you make changes to the source files

### Running Both Services

For full functionality, you need both the backend and frontend running simultaneously:

1. **Terminal 1 - Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   flask run
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd frontend
   ng serve
   ```

3. **Access the application at:** `http://localhost:4200`

## Generating Embeddings

To process book excerpts and generate embeddings for theme retrieval:

1. **Ensure the backend environment is set up and activated:**
   ```bash
   cd backend
   source venv/bin/activate
   ```

2. **Prepare your content:**
   - Place source markdown files in `backend/resources/books/`
   - Update `backend/resources/book_urls.json` to map filenames to URLs

3. **Generate embeddings:**
   ```bash
   python generate_embeddings.py
   ```
   
   This creates/updates `backend/resources/generated/retrievals.json`

## Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
ng test
```

## Building for Production

### Frontend Production Build
```bash
cd frontend
ng build --configuration production
```

### Backend Production Deployment
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors:**
   - Ensure virtual environment is activated for backend
   - Run `pip install -r requirements.txt` again
   - For frontend, run `npm install` again

2. **API key errors:**
   - Verify your `.env` file is in the `backend` directory
   - Check that your API keys are valid and have proper permissions
   - Ensure no extra spaces or quotes around API keys

3. **Port already in use:**
   - Backend: Change port with `flask run --port 5001`
   - Frontend: Change port with `ng serve --port 4201`

4. **CORS errors:**
   - Ensure backend is running before starting frontend
   - Check that Flask-CORS is properly configured

5. **Google Cloud authentication errors:**
   - Verify your service account JSON file path is correct in `GOOGLE_APPLICATION_CREDENTIALS`
   - Check that the service account has the required roles
   - Ensure the JSON file has proper permissions: `chmod 600 service-account-key.json`

6. **"Project not found" or "Permission denied" errors:**
   - Verify your `GOOGLE_CLOUD_PROJECT` matches your actual project ID
   - Ensure required APIs are enabled in Google Cloud Console
   - Check that your service account has access to the project

7. **Environment variable not loading:**
   - Ensure your `.env` file is in the `backend` directory (not the root)
   - Check for typos in variable names
   - Restart the Flask server after changing `.env` file

## Project Structure (Overview)

-   `backend/`: Contains the Flask application, API endpoints, AI logic, and resource files.
    -   `app.py`: Main Flask application file.
    -   `utils/`: Helper modules (e.g., markdown parsing, embedding generation).
    -   `models/`: Data models (e.g., Excerpt, Theme).
    -   `resources/`: Static data, themes, book excerpts, generated embeddings.
    -   `requirements.txt`: Backend Python dependencies.
-   `frontend/`: Contains the Angular application.
    -   `src/`: Main source code for the Angular app.
        -   `app/`: Core application components and modules.
        -   `assets/`: Static assets like images and logos.
        -   `environments/`: Environment-specific configurations.
    -   `angular.json`: Angular CLI configuration.
    -   `package.json`: Frontend Node.js dependencies.
-   `README.md`: This file.

