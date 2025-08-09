# 🚀 Merge Instructions: Social Media Content Creator Feature

This feature branch adds powerful social media content creation tools to your MCP server!

## 📋 What's New

### 🆕 New Tools Added:
1. **`create_social_post`** - Generate complete social media posts with images and text
2. **`get_slide_image`** - Find presentation-ready images for slides  
3. **`create_quote_card`** - Generate inspirational quote cards with backgrounds

### 📁 Files Modified/Added:
- ✅ `social_content_creator.py` - New module with content creation logic
- ✅ `server.py` - Added three new MCP tools
- ✅ `pyproject.toml` - Added `requests` dependency
- ✅ `.env.sample` - Added Unsplash API key configuration

## 🔧 API Integration

### Free APIs Used:
- **Quotable API** - Inspirational quotes (no key required!)
- **Unsplash API** - High-quality stock photos (optional key)
- **Lorem Picsum** - Fallback placeholder images (no key required)

### 🔑 Setup Required:
1. Copy `.env.sample` to `.env`
2. Add your Tavily API key (existing)
3. **Optional**: Add Unsplash API key for better images

## 🎯 How to Merge

### Option 1: GitHub PR Route (Recommended)
```bash
# Push the feature branch
git push origin feature/social-media-content-creator

# Then create a PR on GitHub:
# 1. Go to your GitHub repository
# 2. Click "Compare & pull request"
# 3. Add title: "Add Social Media Content Creator Tools"
# 4. Add description with the features list above
# 5. Request review if needed
# 6. Merge when ready
```

### Option 2: GitHub CLI Route
```bash
# Install GitHub CLI if not already installed
# brew install gh (on macOS)

# Create and merge PR directly
gh pr create --title "Add Social Media Content Creator Tools" --body "Adds create_social_post, get_slide_image, and create_quote_card tools to MCP server"
gh pr merge --merge  # or --squash or --rebase
```

### Option 3: Direct Merge (Local)
```bash
# Switch to main branch
git checkout main

# Merge the feature branch
git merge feature/social-media-content-creator

# Push to remote
git push origin main

# Clean up feature branch
git branch -d feature/social-media-content-creator
git push origin --delete feature/social-media-content-creator
```

## 🧪 Testing the New Features

After merging, test the tools:

```python
# Test social media post generation
create_social_post("artificial intelligence", "motivational")

# Test presentation images
get_slide_image("machine learning", "1920x1080")

# Test quote cards
create_quote_card("technology")
```

## 🔍 Troubleshooting

**Issue**: Import errors after merge
**Solution**: Install new dependencies with `uv sync`

**Issue**: Images not loading
**Solution**: Check if Unsplash API key is set (optional - will fallback to Lorem Picsum)

**Issue**: No quotes generated
**Solution**: Check internet connection (Quotable API is external)

## 🎉 Enjoy Your New Content Creation Powers!

Your MCP server now has powerful content creation capabilities that work with:
- ✅ Instagram posts
- ✅ LinkedIn content  
- ✅ Presentation slides
- ✅ Quote cards
- ✅ Social media automation

Happy creating! 🎨✨
