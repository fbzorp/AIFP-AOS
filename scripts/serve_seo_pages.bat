@echo off
echo Starting local web server for SEO pages...
echo SEO pages will be available at: http://localhost:8080
echo Press Ctrl+C to stop the server
echo.
cd seo_pages
python -m http.server 8080
