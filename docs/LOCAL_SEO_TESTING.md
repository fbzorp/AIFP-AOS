# Local SEO Testing Guide

This guide explains how to test SEO page generation during local development before deploying to production.

## Quick Start

### 1. Generate Test SEO Pages

```bash
# Run the test script
docker compose -f docker-compose.dev.yml exec -T api uv run python scripts/test_seo_generation.py
```

This will create:
- `./seo_pages/test-local-dev-001.html` - Sample SEO page
- `./seo_pages/sitemap.xml` - Google sitemap
- `./seo_pages/robots.txt` - Search engine directives

### 2. View Generated Pages Locally

**Windows:**
```bash
scripts\serve_seo_pages.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/serve_seo_pages.sh
./scripts/serve_seo_pages.sh
```

Then open: `http://localhost:8080/test-local-dev-001.html`

## Configuration

### Local Development (.env)
```bash
# Use production URL placeholder
SEO_PAGES_BASE_URL=https://aifinpay.io/blog
SEO_PAGES_OUTPUT_DIR=./seo_pages
SEO_INDEXNOW_KEY=
```

### Production (.env.production)
```bash
# Use production path
SEO_PAGES_BASE_URL=https://aifinpay.io/blog
SEO_PAGES_OUTPUT_DIR=/var/www/html/seo
SEO_INDEXNOW_KEY=your_indexnow_key
```

## What Gets Generated

### SEO Page Structure
- ✅ Proper HTML5 doctype
- ✅ Meta tags (title, description, keywords)
- ✅ Canonical URL
- ✅ JSON-LD structured data
- ✅ Semantic HTML structure
- ✅ Mobile-responsive viewport

### Sitemap.xml
- ✅ XML format for Google
- ✅ Lists all published SEO pages
- ✅ Auto-updated on each publish

### Robots.txt
- ✅ Allows indexing of /blog/
- ✅ Blocks /api/ and /admin/
- ✅ References sitemap.xml

## Testing Checklist

- [ ] HTML renders correctly in browser
- [ ] Meta tags are present and correct
- [ ] Canonical URL points to production domain
- [ ] JSON-LD structured data is valid
- [ ] Sitemap.xml is valid XML
- [ ] Robots.txt allows /blog/ crawling
- [ ] Pages are mobile-responsive

## Validation Tools

### HTML Validation
```bash
# Online validator
# https://validator.w3.org/
```

### Structured Data Testing
```bash
# Google Rich Results Test
# https://search.google.com/test/rich-results
```

### Sitemap Validation
```bash
# Online XML validator
# https://www.xml-sitemaps.com/validate-xml-sitemap.html
```

## Deployment Transition

When ready to deploy to VPS:

1. **Update .env.production:**
   ```bash
   SEO_PAGES_OUTPUT_DIR=/var/www/html/seo
   ```

2. **Deploy application:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

3. **Configure DNS:**
   - Point aifinpay.io to your VPS IP
   - Update Cloudflare if using proxy

4. **Verify production:**
   ```bash
   curl https://aifinpay.io/blog/sitemap.xml
   curl https://aifinpay.io/blog/robots.txt
   ```

## Alternative Testing Methods

### Ngrok (Temporary Public URL)
```bash
# Install ngrok from https://ngrok.com/
ngrok http 8080

# Update .env temporarily
SEO_PAGES_BASE_URL=https://abc123.ngrok.io/blog
```

### Cloudflare Tunnel (Persistent)
```bash
# Requires Cloudflare account
# Set up Zero Trust tunnel
# Use dev.aifinpay.io for testing
```

## Troubleshooting

### "No such file or directory" error
- Ensure `./seo_pages` directory exists
- The test script creates it automatically

### Pages not updating
- Delete old files in `./seo_pages`
- Run test script again

### Wrong URLs in generated pages
- Check `SEO_PAGES_BASE_URL` in .env
- Should be `https://aifinpay.io/blog` for production

## File Structure

```
AIFP-AOS/
├── seo_pages/              # Generated SEO files (local)
│   ├── test-local-dev-001.html
│   ├── sitemap.xml
│   └── robots.txt
├── scripts/
│   ├── test_seo_generation.py
│   ├── serve_seo_pages.bat
│   └── serve_seo_pages.sh
└── .env                    # Local configuration
```

## Next Steps

1. ✅ Test locally with generated files
2. ✅ Validate HTML and structured data
3. ✅ Plan VPS deployment
4. ✅ Configure production DNS
5. ✅ Deploy and verify production SEO pages
