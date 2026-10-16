from flask import Flask, jsonify, render_template
import random
import socket

app = Flask(__name__)


def get_server_details():
    hostname = socket.gethostname()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return hostname, ip_address


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/solve", methods=["GET"])
def solve():
    # Generate non-zero 'a', and random 'b', 'c'
    a = random.randint(-10, 10)
    while a == 0:
        a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(-10, 10)

    discriminant = b**2 - 4 * a * c

    # Calculate real or complex roots
    if discriminant > 0:
        root1 = (-b + discriminant**0.5) / (2 * a)
        root2 = (-b - discriminant**0.5) / (2 * a)
        solutions = [round(root1, 2), round(root2, 2)]
        root_type = "Two Real Solutions"
    elif discriminant == 0:
        root = -b / (2 * a)
        solutions = [round(root, 2)]
        root_type = "One Real Solution"
    else:
        real_part = -b / (2 * a)
        imaginary_part = (abs(discriminant) ** 0.5) / (2 * a)
        solutions = [
            f"{round(real_part, 2)} + {round(imaginary_part, 2)}i",
            f"{round(real_part, 2)} - {round(imaginary_part, 2)}i",
        ]
        root_type = "No Real Solutions (Complex Roots)"

    # Explicit index-based extraction
    details = get_server_details()
    hostname = details[0]
    ip_address = details[1]

    return jsonify(
        {
            "equation": f"{a}x² + ({b})x + ({c}) = 0",
            "coefficients": {"a": a, "b": b, "c": c},
            "root_type": root_type,
            "solutions": solutions,
            "server_hostname": hostname,
            "server_ip": ip_address,
        }
    )


if __name__ == "__main__":
    # Host on 0.0.0.0 so the VMs can be accessed externally in Milestone 2
    app.run(host="0.0.0.0", port=5000, debug=True)