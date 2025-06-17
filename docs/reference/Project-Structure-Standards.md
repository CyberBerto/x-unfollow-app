# Project Structure Standards

## 📁 Formal Project Structure Template

### **Core Project Architecture**
```
x-unfollow-app/
├── app.py                          # Main Flask application
├── api.py                          # X API integration layer
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Version control exclusions
├── README.md                       # Project overview and setup
├── venv/                           # Python virtual environment
├── static/                         # Frontend assets
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                      # Flask HTML templates
├── .claude/                        # Claude Code integration
│   ├── prompts/                    # Versioned prompt templates
│   ├── context/                    # Session context files
│   └── config/                     # Claude-specific configuration
├── scripts/                        # Development automation
│   ├── dev-setup.sh
│   ├── test-layer.sh
│   └── backup-dev-state.sh  
├── docs/                           # Documentation system
│   ├── active/                     # Current session files
│   ├── planning/                   # Development planning
│   ├── progress/                   # Progress tracking
│   ├── reference/                  # Core principles and standards
│   ├── technical/                  # Technical documentation
│   ├── templates/                  # Documentation templates
│   └── z-archive/                  # Historical files
└── tests/                          # Test suites (future)
    ├── test_layer_1.py
    ├── test_layer_2.py
    └── integration/
```

---

## 🔧 Environment-Specific Configuration

### **Configuration Management Pattern**
```python
# config.py - Environment-specific settings
import os
from dataclasses import dataclass

@dataclass
class Config:
    """Base configuration"""
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    X_CLIENT_ID: str = os.environ.get('X_CLIENT_ID')
    X_CLIENT_SECRET: str = os.environ.get('X_CLIENT_SECRET')
    DEBUG: bool = False

@dataclass 
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG: bool = True
    LOG_LEVEL: str = 'DEBUG'
    
@dataclass
class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG: bool = False
    LOG_LEVEL: str = 'INFO'
```

### **Environment File Structure**
```bash
# .env.example - Template for environment variables
SECRET_KEY=your-secret-key-here
X_CLIENT_ID=your-x-client-id
X_CLIENT_SECRET=your-x-client-secret
FLASK_ENV=development
LOG_LEVEL=DEBUG

# .env.development
SECRET_KEY=dev-secret-key
FLASK_ENV=development
LOG_LEVEL=DEBUG

# .env.production  
SECRET_KEY=production-secret-key
FLASK_ENV=production
LOG_LEVEL=INFO
```

---

## 📝 Structured Logging Best Practices

### **JSON Logging Format**
```python
# Enhanced logging with structured format
import json
import logging
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
    def log_code_change(self, file_path, function_name, change_type, reasoning):
        """Structured logging for code changes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "code_change",
            "file": file_path,
            "function": function_name,
            "change_type": change_type,
            "reasoning": reasoning,
            "layer": self._determine_layer(change_type),
            "session_id": self._get_session_id()
        }
        self.logger.info(json.dumps(log_entry))
        
    def log_layer_progress(self, layer_number, status, metrics=None):
        """Log layer implementation progress"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "layer_progress", 
            "layer": layer_number,
            "status": status,
            "metrics": metrics or {},
            "session_id": self._get_session_id()
        }
        self.logger.info(json.dumps(log_entry))
```

### **Log Organization Structure**
```
docs/technical/daily-logs/
├── 2025-06-15-code-changes.md      # Human-readable daily log
├── 2025-06-15-structured.json     # Machine-readable structured log
├── 2025-06-16-code-changes.md     # Next day human log
├── 2025-06-16-structured.json     # Next day structured log
└── logs-archive/                   # Compressed historical logs
    ├── 2025-06-week1.tar.gz
    └── 2025-06-week2.tar.gz
```

---

## 🤖 Claude Code Integration Standards

### **.claude/ Directory Structure**
```
.claude/
├── prompts/                        # Versioned prompt templates
│   ├── layer-implementation.xml    # Layer development prompts
│   ├── code-review.xml            # Code review prompts  
│   ├── debugging.xml              # Debugging prompts
│   └── documentation.xml          # Documentation prompts
├── context/                       # Session context management
│   ├── current-session.md         # Active session context
│   ├── layer-status.json          # Layer completion tracking
│   └── development-state.json     # Overall project state
└── config/                        # Claude-specific configuration
    ├── claude-config.json         # Claude Code settings
    └── prompt-templates.json      # Prompt template metadata
```

