ENCS3320 Computer Networks Team Project (T029)
================================================

Team
----
  Alma Alkhader (Student ID: 1240386, Section: 2)
  Mohammad Joudeh (Student ID: 1241945, Section: 2)
  Eman Zayed (Student ID: 1240916, Section: 2)


Configure config.json
----------------------
All adjustable settings live in config.json at the project root:

  tcp_port                  - port the TCP diagnostic server listens on (5386)
  http_port                 - port the HTTP web server listens on (6386)
  server_host                - address the servers bind to ("0.0.0.0" = all interfaces)
  log_file                    - relative path to the log file (logs/server_log.jsonl)
  stats_file                   - relative path reserved for statistics data
  max_clients                  - maximum number of TCP clients allowed at once
  default_homepage              - which page loads at the bare "/" URL ("/home")
  buffer_size                    - socket read buffer size in bytes
  command_timeout_seconds         - how long a diagnostic command may run before
                                     it is treated as timed out

Ports 5386 and 6386 are computed from team member Alma's student ID
(1240386) per the assignment's port formula (last 3 digits + 5000 / + 6000).

Run the server
--------------
Windows:
    py run_server.py

Linux / macOS:
    python3 run_server.py

On startup you should see:
    Loading configuration...
    Logger initialized.
    Statistics initialized.
    TCP Server started on port 5386.
    HTTP Server started on port 6386.
    Waiting for client connections...

Leave this running - it is both the diagnostic server and the web server.

Run a client
------------
Windows:
    py run_client.py

Linux / macOS:
    python3 run_client.py

This connects to the server and shows the interactive menu (Ping Host,
Trace Route, DNS Lookup, IP Configuration, Routing Table, ARP Table,
Active TCP Connections, Exit).

Reproducing the multi-client demo
----------------------------------
Start the server in one terminal, then open two or more additional
terminals and run run_client.py in each. Every client gets its own
thread on the server (Thread-1, Thread-2, ...) and can run commands
independently and concurrently  a slow command on one client does not
block another.

Web interface
--------------
With the server running, open:
    http://localhost:6386

Pages available: Home, Dashboard, Command History, Statistics, Search,
Download Log.

Known platform notes
----------------------
- IP Configuration, Routing Table, ARP Table, and Active TCP Connections
  (menu options 4-7) call OS-specific commands (ip/ss on Linux,
  ipconfig/route/arp/netstat on Windows) and are not expected to work on
  macOS, since macOS uses different underlying tools than either.
- NSLOOKUP and PING behavior have been verified on Linux and macOS; see
  DECISIONS.md for Windows-specific verification notes.

Design decisions
------------------
A number of judgment calls were required where the assignment left
behavior unspecified (for example, what counts as a failed command, how
search matching works, and what happens when max_clients is exceeded).
Every such decision, and the reasoning behind it, is documented in
DECISIONS.md at the project root.



