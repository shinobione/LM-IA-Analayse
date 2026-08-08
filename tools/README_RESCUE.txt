LMNotebook Windows Rescue
=========================

If LMNotebook_START.cmd cannot update or create the virtual environment, run LMNotebook_RESCUE.cmd from the repository root.

The rescue launcher:
- resolves Git from PATH or common Windows install locations;
- falls back to direct GitHub downloads for critical launcher files when Git is not visible;
- resolves Python from PATH, Python Launcher, or standard Python 3.12 install locations;
- removes only incomplete backend/.venv folders;
- creates backend/.venv before starting the PowerShell bootstrap;
- resumes the normal one-click launcher.