### **Prompt Template Example**
```xml
<!-- .claude/prompts/layer-implementation.xml -->
<prompt version="1.2" layer="2">
  <context>
    <project>X Unfollow App - Layer 2 Error Classification</project>
    <stack>Python Flask, JavaScript, Bootstrap</stack>
    <current_state>Layer 1 complete - basic batch flow working</current_state>
    <target_file>app.py around line 450</target_file>
  </context>
  
  <constraints>
    <layered_architecture>Must build on Layer 1 without breaking foundation</layered_architecture>
    <logging_required>All changes logged in daily-logs/YYYY-MM-DD-code-changes.md</logging_required>
    <testing>Must verify Layer 1 still works after changes</testing>
    <principles>Reference Development-Principles.md for all decisions</principles>
  </constraints>
  
  <success_criteria>
    <performance>30-50% reduction in batch completion time</performance>
    <classification>Accurate error type detection (free vs expensive)</classification>
    <user_experience>Clear indication of smart timing in UI</user_experience>
    <regression>No impact to existing Layer 1 functionality</regression>
  </success_criteria>
  
  <implementation_guidance>
    <approach>Add classify_unfollow_error() function after existing error handling</approach>
    <error_types>
      <free>not following, user not found, account suspended</free>
      <expensive>rate limits, network errors, unknown errors</expensive>
    </error_types>
    <timing>5-second wait for free errors, 15-minute wait for expensive errors</timing>
  </implementation_guidance>
</prompt>
```

---

## 🔄 Context Management Automation

### **Git Hooks Integration**
```bash
#!/bin/bash
# .git/hooks/post-commit - Auto-update context after commits

# Update development state
echo "$(date): Commit $(git rev-parse HEAD)" >> .claude/context/development-state.json

# Sync with documentation
if [[ $(git diff-tree --no-commit-id --name-only -r HEAD) == *"app.py"* ]]; then
    echo "Code changes detected - updating session context"
    python scripts/update-claude-context.py
fi
```

### **Automated Context Sync Script**
```python
# scripts/update-claude-context.py
import json
import os
from datetime import datetime

def update_development_state():
    """Update Claude context with current development state"""
    
    # Read current progress
    with open('docs/active/Quick-Session-Start.md', 'r') as f:
        session_content = f.read()
    
    # Extract layer information
    current_layer = extract_current_layer(session_content)
    
    # Update Claude context
    context = {
        "last_updated": datetime.now().isoformat(),
        "current_layer": current_layer,
        "session_status": "active",
        "priority_files": [
            "app.py",
            "docs/active/Quick-Session-Start.md", 
            "docs/reference/Development-Principles.md"
        ]
    }
    
    os.makedirs('.claude/context', exist_ok=True)
    with open('.claude/context/current-session.json', 'w') as f:
        json.dump(context, f, indent=2)
    
    print("✅ Claude context updated successfully")
```

---

## 📊 Development Analytics & Metrics

### **Progress Tracking Integration**
```json
{
  "project": "X Unfollow App",
  "layers": {
    "layer_1": {
      "status": "completed",
      "completion_date": "2025-06-12",
      "metrics": {
        "complexity_reduction": "71%",
        "lines_of_code_change": "365 → 105",
        "test_success_rate": "100%"
      }
    },
    "layer_2": {
      "status": "ready",
      "target_file": "app.py:~450",
      "expected_benefit": "30-50% batch time reduction"
    }
  },
  "development_velocity": {
    "avg_session_duration": "45 minutes",
    "documentation_ratio": "1:3 (code:docs)",
    "regression_rate": "0%"
  }
}
```

### **Quality Metrics Tracking**
- **Code Coverage**: Track test coverage as layers are implemented
- **Documentation Coverage**: Ensure all changes are documented
- **Performance Metrics**: Measure actual vs expected improvements
- **User Experience**: Track user feedback and usage patterns

---

## 🛡️ Security and Best Practices

### **Configuration Security**
- **Environment Variables**: Never commit secrets to version control
- **Secure Defaults**: Safe fallback values for all configuration options  
- **Access Control**: Proper file permissions for sensitive configuration
- **Audit Trail**: Log all configuration changes

### **Development Security**
- **Input Validation**: Validate all user inputs and API responses
- **Error Handling**: Don't expose sensitive information in error messages
- **API Security**: Proper OAuth 2.0 implementation with X API
- **Session Management**: Secure session handling and storage

---

## 🚀 Integration with Existing Workflow

This project structure enhances your existing layered development approach:

- **Preserves**: Your proven session management and documentation system
- **Enhances**: Adds professional structure and automation capabilities  
- **Integrates**: Works seamlessly with your existing "GO" and session commands
- **Scales**: Supports growth from Layer 1 through Layer 5 implementation

The structure follows your core principle: **systematic building on stable foundations** while adding modern development practices for long-term maintainability.