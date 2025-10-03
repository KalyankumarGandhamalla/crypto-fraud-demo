import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import select
from dotenv import load_dotenv

# internal imports
from db_init import SessionLocal, init_db
from models import FraudReport, Investigation  # <-- FIXED

# ---------------------------
# Flask App Setup
# ---------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # allow all origins

load_dotenv()

# ---------------------------
# Config
# ---------------------------
ALCHEMY_KEY = os.getenv("ALCHEMY_API_KEY", "")
if not ALCHEMY_KEY:
    print("⚠️ Warning: ALCHEMY_API_KEY not set in .env")

RPC_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "devsecret")

# init DB if not exists
init_db()

# ---------------------------
# Alchemy Functions
# ---------------------------
def get_eth_balance(address):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1
    }
    try:
        r = requests.post(RPC_URL, json=payload, timeout=15)
        print("Balance API raw:", r.text)
        r.raise_for_status()
        data = r.json()
        wei = int(data["result"], 16)
        return wei / 1e18
    except Exception as e:
        print("Alchemy Balance error:", e)
        return 0


def get_eth_transactions(address, max_txs=20):
    payload = {
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": "0x0",
            "toBlock": "latest",
            "toAddress": address,
            "category": ["external", "erc20", "erc721", "erc1155"],
            "maxCount": hex(max_txs),
            "order": "desc"
        }],
        "id": 1
    }
    try:
        r = requests.post(RPC_URL, json=payload, timeout=20)
        print("Tx API raw:", r.text)
        r.raise_for_status()
        data = r.json()
        return data.get("result", {}).get("transfers", [])
    except Exception as e:
        print("Alchemy Tx error:", e)
        return []


def analyze_transactions(tx_list):
    suspicious = []
    for tx in tx_list:
        try:
            value_eth = float(tx.get("value", 0))
            if value_eth >= 10:
                suspicious.append({
                    "txhash": tx.get("hash"),
                    "reason": f"Large transfer ({value_eth:.4f} ETH)",
                    "value_eth": value_eth,
                    "from": tx.get("from"),
                    "to": tx.get("to"),
                    "blockNum": tx.get("blockNum")
                })
        except:
            continue

    if tx_list:
        sender = tx_list[0].get("from", "").lower()
        out_count = sum(1 for t in tx_list if t.get("from", "").lower() == sender)
        if out_count >= 6:
            suspicious.append({"reason": f"Many recent outgoing transactions ({out_count})"})

    return suspicious

# ---------------------------
# Fraud Reports API
# ---------------------------
@app.route("/api/reports", methods=["POST"])
def create_report():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    report = FraudReport(
        wallets=data.get("wallets", ""),
        fraud_type=data.get("fraud_type", "unknown"),
        description=data.get("description", ""),
        attachment=data.get("attachment"),
        reporter_name=data.get("reporter_name")
    )
    session = SessionLocal()
    session.add(report)
    session.commit()
    session.refresh(report)
    session.close()
    return jsonify({"id": report.id, "status": report.status}), 201


@app.route("/api/reports", methods=["GET"])
def list_reports():
    session = SessionLocal()
    reports = session.execute(
        select(FraudReport).order_by(FraudReport.created_at.desc())
    ).scalars().all()
    result = []
    for r in reports:
        result.append({
            "id": r.id,
            "reporter_name": r.reporter_name,
            "wallets": r.wallets,
            "fraud_type": r.fraud_type,
            "description": r.description,
            "attachment": r.attachment,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        })
    session.close()
    return jsonify(result)


@app.route("/api/reports/<int:report_id>/status", methods=["PUT"])
def update_report_status(report_id):
    data = request.get_json()
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status required"}), 400

    session = SessionLocal()
    report = session.get(FraudReport, report_id)
    if not report:
        session.close()
        return jsonify({"error": "not found"}), 404

    report.status = new_status
    session.commit()
    session.close()
    return jsonify({"id": report.id, "status": report.status})


@app.route("/api/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    session = SessionLocal()
    r = session.get(FraudReport, report_id)
    if not r:
        session.close()
        return jsonify({"error": "not found"}), 404

    result = {
        "id": r.id,
        "reporter_name": r.reporter_name,
        "wallets": r.wallets,
        "fraud_type": r.fraud_type,
        "description": r.description,
        "attachment": r.attachment,
        "status": r.status,
        "created_at": r.created_at.isoformat()
    }
    session.close()
    return jsonify(result)

# ---------------------------
# Investigations API
# ---------------------------
@app.route("/api/investigations", methods=["POST"])
def create_investigation():
    data = request.get_json()
    wallet = data.get("wallet_address")
    if not wallet:
        return jsonify({"error": "wallet_address required"}), 400

    inv = Investigation(
        wallet_address=wallet,
        summary=data.get("summary", ""),
        findings=data.get("findings", ""),
        linked_report_id=data.get("linked_report_id")
    )
    session = SessionLocal()
    session.add(inv)
    session.commit()
    session.refresh(inv)
    session.close()
    return jsonify({"id": inv.id, "wallet_address": inv.wallet_address}), 201

# ---------------------------
# Wallet Lookup API
# ---------------------------
@app.route("/api/wallet/<string:address>", methods=["GET"])
def wallet_details(address):
    balance = get_eth_balance(address)
    txs = get_eth_transactions(address, max_txs=50)
    suspicious = analyze_transactions(txs)

    simplified = []
    for t in txs:
        simplified.append({
            "hash": t.get("hash"),
            "from": t.get("from"),
            "to": t.get("to"),
            "value_eth": float(t.get("value", 0)),
            "asset": t.get("asset", "-"),
            "category": t.get("category", "-"),
            "blockNum": t.get("blockNum")
        })

    return jsonify({
        "address": address,
        "balance_eth": balance,
        "tx_count": len(txs),
        "transactions": simplified,
        "suspicious": suspicious
    })

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
