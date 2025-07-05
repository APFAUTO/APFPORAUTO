# Free Hosting Setup Guide

## Railway Deployment (Recommended - Free)

### Step 1: Prepare Your Repository
1. Make sure all files are committed to Git
2. Your repository should now have these new files:
   - `railway.json` - Railway configuration
   - `Procfile` - Tells Railway how to run your app
   - `runtime.txt` - Specifies Python version

### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect it's a Python app and deploy

### Step 3: Add Database (Free)
1. In your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Railway will automatically set the `DATABASE_URL` environment variable
4. Your app will automatically use this database

### Step 4: Set Environment Variables (Optional)
In Railway dashboard, go to your app's "Variables" tab and add:
- `SECRET_KEY`: A random string for Flask security
- `FLASK_ENV`: Set to `production`

### Step 5: Access Your App
- Railway will provide a URL like `https://your-app-name.railway.app`
- Your app will be live and accessible!

## Alternative Free Options

### Render (750 hours/month free)
1. Go to [render.com](https://render.com)
2. Connect your GitHub repo
3. Choose "Web Service"
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python app.py`

### PythonAnywhere (512MB RAM free)
1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Create free account
3. Upload your files via Files tab
4. Set up a web app pointing to your `app.py`

## Important Notes

### File Storage
- Railway and other cloud platforms don't provide persistent file storage
- Uploaded files will be temporary
- For production, consider using cloud storage (AWS S3, etc.)

### Database
- Railway provides free PostgreSQL database
- Your app will automatically migrate to use it
- Data persists between deployments

### Environment
- Set `FLASK_ENV=production` for security
- Add a strong `SECRET_KEY`
- Disable debug mode (already done in app.py)

## Troubleshooting

### Common Issues:
1. **Port issues**: App now uses `PORT` environment variable
2. **Database connection**: Check `DATABASE_URL` is set correctly
3. **File uploads**: Files are temporary on Railway

### Railway Logs:
- Check Railway dashboard for deployment logs
- Use `railway logs` command if using Railway CLI

## Cost
- **Railway**: 500 hours/month free (enough for personal use)
- **Render**: 750 hours/month free
- **PythonAnywhere**: Always free tier available

All options are completely free for your use case! 