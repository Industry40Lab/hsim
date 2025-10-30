# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.0.1   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in hsim, please report it by emailing the maintainers. Please do not open a public issue for security vulnerabilities.

When reporting a vulnerability, please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if applicable)

## Security Best Practices

### Environment Variables

Never commit sensitive information to version control. Always use environment variables for:

- `FLASK_SECRET_KEY`: Flask session secret key
- `AZURE_CONNECTION_STRING`: Azure Communication Services connection string
- Database credentials
- API keys and tokens

### Password Security

The application enforces strong password requirements:

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter  
- At least one digit

Passwords are hashed using Werkzeug's `generate_password_hash` before storage.

### Database Security

- All SQL queries use parameterized statements to prevent SQL injection
- Database connections are properly closed after use
- User authentication is required for all protected routes

### Web Application Security

The Flask application includes the following security headers:

- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: SAMEORIGIN` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Enables XSS filtering
- `Strict-Transport-Security` - Enforces HTTPS connections

### Session Security

- Sessions use secure, randomly generated secret keys
- Session data is not stored in cookies (server-side sessions recommended for production)
- Logout properly clears all session data

### File Upload Security

- File uploads use `secure_filename()` to sanitize filenames
- Only `.xlsx` files are accepted for simulation uploads
- Files are stored in temporary directories that are cleaned up on shutdown

### Production Deployment

For production deployments:

1. Set `FLASK_SECRET_KEY` to a strong, random value
2. Use HTTPS (enable with `Strict-Transport-Security` header)
3. Set `debug=False` in Flask app
4. Use a production WSGI server (e.g., Gunicorn)
5. Implement rate limiting for login attempts
6. Regular security audits and dependency updates
7. Use a dedicated database server with proper access controls
8. Enable logging and monitoring for suspicious activity

### Dependency Security

Run regular security audits:

```bash
pip install safety
safety check
```

Update dependencies regularly to patch known vulnerabilities.

## Known Security Considerations

1. **Azure Connection String**: The Azure Communication Services connection string should be kept secret. Use environment variables, never hardcode in source.

2. **SQLite Database**: The default SQLite database is suitable for development but consider using PostgreSQL or MySQL for production deployments with sensitive data.

3. **Email Password Reset**: Password reset emails contain the new password in plain text. Consider implementing token-based reset links instead.

4. **Session Management**: Consider implementing session timeouts and refresh mechanisms for enhanced security.

## Security Updates

Security updates will be released as needed. Users should update to the latest version promptly when security issues are addressed.
