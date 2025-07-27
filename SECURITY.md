# Security Guide for City Pulse

## Environment Variables Security

### 1. API Key Management

**DO:**
- ✅ Store API keys in `.env` file
- ✅ Add `.env` to `.gitignore` 
- ✅ Use environment-specific files (`.env.development`, `.env.production`)
- ✅ Validate required environment variables on startup
- ✅ Use different API keys for different environments

**DON'T:**
- ❌ Commit API keys to version control
- ❌ Hardcode API keys in source code
- ❌ Share API keys in chat/email
- ❌ Use production API keys in development

### 2. Google Gemini API Key Security

Your current API key in `.env`:
```
GEMINI_API_KEY=AIzaSyAexl1B96BaGsyDN27BKJhZ5YeTkI_dkV8
```

**Recommendations:**
1. **Rotate this key** if it was exposed in code/commits
2. **Set up API quotas** in Google Cloud Console
3. **Restrict API key** to specific IPs/domains if possible
4. **Monitor usage** for unexpected spikes

### 3. Environment File Structure

```
.env                    # Main environment file (DO NOT COMMIT)
.env.example           # Template file (SAFE TO COMMIT)
.env.local            # Local overrides (DO NOT COMMIT)
.env.development      # Development settings (DO NOT COMMIT)
.env.production       # Production settings (DO NOT COMMIT)
```

### 4. Docker Security

- Environment variables are passed securely to containers
- `.env` file is mounted as read-only
- No environment variables exposed in Docker images

### 5. Emergency Procedures

**If API key is compromised:**
1. Immediately revoke the key in Google Cloud Console
2. Generate a new API key
3. Update `.env` file with new key
4. Restart applications
5. Review access logs for unauthorized usage

### 6. Additional Security Measures

- Enable 2FA on Google Cloud account
- Use IAM roles with minimal permissions
- Regularly audit API usage
- Set up alerts for unusual activity
- Keep dependencies updated (`npm audit`, `pip check`)

### 7. Production Deployment

For production deployments:
- Use secrets management systems (AWS Secrets Manager, Azure Key Vault, etc.)
- Enable HTTPS/TLS encryption
- Set up proper firewall rules
- Use container image scanning
- Implement logging and monitoring

## Quick Setup for New Team Members

1. Copy `.env.example` to `.env`
2. Get API keys from team lead
3. Fill in the actual values in `.env`
4. Never commit `.env` file
5. Ask for help if you need additional API access
