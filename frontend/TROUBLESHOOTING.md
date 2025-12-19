# Troubleshooting React UI

## Common Issues

### 1. `Unexpected className prop` Error
**Status**: ✅ Fixed
**Cause**: `react-markdown` v9 removed support for the `className` prop.
**Fix**: We updated `App.jsx` to wrap the markdown component in a `div` with the class instead.

### 2. Backend Connection Failed
**Check**: Ensure `python app.py` is running.
**Fix**: Run `start_react_app.bat` to launch both services together.

### 3. Port Conflicts
**Check**: If ports 8000 or 5173 are busy.
**Fix**: Open Task Manager and kill python.exe or node.exe processes, then restart.

## How to Apply Fixes
Simply refresh your browser at `http://localhost:5173`. The development server handles updates automatically.
