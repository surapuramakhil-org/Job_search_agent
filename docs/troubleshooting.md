### Troubleshooting

#### 1. OpenAI API Rate Limit Errors

**Error Message:**

openai.RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: <https://platform.openai.com/docs/guides/error-codes/api-errors>.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}

**Solution:**

- Check your OpenAI API billing settings at <https://platform.openai.com/account/billing>
- Ensure you have added a valid payment method to your OpenAI account
- Note that ChatGPT Plus subscription is different from API access
- If you've recently added funds or upgraded, wait 12-24 hours for changes to take effect
- Free tier has a 3 RPM limit; spend at least $5 on API usage to increase

#### 2. Incorrect Information in Job Applications

**Issue:** Bot provides inaccurate data for experience, CTC, and notice period

**Solution:**

- Update prompts for professional experience specificity
- Add fields in `config.yaml` for current CTC, expected CTC, and notice period
- Modify bot logic to use these new config fields

#### 3. YAML Configuration Errors

**Error Message:**

yaml.scanner.ScannerError: while scanning a simple key

**Solution:**

- Copy example `config.yaml` and modify gradually
- Ensure proper YAML indentation and spacing
- Use a YAML validator tool
- Avoid unnecessary special characters or quotes

#### 4. Bot Logs In But Doesn't Apply to Jobs

**Issue:** Bot searches for jobs but continues scrolling without applying

**Solution:**

- Check for security checks or CAPTCHAs
- Verify `config.yaml` job search parameters
- Ensure your account profile meets job requirements
- Review console output for error messages

#### 5. General Troubleshooting Tips

- Use the latest version of the script
- Verify all dependencies are installed and updated
- Check internet connection stability
- Clear browser cache and cookies if issues persist

For further assistance, please create an issue on the [GitHub repository](https://github.com/surapuramakhil-org/Job_hunt_assistant/issues) with detailed information about your problem, including error messages and your configuration (with sensitive information removed).
