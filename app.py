from flask import Flask, render_template, request
import ipaddress
import platform
import re
import socket
import subprocess

app = Flask(__name__)

DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
)


def is_valid_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_valid_domain(domain):
    if not domain:
        return False
    return DOMAIN_PATTERN.match(domain) is not None


def is_valid_host(host):
    return is_valid_ip(host) or is_valid_domain(host)


def is_valid_port(port):
    try:
        port_number = int(port)
        return 1 <= port_number <= 65535
    except (TypeError, ValueError):
        return False


@app.route("/")
def home():
    tools = [
        {"title": "Subnet Calculator", "desc": "Find network, broadcast, mask, and host range.", "url": "/subnet", "icon": "🧮"},
        {"title": "DNS Resolution", "desc": "Convert a domain name to an IP address.", "url": "/dns", "icon": "🌐"},
        {"title": "Reverse DNS", "desc": "Find a domain name from an IP address.", "url": "/reverse-dns", "icon": "🔁"},
        {"title": "Port Checker", "desc": "Check if a TCP port is open or closed.", "url": "/port-checker", "icon": "🔌"},
        {"title": "Domain Validation", "desc": "Validate domain format and DNS availability.", "url": "/validation", "icon": "✅"},
        {"title": "Ping Test", "desc": "Test reachability and response time.", "url": "/ping", "icon": "📡"},
        {"title": "Path Visualization", "desc": "See a simple domain-to-IP network path.", "url": "/visualization", "icon": "🗺️"},
    ]
    return render_template("home.html", tools=tools)


@app.route("/dns", methods=["GET", "POST"])
def dns_lookup():
    ip_address = None
    error = None
    domain = ""

    if request.method == "POST":
        domain = request.form.get("domain", "").strip().lower()
        if not domain:
            error = "Please enter a domain name."
        elif not is_valid_domain(domain):
            error = "Invalid domain format. Example: google.com"
        else:
            try:
                ip_address = socket.gethostbyname(domain)
            except socket.gaierror:
                error = "Could not resolve this domain."

    return render_template("dns.html", ip_address=ip_address, error=error, domain=domain)


@app.route("/reverse-dns", methods=["GET", "POST"])
def reverse_dns():
    domain_name = None
    error = None
    ip = ""

    if request.method == "POST":
        ip = request.form.get("ip", "").strip()
        if not ip:
            error = "Please enter an IP address."
        elif not is_valid_ip(ip):
            error = "Invalid IP address format. Example: 8.8.8.8"
        else:
            try:
                domain_name = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                error = "No domain name found for this IP address."
            except socket.gaierror:
                error = "Could not process this IP address."

    return render_template("reverse_dns.html", domain_name=domain_name, error=error, ip=ip)


@app.route("/port-checker", methods=["GET", "POST"])
def port_checker():
    result = None
    error = None
    status = None
    host = ""
    port = ""

    if request.method == "POST":
        host = request.form.get("host", "").strip().lower()
        port = request.form.get("port", "").strip()

        if not host:
            error = "Please enter a host."
        elif not is_valid_host(host):
            error = "Invalid host format. Use a domain or IP address."
        elif not port:
            error = "Please enter a port number."
        elif not is_valid_port(port):
            error = "Port must be between 1 and 65535."
        else:
            try:
                port_number = int(port)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    code = sock.connect_ex((host, port_number))
                if code == 0:
                    result = f"Port {port_number} is OPEN on {host}."
                    status = "open"
                else:
                    result = f"Port {port_number} is CLOSED or filtered on {host}."
                    status = "closed"
            except socket.gaierror:
                error = "Host could not be resolved."
            except Exception:
                error = "Connection error occurred."

    return render_template("port_checker.html", result=result, error=error, status=status, host=host, port=port)


