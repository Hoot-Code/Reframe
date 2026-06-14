# Security Policy

## Overview

ReFrame Bot processes user-uploaded media files. Security is critical to prevent abuse and protect users.

## Security Measures

### File Upload Security
- **File size limits**: Configurable max upload size (default 50MB)
- **Magic-byte validation**: All uploaded files are scanned to verify they match claimed format
- **Malicious pattern detection**: Rejects files containing PHP, shell scripts, ELF/PE executables, or embedded ZIP archives
- **JPEG EOF validation**: Verifies JPEG files end with correct EOF marker
- **Automatic cleanup**: All uploaded files are deleted after processing

### Access Control
- **Admin isolation**: Admin commands are invisible to non-admin users
- **Admin ID whitelist**: Only configured Telegram user IDs can access admin features
- **Banned user enforcement**: Banned users cannot process files

### Rate Limiting
- **Per-user limits**: Maximum 5 file uploads per minute per user
- **Concurrent job limits**: Semaphore-based concurrency control (configurable)

### Data Protection
- **No persistent media storage**: All uploaded files are temporary and auto-deleted
- **Database encryption**: PostgreSQL connections support SSL/TLS
- **No secrets in logs**: Sensitive values are never logged

### Infrastructure Security
- **Docker**: Non-root container execution
- **Kubernetes**: Resource limits, liveness/readiness probes
- **Network isolation**: Services communicate via internal network only

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to the maintainer
3. Include detailed reproduction steps
4. Allow reasonable time for fix before public disclosure

## Scanner Limitations

The security scanner is a **lightweight pre-screening mechanism**, not a full security analysis. It:

- Inspects only the first 8KB of file content
- Uses pattern matching, not deep inspection
- Cannot detect polymorphic payloads, steganography, or decoder exploits

This provides defense against obvious threats but should not be relied upon as the sole security measure.

## Compliance Notes

### SOC 2 Type II Alignment
This project aligns with SOC 2 trust service criteria:

- **CC6.1**: Logical access controls via admin ID whitelist
- **CC6.6**: System boundaries enforced via rate limiting and file size limits
- **CC7.1**: Security monitoring via threat logging and admin alerts
- **CC7.2**: Anomaly detection via security event logging
- **CC8.1**: Change management via admin-only configuration

### Data Retention
- **Media files**: Deleted immediately after processing
- **Process logs**: Retained for 30 days, then automatically purged
- **Security logs**: Retained for 30 days, then automatically purged
- **User data**: Retained indefinitely (can be deleted by admin)

## Security Scanning

Automated security scanning runs via GitHub Actions:
- **Trivy**: Filesystem vulnerability scanning
- **Snyk**: Dependency vulnerability scanning
- **Schedule**: Weekly + on every push/PR
