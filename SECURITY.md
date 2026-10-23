# Security policy

## Supported versions

The latest release receives security fixes.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature for this repository. Include the affected version, Ubuntu release, reproduction steps, and impact. Do not open a public issue for a vulnerability that exposes user data or permits command execution.

The tray service runs under the current user. It does not require root access or listen on a network socket. The installer uses `sudo` only for packages installed through Ubuntu's package manager.