@app.route("/subnet", methods=["GET", "POST"])
def subnet_calculator():
    result = None
    error = None
    ip_input = ""

    if request.method == "POST":
        ip_input = request.form.get("ip_network", "").strip()
        if not ip_input:
            error = "Please enter an IP address with subnet. Example: 192.168.1.0/24"
        else:
            try:
                network = ipaddress.ip_network(ip_input, strict=False)
                hosts = list(network.hosts())
                result = {
                    "IP Version": f"IPv{network.version}",
                    "Network Address": network.network_address,
                    "Broadcast Address": network.broadcast_address if network.version == 4 else "N/A for IPv6",
                    "Subnet Mask": network.netmask,
                    "Prefix Length": f"/{network.prefixlen}",
                    "Total Addresses": network.num_addresses,
                    "Usable Hosts": len(hosts),
                    "First Host": hosts[0] if hosts else "N/A",
                    "Last Host": hosts[-1] if hosts else "N/A",
                }
            except ValueError:
                error = "Invalid input. Please use a format like 192.168.1.0/24"

    return render_template("subnet.html", result=result, error=error, ip_input=ip_input)


@app.route("/validation", methods=["GET", "POST"])
def validation():
    result = None
    error = None
    domain = ""

    if request.method == "POST":
        domain = request.form.get("domain", "").strip().lower()
        if not domain:
            error = "Please enter a domain name."
        elif not is_valid_domain(domain):
            error = "Invalid domain format. Avoid spaces and special symbols."
        else:
            result = {"Format": "Valid", "DNS Status": "Not checked", "IP Address": "N/A"}
            try:
                result["IP Address"] = socket.gethostbyname(domain)
                result["DNS Status"] = "Resolvable"
            except socket.gaierror:
                result["DNS Status"] = "Valid format, but DNS not found"

    return render_template("validation.html", result=result, error=error, domain=domain)


@app.route("/ping", methods=["GET", "POST"])
def ping():
    result = None
    error = None
    host = ""

    if request.method == "POST":
        host = request.form.get("host", "").strip().lower()
        if not host:
            error = "Please enter a domain or IP address."
        elif not is_valid_host(host):
            error = "Invalid host. Use a domain or IP address."
        else:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "4", host]
            try:
                completed = subprocess.run(command, capture_output=True, text=True, timeout=8)
                reachable = completed.returncode == 0
                output = completed.stdout or completed.stderr
                result = {
                    "Host": host,
                    "Status": "Reachable" if reachable else "Unreachable",
                    "Output": "\n".join(output.splitlines()[:8]),
                    "ok": reachable,
                }
            except subprocess.TimeoutExpired:
                error = "Ping request timed out."
            except FileNotFoundError:
                error = "Ping command is not available on this system."

    return render_template("ping.html", result=result, error=error, host=host)

@app.route("/visualization", methods=["GET", "POST"])
def visualization():
    result = None
    error = None
    domain = ""

    if request.method == "POST":
        domain = request.form.get("domain", "").strip().lower()

        if not domain:
            error = "Please enter a domain name."

        elif not is_valid_domain(domain):
            error = "Invalid domain format. Example: google.com"

        else:
            try:
                ip_address = socket.gethostbyname(domain)

                parts = domain.split(".")
                tree = []

                # Root DNS
                tree.append({
                    "name": "Root DNS",
                    "detail": "The request starts from the global DNS root."
                })

                # TLD Server مثل .com
                tld = parts[-1]
                tree.append({
                    "name": f".{tld} TLD Server",
                    "detail": f"Directs the request to domains ending with .{tld}."
                })

                # Main domain مثل google.com
                main_domain = ".".join(parts[-2:])
                tree.append({
                    "name": main_domain,
                    "detail": "Authoritative domain zone."
                })

                # Subdomains مثل mail.google.com
                if len(parts) > 2:
                    current_domain = main_domain

                    for sub in reversed(parts[:-2]):
                        current_domain = sub + "." + current_domain
                        tree.append({
                            "name": current_domain,
                            "detail": "Subdomain record."
                        })

                # Final IP
                tree.append({
                    "name": ip_address,
                    "detail": f"Final resolved IP address for {domain}."
                })

                result = {
                    "domain": domain,
                    "ip": ip_address,
                    "tree": tree
                }

            except socket.gaierror:
                error = "Could not resolve this domain for visualization."

    return render_template("visualization.html", result=result, error=error, domain=domain)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
