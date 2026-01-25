# Troubleshooting Guide

## CORS Errors

If you see "Access-Control-Allow-Origin" errors:

1. **Make sure backend is running on port 5001** (not 5000):
   ```bash
   cd webapp/backend
   python3 app.py
   ```
   You should see: "Starting Flask server on http://0.0.0.0:5001"

2. **Clear browser cache** or do a hard refresh:
   - Chrome/Edge: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Firefox: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

3. **Restart the Vite dev server**:
   ```bash
   cd webapp/frontend
   # Stop the server (Ctrl+C) and restart:
   npm run dev
   ```

4. **Check that Vite proxy is configured correctly**:
   - Open `webapp/frontend/vite.config.js`
   - Should have: `target: 'http://localhost:5001'`

5. **Verify backend is accessible**:
   ```bash
   curl http://localhost:5001/api/health
   ```
   Should return: `{"status":"ok",...}`

## Port 5000 Already in Use

Port 5000 is often used by AirPlay on macOS. The app now uses port 5001 by default.

To use a different port:
```bash
PORT=5002 python3 app.py
```

## "Failed to fetch" Error

This usually means:
1. Backend is not running - start it with `python3 app.py`
2. Wrong port - make sure backend is on 5001
3. Firewall blocking - check your firewall settings

## File Upload Issues

- Maximum file size: 500MB (configurable in `app.py`)
- Make sure files are in correct format:
  - Students: .xlsx or .xls
  - Timetable: .xlsx or .xls
  - Photos: .zip file
  - Logo/Signature: .png, .jpg, or .jpeg

## Still Having Issues?

1. Check browser console for detailed error messages
2. Check backend terminal for Python errors
3. Verify all dependencies are installed:
   ```bash
   cd webapp/backend
   python3 -m pip install -r requirements.txt
   ```
