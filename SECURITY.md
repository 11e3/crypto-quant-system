# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.

Instead, please report it via one of the following methods:

1. **Email**: Send details to [utioed@gmail.com]
2. **Private Security Advisory**: Create a [private security advisory](https://github.com/your-username/upbit-quant-system/security/advisories/new) on GitHub

### What to Include

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity and complexity

## Security Best Practices

### For Users

1. **API Keys**: Never commit API keys to version control
   - Use environment variables
   - Use `.env` files (and ensure they're in `.gitignore`)
   - Use secret management services in production

2. **Environment Variables**: Store sensitive data in environment variables
   ```bash
   export UPBIT_ACCESS_KEY="your-key"
   export UPBIT_SECRET_KEY="your-secret"
   ```

3. **Permissions**: Use API keys with minimal required permissions
   - Read-only keys for backtesting
   - Trading keys only for live trading

4. **Network Security**: Use secure connections
   - HTTPS for all API calls
   - Secure WebSocket connections (WSS)

5. **Regular Updates**: Keep dependencies updated
   ```bash
   uv sync --upgrade
   ```

### For Developers

1. **Input Validation**: Always validate user inputs
2. **Error Handling**: Don't expose sensitive information in error messages
3. **Dependencies**: Regularly update and audit dependencies
4. **Secrets**: Never hardcode secrets in source code
5. **Code Review**: Review security-sensitive code carefully

## Known Security Considerations

### API Key Management

- API keys are required for live trading
- Keys should be stored securely (environment variables, secret managers)
- Never share API keys publicly
- Rotate keys regularly

### Trading Risks

- This software executes real trades with real money
- Always test thoroughly in backtesting before live trading
- Use dry-run mode when available
- Start with small amounts
- Monitor the bot regularly

### Data Privacy

- Trading data may contain sensitive information
- Be cautious when sharing logs or reports
- Consider data anonymization for public sharing

## Security Updates

Security updates will be announced via:
- GitHub Releases
- Security Advisories
- Project README (for critical issues)

## Acknowledgments

We appreciate responsible disclosure of security vulnerabilities. Contributors who report valid security issues will be acknowledged (if desired) in our security advisories.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Upbit API Security](https://docs.upbit.com/docs/user-request-guide)
