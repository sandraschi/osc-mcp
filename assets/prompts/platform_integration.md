# Platform Integration Guide - OSCMCP

## WordPress Integration

### Setup
```
1. Enable REST API (default in WP 4.7+)
2. Install Application Passwords (WP 5.6+)
3. Configure permalinks (Settings → Permalinks)
4. Set user permissions appropriately
```

### Common Operations
```python
# WordPress REST API integration
wp = WordPress(url="https://site.com", auth=("user", "app_password"))

# Create post
wp.create_post(title="Title", content="Content", status="publish")

# Get posts
posts = wp.get_posts(category="news", per_page=10)

# Update post
wp.update_post(post_id=123, data={"title": "New Title"})

# Manage media
media = wp.upload_media(file_path="image.jpg")
```

### WordPress-Specific Features
- Custom post types and fields
- Shortcodes and blocks (Gutenberg)
- Plugin/theme management
- Multisite support
- WooCommerce integration

---

## Drupal Integration

### Setup
```
1. Enable JSON:API or RESTful Web Services module
2. Configure authentication (OAuth, Basic Auth)
3. Set content permissions
4. Configure content types
```

### Common Operations
```python
# Drupal JSON:API
drupal = Drupal(url="https://site.com", api_key="key")

# Create node (content)
drupal.create_node(
    type="article",
    title="Title",
    body="Content",
    field_tags=["tag1", "tag2"]
)

# Get content
nodes = drupal.get_nodes(content_type="article", status=1)

# Update node
drupal.update_node(nid=123, data={"title": "New Title"})
```

### Drupal-Specific Features
- Content entities and bundles
- Views for content queries
- Taxonomy and vocabularies
- Module system
- Multi-language support

---

## Ghost Integration

### Setup
```
1. Create Custom Integration (Settings → Integrations)
2. Get API keys (Content API + Admin API)
3. Configure webhooks (optional)
```

### Common Operations
```python
# Ghost Admin API
ghost = Ghost(url="https://site.com", admin_key="key")

# Create post
ghost.create_post(
    title="Title",
    html="<p>Content</p>",
    status="published",
    featured=False
)

# Get posts
posts = ghost.get_posts(filter="tag:news", limit=10)

# Manage members (if enabled)
ghost.add_member(email="user@example.com", name="Name")
```

### Ghost-Specific Features
- Membership/subscription system
- Newsletter integration
- Theme customization
- SEO and code injection
- Portal for members

---

## Strapi Integration (Headless CMS)

### Setup
```
1. Create API token (Settings → API Tokens)
2. Configure content types
3. Set permissions for API access
4. Enable endpoints
```

### Common Operations
```python
# Strapi REST API
strapi = Strapi(url="https://api.site.com", token="token")

# Create content
strapi.create_entry(
    collection="articles",
    data={"title": "Title", "content": "Content"}
)

# Get entries
articles = strapi.get_entries("articles", filters={"category": "news"})

# Update entry
strapi.update_entry("articles", id=123, data={"title": "New"})
```

### Strapi-Specific Features
- Custom content types
- GraphQL support
- Plugin marketplace
- Media library
- Internationalization (i18n)
- Role-based access control

---

## Platform Comparison

| Feature | WordPress | Drupal | Ghost | Strapi |
|---------|-----------|--------|-------|--------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Community** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **E-commerce** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Headless** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Multi-Platform Management

### Platform Selection Guide
```
Choose WordPress if:
- Traditional blog/website
- Large plugin ecosystem needed
- E-commerce (WooCommerce)
- Non-technical users

Choose Drupal if:
- Complex content relationships
- Enterprise requirements
- Advanced taxonomies
- Multi-site management

Choose Ghost if:
- Focus on blogging/newsletter
- Membership model
- Speed is critical
- Minimal, clean interface

Choose Strapi if:
- Headless CMS needed
- Custom content types
- Modern tech stack (React, Vue, etc.)
- API-first approach
```

### Cross-Platform Operations
```python
# Manage multiple CMSs from single interface
cms_manager = CMSManager()
cms_manager.add_platform("wordpress", wp_config)
cms_manager.add_platform("ghost", ghost_config)

# Publish to multiple platforms
cms_manager.publish_everywhere(
    title="Title",
    content="Content",
    platforms=["wordpress", "ghost"]
)

# Sync content across platforms
cms_manager.sync(source="wordpress", target="ghost", filters={"tag": "featured"})
```

---

## Integration Best Practices

**Security**:
- ✅ Use API tokens/application passwords (not main credentials)
- ✅ HTTPS only for API connections
- ✅ Rate limiting to prevent abuse
- ✅ Rotate API keys regularly
- ✅ Principle of least privilege (minimal permissions)

**Performance**:
- ✅ Cache API responses when appropriate
- ✅ Batch operations where possible
- ✅ Asynchronous operations for bulk tasks
- ✅ Monitor API rate limits
- ✅ Implement retry logic with backoff

**Reliability**:
- ✅ Error handling for API failures
- ✅ Logging all API operations
- ✅ Health checks for platform availability
- ✅ Backup before bulk operations
- ✅ Test in staging environment first

---

**Austrian Engineering**: One interface, multiple platforms, zero complexity! 🇦🇹

