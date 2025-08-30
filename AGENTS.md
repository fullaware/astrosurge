# AGENTS.md - Development Guidelines for AstroSurge

## 🚨 **CRITICAL SECURITY RULES**

### **NEVER Hardcode Sensitive Information**
- ❌ **NEVER** hardcode API keys, passwords, or connection strings
- ❌ **NEVER** commit `.env` files to version control
- ❌ **NEVER** expose database credentials in code
- ❌ **NEVER** hardcode URLs or endpoints that contain sensitive data

### **ALWAYS Use Environment Variables**
- ✅ **ALWAYS** use `os.getenv()` or `load_dotenv()` for configuration
- ✅ **ALWAYS** reference environment variables for sensitive data
- ✅ **ALWAYS** provide fallback values for non-critical configurations
- ✅ **ALWAYS** validate that required environment variables are set

## 🔐 **Environment Configuration**

### **Required Environment Variables**
```bash
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/asteroids

# API Configuration
API_BASE_URL=http://localhost:8000/api

# Development Settings
NODE_ENV=development
DEBUG=false

# Add any new API keys or secrets here
# API_KEY=your_api_key_here
# SECRET_KEY=your_secret_key_here
```

## 🗄️ **MongoDB Data Verification**

### **Always Use MongoDB MCP for Data Operations**
- ✅ **ALWAYS** use the MongoDB MCP (Model Context Protocol) for database operations
- ✅ **ALWAYS** verify data integrity through MCP queries before making changes
- ✅ **ALWAYS** use MCP for data exploration, validation, and troubleshooting
- ✅ **ALWAYS** rely on MCP for collection schema analysis and data counts

### **MongoDB MCP Best Practices**
```python
# ✅ CORRECT - Use MCP for data verification
# Use MCP to check collection contents before operations
# Use MCP to verify data structure and relationships
# Use MCP to monitor database performance and storage

# ❌ WRONG - Direct database manipulation without verification
# Don't assume data structure without MCP inspection
# Don't perform bulk operations without MCP validation
```

### **Common MCP Operations for Data Verification**
- **Collection Inspection**: Use MCP to examine collection schemas and indexes
- **Data Validation**: Use MCP to verify data integrity and relationships
- **Performance Monitoring**: Use MCP to check collection sizes and storage usage
- **Troubleshooting**: Use MCP to investigate data inconsistencies or errors

### **Environment File Setup**
1. Create a `.env` file in the project root
2. Add `.env` to `.gitignore` (already configured)
3. Use `.env.example` for documentation (create if needed)
4. Load environment variables using `python-dotenv`

## 🛡️ **Security Best Practices**

### **Database Security**
```python
# ✅ CORRECT - Use environment variables
connection_string = os.getenv("MONGODB_URI")
if not connection_string:
    raise ValueError("MONGODB_URI environment variable not set")

# ❌ WRONG - Hardcoded connection string
connection_string = "mongodb://localhost:27017/asteroids"
```

### **API Security**
```python
# ✅ CORRECT - Validate environment variables
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable not set")

# ❌ WRONG - Hardcoded API key
api_key = "sk-1234567890abcdef"
```

### **Frontend Configuration**
```python
# ✅ CORRECT - Use environment variables
api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# ❌ WRONG - Hardcoded URLs
api_base_url = "https://api.example.com"
```

## 🔧 **Development Workflow**

### **Adding New Environment Variables**
1. **Update `.env` file** with new variable
2. **Update this AGENTS.md** to document the variable
3. **Add validation** in your code to ensure it's set
4. **Provide fallback** values where appropriate

### **Code Review Checklist**
- [ ] No hardcoded credentials or API keys
- [ ] All sensitive data uses environment variables
- [ ] Environment variables are properly validated
- [ ] Fallback values are provided for non-critical configs
- [ ] No `.env` files are committed to version control
- [ ] MongoDB operations use MCP for data verification
- [ ] Data integrity is verified before bulk operations

### **Testing Environment Variables**
```python
# Test that required environment variables are set
def test_environment_configuration():
    required_vars = ["MONGODB_URI"]
    for var in required_vars:
        assert os.getenv(var), f"Missing required environment variable: {var}"
```

## 📁 **Project Structure**

### **Environment Files**
```
astrosurge/
├── .env                    # Local environment variables (gitignored)
├── .env.example           # Example environment file (committed)
├── .gitignore             # Already excludes .env files
└── AGENTS.md              # This file - development guidelines
```

### **Configuration Loading**
```python
# In Python files
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

# In shell scripts
source .env
export MONGODB_URI="mongodb://localhost:27017/asteroids"
```

### **MongoDB MCP Integration**
```python
# MCP provides safe database access and verification
# Use MCP for all database operations to ensure data integrity
# MCP handles connection management and error handling automatically
# MCP provides standardized interfaces for database operations
```

### **Flask WebUI Structure**
```
astrosurge/
├── web_ui.py              # Main Flask application
├── templates/             # Jinja2 HTML templates
│   ├── login.html         # User authentication
│   ├── company_setup.html # Company naming
│   └── dashboard.html     # Main dashboard
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   │   └── style.css      # Main CSS
│   └── js/                # JavaScript
│       └── dashboard.js   # Dashboard functionality
└── app_new.py             # FastAPI backend API
```

## 🚀 **Deployment Considerations**

### **Production Environment**
- Use production-grade environment variable management
- Consider using secrets management services
- Rotate credentials regularly
- Monitor for credential exposure

### **Docker Deployment**
```dockerfile
# ✅ CORRECT - Pass environment variables
ENV MONGODB_URI=${MONGODB_URI}

# ❌ WRONG - Hardcoded in Dockerfile
ENV MONGODB_URI=mongodb://localhost:27017/asteroids
```

### **Flask WebUI Deployment**
```bash
# ✅ CORRECT - Use environment variables
export FLASK_ENV=production
export FLASK_APP=web_ui.py
python3 web_ui.py

# ❌ WRONG - Hardcoded configuration
app.run(debug=True, host='0.0.0.0', port=3000)
```

## 📚 **Additional Resources**

### **Python Environment Management**
- [python-dotenv documentation](https://github.com/theskumar/python-dotenv)
- [Environment variable best practices](https://12factor.net/config)

### **Flask Development**
- [Flask documentation](https://flask.palletsprojects.com/)
- [Jinja2 templating](https://jinja.palletsprojects.com/)

### **Security Guidelines**
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security/security-advisories)

### **Project Documentation**
- See `docs/pid.md` for project overview
- See `README.md` for setup instructions
- See `.gitignore` for excluded files

## ⚠️ **Emergency Procedures**

If you accidentally commit sensitive information:
1. **IMMEDIATELY** revoke/rotate the exposed credentials
2. **NEVER** try to remove it from git history yourself
3. **Contact** the project maintainer immediately
4. **Document** the incident and lessons learned

---

**Remember: Security is everyone's responsibility. When in doubt, ask before committing!**
