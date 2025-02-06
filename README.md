# LocateFinderWSL
## UI wrapper for locate linux command for Windows

## Requirements
wsl running default ubuntu

locate command installed `sudo apt install locate`

drives mounted in wsl
` sudo mount -t drvfs D: /mnt/d `

the filesystem needs to be indexed `sudo updatedb`

**The Program should be run on windows, do not run inside wsl!**