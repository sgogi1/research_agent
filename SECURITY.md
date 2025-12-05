# Security Policy

## 🔒 Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please report it privately:

### Email Security Report

Send an email to: **sareengogi@gmail.com**

Include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We'll acknowledge receipt within 48 hours
- **Assessment**: We'll assess the vulnerability within 7 days
- **Fix Timeline**: Critical vulnerabilities will be addressed as quickly as possible
- **Disclosure**: We'll coordinate disclosure after a fix is available

## 🛡️ Security Best Practices

### For Users

1. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Secure API Keys**
   - Never commit `.env` files
   - Use environment variables in production
   - Rotate API keys regularly

3. **Use HTTPS**
   - Always use HTTPS in production
   - Configure SSL/TLS certificates

4. **Regular Updates**
   - Keep the application updated to the latest version
   - Monitor security advisories

### For Developers

1. **Input Validation**
   - Validate all user inputs
   - Sanitize data before processing
   - Use parameterized queries (if using databases)

2. **Authentication & Authorization**
   - Implement proper authentication if needed
   - Use secure session management
   - Follow principle of least privilege

3. **Dependencies**
   - Regularly update dependencies
   - Monitor for known vulnerabilities
   - Use `pip-audit` or similar tools

4. **Secrets Management**
   - Never hardcode secrets
   - Use environment variables
   - Use secret management services in production

## 🔍 Known Security Considerations

### API Key Security

- The application requires an OpenRouter API key
- This key should be kept secure and never exposed
- Use environment variables or secure secret management

### Input Validation

- User-provided topics are processed by LLM
- No sensitive data should be included in topics
- Generated reports are stored in `history/` directory

### File Storage

- Reports are stored as HTML files
- Ensure proper file permissions
- Consider implementing access controls for production

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security.html)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)

## 🙏 Thank You

Thank you for helping keep AI Research Agent secure!

