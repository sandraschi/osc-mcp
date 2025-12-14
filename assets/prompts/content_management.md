# Content Management Guide - OSCMCP

## Content Creation Workflows

### Blog Posts
```
Workflow:
1. Create draft post
2. Add title, content, excerpt
3. Set categories and tags
4. Upload featured image
5. Configure SEO metadata
6. Preview
7. Publish or schedule

Best Practices:
- Clear, engaging titles (under 60 chars for SEO)
- Structured content (headings, lists, images)
- Internal/external links
- Alt text for images
- Meta description (under 160 chars)
```

### Pages (Static Content)
```
Use cases:
- About Us
- Contact
- Terms & Conditions
- Landing pages

Considerations:
- Permanent URLs (avoid changing)
- Parent-child hierarchies
- Template selection
- Navigation menu placement
```

### Media Management
```
Image Optimization:
- Resize before upload (max 2000px width)
- Compress (TinyPNG, ImageOptim)
- Use WebP format where supported
- Descriptive filenames (seo-friendly-name.jpg)
- Alt text for accessibility/SEO

Media Library:
- Organize in folders/categories
- Delete unused media
- Regular cleanup
- Backup important assets
```

## Content Operations

### Bulk Updates
```python
# Update multiple posts at once
bulk_update(
    content_type="post",
    filter={"category": "old-category"},
    updates={"category": "new-category", "status": "draft"}
)

Use cases:
- Recategorize content
- Update author
- Change status (publish → draft)
- Add/remove tags
- Update SEO metadata
```

### Content Migration
```
Platform-to-Platform:
1. Export from source (WordPress, Drupal, etc.)
2. Transform data (normalize structure)
3. Validate content
4. Import to target platform
5. Verify (check links, images, formatting)
6. Update SEO/permalinks
7. Test thoroughly

Common issues:
- Broken internal links (update after import)
- Missing media (re-upload)
- Format differences (fix markup)
- Permalink structure (configure redirects)
```

### Search & Filtering
```
Search by:
- Title, content, excerpt
- Author, date range
- Categories, tags, custom taxonomies
- Status (draft, published, scheduled)
- Custom fields/metadata

Advanced:
- Regex pattern matching
- Multiple criteria (AND/OR logic)
- Exclude criteria (NOT logic)
- Sort by date, title, views, etc.
```

## SEO Optimization

### On-Page SEO
```
Checklist:
✅ Keyword in title (near beginning)
✅ Keyword in first paragraph
✅ Keyword in H2/H3 headings
✅ Meta description with keyword
✅ Image alt text descriptive
✅ Internal links to related content
✅ External links to authoritative sources
✅ URL slug short and descriptive
✅ Content length appropriate (800+ words for in-depth)

Technical SEO:
✅ Mobile-responsive
✅ Fast page load (<3 seconds)
✅ HTTPS enabled
✅ XML sitemap updated
✅ Robots.txt configured
✅ Schema markup where appropriate
```

### Content Quality
```
Standards:
- Original, not duplicate
- Well-written, edited, proofread
- Proper formatting (paragraphs, headings, lists)
- Visual elements (images, videos, infographics)
- Scannable (short paragraphs, subheadings)
- Value-focused (helpful, informative, actionable)

Avoid:
- Keyword stuffing
- Thin content (<300 words without reason)
- Duplicate content
- Broken links
- Poor formatting
```

## Content Organization

### Taxonomy Strategy
```
Categories (broad):
- News
- Tutorials
- Product Updates
- Case Studies

Tags (specific):
- Feature names
- Technologies
- Locations
- Topics

Custom Taxonomies:
- Product lines
- Event types
- Content formats
- Difficulty levels
```

### Content Hierarchy
```
Site Structure:
Homepage
├── About
│   ├── Team
│   └── History
├── Services
│   ├── Service A
│   └── Service B
├── Blog
│   └── Posts (by category)
└── Contact

Benefits:
- Clear navigation
- Better UX
- SEO advantages (URL structure)
- Easier maintenance
```

## Multilingual Content

### Translation Workflow
```
1. Create content in primary language
2. Mark for translation
3. Translate (human or machine + human review)
4. Link translations (hreflang tags)
5. Configure language switcher
6. Test all language versions

Platforms:
- WordPress: WPML, Polylang
- Drupal: Content Translation
- Strapi: Internationalization (i18n)
```

## Content Scheduling

### Publishing Calendar
```
Strategy:
- Plan content weeks/months ahead
- Balance content types
- Coordinate with marketing campaigns
- Consider audience timezone
- Monitor performance, adjust schedule

Automation:
- Schedule posts in advance
- Auto-publish at optimal times
- Social media auto-posting
- Email newsletter triggers
- Content recycling (evergreen)
```

---

## Content Checklist

**Before Publishing**:
- ✅ Proofread and edited
- ✅ Images optimized and have alt text
- ✅ Links tested (internal and external)
- ✅ SEO metadata complete
- ✅ Categories/tags assigned
- ✅ Responsive on mobile
- ✅ Preview looks correct

**After Publishing**:
- ✅ Share on social media
- ✅ Submit to search engines (if new)
- ✅ Monitor for errors
- ✅ Track performance (views, engagement)
- ✅ Update as needed

---

**Austrian Quality**: Every piece of content represents your brand. Make it count! 🇦🇹

