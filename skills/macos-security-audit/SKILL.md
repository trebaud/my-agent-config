---
name: macos-security-audit
description: Run a comprehensive security audit on a macOS system. Checks processes, network connections, persistence mechanisms, code signatures, access controls, system hardening, filesystem integrity, and authentication logs. Use when the user asks to audit, harden, or check the security posture of a Mac.
compatibility: Requires macOS. Some checks require sudo for full coverage.
metadata:
  author: moose
  version: "1.0"
allowed-tools: Bash Read
---

# macOS Security Audit

Run all independent checks in parallel where possible. For each area, flag anything suspicious and verify legitimacy of third-party components.

## Processes and Network

1. List running processes sorted by resource usage — flag unrecognized binaries
2. List all listening ports and established outbound connections (`lsof -i -P -n`)
3. Cross-reference processes with their network activity — flag unexpected outbound connections

## Persistence Mechanisms

4. List LaunchAgents and LaunchDaemons at all three levels:
   - `~/Library/LaunchAgents/`
   - `/Library/LaunchAgents/`
   - `/Library/LaunchDaemons/`
5. Read the contents of every non-Apple plist file to inspect what binary it executes and on what schedule
6. Check login items (`osascript -e 'tell application "System Events" to get the name of every login item'`)
7. Check cron jobs for the current user (`crontab -l`) and `/etc/crontab`

## Code Signature Verification

8. For every non-Apple binary referenced by a LaunchAgent/Daemon or login item, run `codesign -dvv` and verify:
   - Signing authority is a known, legitimate developer
   - Team ID matches the expected vendor
   - Notarization status is present where expected
9. Verify the code signature of any updater frameworks or helper tools found (e.g. Google, Adobe, Spotify updaters)

## Access Control

10. List user accounts with UID >= 500 (`dscl . list /Users UniqueID`)
11. List admin group members (`dscl . -read /Groups/admin GroupMembership`)
12. Check `/etc/sudoers.d/` for custom sudoers rules
13. List SSH keys, check permissions, check for `authorized_keys` and `~/.ssh/config`
14. Find SUID/SGID binaries outside `/System` and `/usr` (`find /usr/local /opt /Applications -perm -4000 -o -perm -2000`)

## System Hardening

15. Check SIP status (`csrutil status`)
16. Check Gatekeeper status (`spctl --status`)
17. Check FileVault status (`fdesetup status`)
18. Check Application Firewall state and stealth mode (`/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate` and `--getstealthmode`)
19. List kernel extensions (`kextstat | grep -v com.apple`) and system extensions (`systemextensionsctl list`)

## Filesystem and Integrity

20. Check `/tmp` and `/private/tmp` for scripts, dylibs, hidden files, or unexpected executables
21. Find recently modified files (last 7 days) in `/etc`, `/Library/LaunchAgents`, `/Library/LaunchDaemons`, and `~/Library/LaunchAgents`
22. Check `/etc/hosts` for suspicious redirects beyond the default entries
23. Check DNS resolver config (`scutil --dns`) for non-standard nameservers

## Authentication and Logs

24. Show recent login history (`last -20`)
25. Check for failed authentication attempts (`log show --predicate 'eventMessage contains "authentication failure"' --last 7d`)

## Output Format

Summarize all findings in a markdown table with columns:

| Area | Finding | Severity | Recommended Action |

Severity levels: **None**, **Low**, **Med**, **High**

Sort High and Med findings to the top. End with an overall system health verdict.
