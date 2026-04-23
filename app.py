from flask import Flask, render_template, request
import socket
import ipaddress

app = Flask(__name__)


@app.route("/")
def home():
    # Temporary homepage until the full project is integrated
    return """
    <h2>NetAssist - DNS Tools</h2>
    <ul>
        <li><a href='/dns'>DNS Resolution</a></li>
        <li><a href='/reverse-dns'>Reverse DNS Lookup</a></li>
    </ul>
    """


@app.route("/dns", methods=["GET", "POST"])
def dns_lookup():
    ip_address = None
    error = None

    if request.method == "POST":
        domain = request.form.get("domain", "").strip()

        if not domain:
            error = "Please enter a domain name."
        else:
            try:
                # Resolve domain name to IP address
                ip_address = socket.gethostbyname(domain)
            except socket.gaierror:
                error = "Invalid domain name or could not resolve the domain."

    return render_template("dns.html", ip_address=ip_address, error=error)


@app.route("/reverse-dns", methods=["GET", "POST"])
def reverse_dns():
    domain_name = None
    error = None

    if request.method == "POST":
        ip = request.form.get("ip", "").strip()

        if not ip:
            error = "Please enter an IP address."
        else:
            try:
                # Validate IP address format before doing reverse lookup
                ipaddress.ip_address(ip)

                # Perform reverse DNS lookup
                domain_name = socket.gethostbyaddr(ip)[0]
            except ValueError:
                error = "Invalid IP address format."
            except socket.herror:
                error = "No domain name found for this IP address."
            except socket.gaierror:
                error = "Could not process this IP address."

    return render_template("reverse_dns.html", domain_name=domain_name, error=error)


if __name__ == "__main__":
    app.run(debug=True)