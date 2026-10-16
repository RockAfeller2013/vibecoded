- build music based on my libarary
- Mix music based on DJ Techniques. and automix feature
- https://www.flowmusic.app/session/3c94db5a-5f18-4aab-b572-380a470b6067?t=true


Retrieve Files via the File Station Web API
If your page requires programmatic access to retrieve and display image files, you can utilize the official File Station Web API:

List folder contents using the SYNO.FileStation.List API method with the folder path set to /photo.
Retrieve files using the SYNO.FileStation.Download method specifying the photo path (such as ["/photo/example.jpg"]).
API requests must authenticate with a DSM account that has read permissions assigned to the /photo shared folder under DSM Control Panel > Shared Folder.
For security, authentication and download requests should be processed through a backend service rather than directly in client-side HTML, ensuring your DSM credentials and session IDs remain protected.
Full parameter specifications can be found in the Synology File Station API Guide.

https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

A browser-based index.html cannot directly connect to an SMB share or securely store SMB credentials. You can use a local Python backend to mount or access your Synology NAS, with an HTML interface to browse the music folder.
Your target path is:
- NAS IP: 192.168.1.146
- SMB share: music
- Folder: Feel
- macOS mount path: /Volumes/music/Feel
- SMB path: smb://192.168.1.146/music
If you specifically need a standalone index.html, it can provide a form for entering the NAS connection details, but a backend is required to access files over SMB.

Option B: Enable WebDAV or Audio Station on your Synology
If you don't want to run a local terminal script:
Enable WebDAV in your Synology Package Center. WebDAV runs over standard HTTP/HTTPS, allowing standard browser fetch() requests with Basic Auth to browse folders and stream audio files directly from the NAS


- Music Assistant for Proxmox VE - https://github.com/jingato/music-assistant-proxmox
- Installation and Deployment - https://deepwiki.com/music-assistant/server/1.1-installation-and-deployment
- https://developers.music-assistant.io/ - https://developers.music-assistant.io/


