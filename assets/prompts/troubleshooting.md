# Troubleshooting Guide - OSCMCP

## Connection Issues

### Problem: Cannot connect to CMS platform

**Solutions**:
1. ✅ Verify CMS URL is correct and accessible
2. ✅ Check API credentials (token, password)
3. ✅ Confirm REST API enabled on CMS
4. ✅ Test with curl or Postman first
5. ✅ Check firewall/network access
6. ✅ Verify HTTPS certificate valid

### Problem: Authentication failures

**Checklist**:
- Correct username/API token
- Token not expired
- User has required permissions
- API authentication method enabled
- Application passwords enabled (WordPress)

## Content Operations Issues

### Problem: Cannot create/update content

**Solutions**:
- ✅ User has publish/edit permissions
- ✅ Required fields provided
- ✅ Content type exists
- ✅ No validation errors (check CMS logs)
- ✅ No conflicting plugins

### Problem: Media upload fails

**Common causes**:
- File too large (check upload_max_filesize)
- Invalid file type (not in allowed types)
- Permissions on uploads directory
- Disk space full
- Memory limit exceeded (php memory_limit)

**Solutions**:
- Resize/compress files before upload
- Check CMS settings for upload limits
- Verify file type in whitelist
- Free disk space
- Increase PHP limits if admin access

## API Rate Limiting

### Problem: Too many requests error (429)

**Solutions**:
- Implement exponential backoff
- Reduce request frequency
- Use batch operations
- Cache responses
- Check CMS rate limit settings

### Problem: Slow API responses

**Causes & Solutions**:
- Large result sets → Use pagination
- Complex queries → Optimize filters
- CMS server overloaded → Scale resources
- Network latency → Use CDN, optimize connection
- Plugin conflicts → Disable/debug plugins

## Platform-Specific Issues

### WordPress
```
Common issues:
- Permalinks not updated (Settings → Permalinks → Save)
- Plugin conflicts (disable to test)
- Theme compatibility issues
- Database optimization needed
- Memory limits (wp-config.php)
```

### Drupal
```
Common issues:
- Cache not cleared (drush cr)
- Module dependencies missing
- Permissions misconfigured
- Database updates needed (drush updb)
- Views cache issues
```

### Ghost
```
Common issues:
- Theme compatibility
- Member features not enabled
- Newsletter not configured
- Database migration needed
- Storage adapter issues
```

### Strapi
```
Common issues:
- Content type changes require restart
- Permissions not configured
- Plugin conflicts
- Database connection lost
- Build errors (admin panel)
```

## OSCMCP Server Issues

### Problem: MCP server won't start

**Checklist**:
1. Python 3.8+ installed
2. Dependencies: `pip install -r requirements.txt`
3. Configuration file valid
4. Ports not in use
5. Check server logs

### Problem: Commands timeout

**Solutions**:
- Increase timeout settings
- Check CMS responsiveness
- Verify network connection
- Monitor CMS server resources
- Optimize queries/operations

## Data Issues

### Problem: Content formatting broken after import

**Solutions**:
- ✅ Check HTML/markdown conversion
- ✅ Verify special characters encoding (UTF-8)
- ✅ Fix broken shortcodes/embeds
- ✅ Update internal links
- ✅ Reprocess media

### Problem: Missing content after migration

**Debug**:
1. Check source export completeness
2. Verify import logs for errors
3. Compare source vs target counts
4. Check for filtering/exclusions
5. Validate content type mapping

## Performance Troubleshooting

### Slow Content Loading

**Optimize**:
- Enable caching (object cache, page cache)
- Optimize database queries
- Use CDN for static assets
- Compress images
- Minify CSS/JS
- Enable gzip compression

### High Server Load

**Solutions**:
- Identify problematic plugins/modules
- Optimize database (indexes, cleanup)
- Implement caching layers
- Scale server resources
- Use load balancing if needed

## Security Issues

### Problem: Unauthorized access attempts

**Actions**:
- Change API credentials immediately
- Review user permissions
- Check access logs
- Enable 2FA if available
- Implement IP whitelisting
- Rate limit authentication attempts

### Problem: Suspicious content changes

**Investigate**:
- Review user activity logs
- Check for compromised accounts
- Scan for malware/backdoors
- Restore from known-good backup
- Update all software immediately
- Change all credentials

## Emergency Procedures

### Site Down
```
Priority order:
1. Check server status (hosting, VPS)
2. Check CMS application (PHP, database)
3. Check database connectivity
4. Review error logs
5. Restore from backup if needed
6. Contact hosting support
```

### Data Loss
```
Recovery:
1. Don't panic - stop all operations
2. Check available backups (most recent)
3. Assess extent of loss
4. Restore from backup
5. Verify restoration
6. Identify cause to prevent recurrence
```

## Diagnostic Tools

### Health Check
```python
# Check CMS connectivity
status = check_cms_health(platform="wordpress")

# Verify API access
api_status = test_api_connection()

# Database check
db_status = check_database_status()
```

### Logging
```
Enable debug logging:
- OSCMCP server logs
- CMS platform logs (error.log, access.log)
- Web server logs (Apache, Nginx)
- Database logs

Review for:
- Error messages
- Slow queries
- Failed operations
- Security warnings
```

## Getting Help

**In Order**:
1. This troubleshooting guide
2. OSCMCP documentation (README.md, docs/)
3. Platform-specific documentation (WordPress Codex, Drupal.org, etc.)
4. Community forums
5. Professional support
6. GitHub Issues (for OSCMCP-specific problems)

**When Reporting**:
- CMS platform and version
- OSCMCP version
- Python version
- Error messages (exact text)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs

---

## Prevention Best Practices

**Daily**:
- Monitor error logs
- Check backup status
- Verify critical functions
- Review security alerts

**Weekly**:
- Update plugins/modules
- Optimize database
- Review performance metrics
- Test backup restoration

**Monthly**:
- Update CMS core
- Security audit
- Content audit (remove old/outdated)
- Performance review

**Before Major Changes**:
- Create full backup
- Test in staging environment
- Document changes
- Have rollback plan
- Schedule during low-traffic time

---

**Austrian Reliability**: Prevent problems through preparation, solve issues systematically! 🇦🇹

