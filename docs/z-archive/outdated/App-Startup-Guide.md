# App Startup Guide

*Quick reference for starting the X Unfollow app when opening Claude sessions*

## 🚀 Essential Startup Command

**Navigate to project folder and start app:**
```bash
cd /Users/bob/Documents/projects/x-unfollow-app
source venv/bin/activate && python app.py
```

## 📋 Pre-Session Checklist

### Required Before Testing
- [ ] **Start Flask app** using command above
- [ ] **Verify app is running** at http://127.0.0.1:5001
- [ ] **Login to X** through the app interface
- [ ] **Load CSV file** with usernames to test

### App Status Indicators
- ✅ **App running**: Terminal shows "Running on http://127.0.0.1:5001"
- ✅ **Authentication**: Dashboard shows your @username
- ✅ **Ready for testing**: CSV list loaded and users selectable

## 🔧 Quick Test Process

1. **Upload CSV file** with 2-3 test usernames
2. **Select accounts** using checkboxes  
3. **Click "Test Batch"** (max 5 accounts)
4. **Monitor progress** in the operations section

## 📁 CSV File Format

**Simple format** (save as .csv):
```
username1
username2
username3
```

**Location**: Any local folder, upload via web interface

## ⚠️ Important Notes

- **Virtual environment required**: Always use `source venv/bin/activate`
- **Port 5001**: App runs on localhost:5001, not 5000
- **Rate limits**: Test batches respect 15-minute intervals  
- **Browser refresh**: May need to refresh if app was restarted

---

**Quick Copy-Paste Command:**
```bash
cd /Users/bob/Documents/projects/x-unfollow-app && source venv/bin/activate && python app.py
```

*Keep this tab open during development sessions for easy reference*