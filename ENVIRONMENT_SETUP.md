# Environment Setup Guide

## Required API Keys

To run the Capsule Brain Supreme AGI, you need to set up the following environment variables:

### 1. Create a `.env` file

Create a `.env` file in the project root with the following content:

```bash
# Required API Keys
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ADMIN_TOKEN=your_secure_admin_token_here

# Application Configuration
APP_ENV=development
APP_PROFILE=local
```

### 2. Get Your DeepSeek API Key

1. Go to [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and replace `your_deepseek_api_key_here` in your `.env` file

### 3. Generate Admin Token

Generate a secure random token for admin access:

```bash
# Option 1: Using Python
python3 -c "import secrets; print('ADMIN_TOKEN=' + secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -base64 32

# Option 3: Using Node.js
node -e "console.log('ADMIN_TOKEN=' + require('crypto').randomBytes(32).toString('base64'))"
```

### 4. Complete .env File Example

```bash
# =============================================================================
# REQUIRED API KEYS
# =============================================================================

# DeepSeek API Key (Required for LLM functionality)
DEEPSEEK_API_KEY=sk-1234567890abcdef1234567890abcdef

# Admin Token (Required for sensitive operations)
ADMIN_TOKEN=cb_admin_1234567890abcdef1234567890abcdef

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

# Application Environment
APP_ENV=development
APP_PROFILE=local

# Alternative environment variable names (for compatibility)
ENVIRONMENT=development
ENV=development

# =============================================================================
# OPTIONAL CONFIGURATION
# =============================================================================

# API Host and Port (defaults to localhost:8000)
CB_API_HOST=localhost
CB_API_PORT=8000

# CORS Origins
ALLOW_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Telemetry
TELEMETRY_ENABLE=true
```

### 5. Security Notes

- **Never commit your `.env` file to version control**
- Keep your API keys secure and never share them
- Use strong, random admin tokens
- In production, use a secure secret management system
- Regularly rotate your API keys and admin tokens

### 6. Verify Setup

After setting up your `.env` file, you can verify the configuration:

```bash
# Test the environment setup
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('DeepSeek API Key:', '✅ Set' if os.getenv('DEEPSEEK_API_KEY') else '❌ Missing')
print('Admin Token:', '✅ Set' if os.getenv('ADMIN_TOKEN') else '❌ Missing')
print('App Environment:', os.getenv('APP_ENV', 'Not set'))
"
```

### 7. Start the Application

Once your `.env` file is configured:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python3 launch_capsule_brain.py
```

The application will be available at `http://localhost:8000`

## Troubleshooting

### Common Issues

1. **"DEEPSEEK_API_KEY not found in environment"**
   - Make sure your `.env` file exists in the project root
   - Check that the variable name is exactly `DEEPSEEK_API_KEY`
   - Restart the application after adding the key

2. **"Admin token not configured"**
   - Add `ADMIN_TOKEN=your_token_here` to your `.env` file
   - Generate a secure random token

3. **API endpoints returning 503**
   - This is normal when the engine isn't fully started
   - The GUI will work once the application is running

### Testing Your Setup

Run this test to verify everything is working:

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Test environment variables
deepseek_key = os.getenv('DEEPSEEK_API_KEY')
admin_token = os.getenv('ADMIN_TOKEN')

print('🔧 Environment Configuration Test')
print('=' * 40)
print(f'DeepSeek API Key: {\"✅ Set\" if deepseek_key else \"❌ Missing\"}')
print(f'Admin Token: {\"✅ Set\" if admin_token else \"❌ Missing\"}')
print(f'App Environment: {os.getenv(\"APP_ENV\", \"Not set\")}')

if deepseek_key and admin_token:
    print('\\n🎉 Configuration looks good!')
    print('You can now start the application with: python3 launch_capsule_brain.py')
else:
    print('\\n⚠️  Please check your .env file configuration')
"
```
