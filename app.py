from flask import Flask, render_template, request
import socket
import ipaddress
import re

app = Flask(__name__)

# -------- Validation Functions --------
def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_domain(domain):
    pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, domain)


def is_valid_port(port):
    try:
        port = int(port)
        return 1 <= port <= 65535
    except:
        return False


# -------- Home --------
@app.route("/")
def home():
    return """
    <h2>NetAssist - DNS Tools</h2>
    <ul>
        <li><a href='/subnet'>Subnet Calculator</a></li>
        <li><a href='/dns'>DNS Resolution</a></li>
        <li><a href='/reverse-dns'>Reverse DNS Lookup</a></li>
        <li><a href='/port-checker'>Port Checker</a></li>
    </ul>
    """


# -------- DNS Resolution --------
@app.route("/dns", methods=["GET", "POST"])
def dns_lookup():
    ip_address = None
    error = None
    domain = ""

    if request.method == "POST":
        domain = request.form.get("domain", "").strip()

        if not domain:
            error = "Please enter a domain name."

        elif not is_valid_domain(domain):
            error = "Invalid domain format."

        else:
            try:
                ip_address = socket.gethostbyname(domain)
            except socket.gaierror:
                error = "Could not resolve domain."

    return render_template("dns.html",
                           ip_address=ip_address,
                           error=error,
                           domain=domain)


# -------- Reverse DNS --------
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
            error = "Invalid IP address format."

        else:
            try:
                domain_name = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                error = "No domain name found for this IP address."
            except socket.gaierror:
                error = "Could not process this IP address."

    return render_template("reverse_dns.html",
                           domain_name=domain_name,
                           error=error,
                           ip=ip)


# -------- Port Checker (YOUR PART) --------
@app.route("/port-checker", methods=["GET", "POST"])
def port_checker():
    result = None
    error = None
    status = None

    if request.method == "POST":
        host = request.form.get("host", "").strip()
        port = request.form.get("port", "").strip()

        if not host:
            error = "Please enter a host (domain or IP)."

        elif not (is_valid_ip(host) or is_valid_domain(host)):
            error = "Invalid host format (must be IP or domain)."

        elif not port:
            error = "Please enter a port number."

        elif not is_valid_port(port):
            error = "Port must be between 1 and 65535."

        else:
            try:
                port = int(port)

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)

                if s.connect_ex((host, port)) == 0:
                    result = f"Port {port} is OPEN on {host}"
                    status = "open"
                else:
                    result = f"Port {port} is CLOSED on {host}"
                    status = "closed"

                s.close()

            except socket.gaierror:
                error = "Invalid host or DNS resolution failed."
            except Exception:
                error = "Connection error occurred."

    return render_template("port_checker.html",
                           result=result,
                           error=error,
                           status=status)



# -------- Subnet Calculator --------
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
                    "network_address": network.network_address,
                    "broadcast_address": network.broadcast_address,
                    "subnet_mask": network.netmask,
                    "total_addresses": network.num_addresses,
                    "usable_hosts": len(hosts),
                    "first_host": hosts[0] if hosts else "N/A",
                    "last_host": hosts[-1] if hosts else "N/A"
                }

            except ValueError:
                error = "Invalid input. Please use format like 192.168.1.0/24"

    return render_template(
        "subnet.html",
        result=result,
        error=error,
        ip_input=ip_input
    )

# -------- Run App --------
if __name__ == "__main__":
    app.run(debug=True)